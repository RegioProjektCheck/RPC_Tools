# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# REGIOPROJEKTCHECK
# projektVerwaltung.py
#
# Description:
# PROJECT URL: http://www.regioprojektcheck.de
#
# Author:
# ILS gGmbH / HCU Hamburg / GGR Planung
#
# LICENSE: The MIT License (MIT) Copyright (c) 2014 RPC Consortium
# ---------------------------------------------------------------------------

import sys
from os.path import join, isdir
import os
import shutil
import gc
import arcpy
import numpy as np
from datetime import datetime

from rpctools.utils.params import Tool
from rpctools.utils.spatial_lib import get_ags
from rpctools.utils.spatial_lib import get_gemeindetyp
from rpctools.utils.constants import Nutzungsart
from rpctools.utils.encoding import encode

from rpctools.utils.params import Tool
from rpctools.diagrams.diagram_teilflaechen import DiaTeilflaechen
from rpctools.utils.spatial_lib import Point


class Projektverwaltung(Tool):

    _param_projectname = 'name'
    _workspace = 'FGDB_Definition_Projekt.gdb'


    def add_outputs(self):
        # add Teilflächen
        fc = "Teilflaechen_Plangebiet"
        layer = "Teilflaechen des Plangebiets"
        self.output.add_layer("projektdefinition", layer, fc,
                              name=u"Nutzungen des Plangebiets")

        self.output.add_osm_layer()
        self.output.add_project_contour()

        diagram = DiaTeilflaechen(project_name=self.par.name.value)
        self.output.add_diagram(diagram)


class ProjektAnlegen(Projektverwaltung):
    """Projekt neu anlegen"""
    _sk_radius = 20000

    def add_outputs(self):
        if os.path.exists(self.folders.get_projectpath(check=False)):
            super(ProjektAnlegen, self).add_outputs()

    def run(self):
        """"""
        gc.collect()
        #self.output.define_projection()
        try:
            self.projekt_anlegen()
            self.parent_tbx.config.active_project = self.projectname
        except Exception as e:
            success = False
            arcpy.AddError(e.message)
            arcpy.AddMessage("Fehlerhaftes Projekt wird wieder entfernt...")
            arcpy.Delete_management(self.folders.get_projectpath(check=False))

    def projekt_anlegen(self):
        """Projekt anlegen"""
        arcpy.env.overwriteOutput = True

        # get new Project input Data
        project_name = self.projectname

        flaeche = self.par.shapefile.value
        project_path = self.folders.get_projectpath(check=False)

        self.copy_template(project_path)

        tfl, gdbPfad = self.copy_teilflaechen_to_gdb(project_name, flaeche)
        toolbox = self.parent_tbx
        max_dist = toolbox.config.max_area_distance
        ags_projekt, gemeindename_projekt = \
            self.get_gemeinde(tfl, 'OBJECTID', max_dist)
        self._project_ags = ags_projekt

        self.calculate_teilflaechen_attributes(tfl,
                                               ags_projekt,
                                               gemeindename_projekt)

        self.set_source_xy()
        self.set_projektrahmendaten(ags_projekt,
                                    project_name,
                                    gemeindename_projekt)

        # output information to user
        arcpy.AddMessage("Basisdaten erfolgreich kopiert \n")

        arcpy.AddMessage(u"Neues Projekt angelegt im Ordner {}\n".format(
            project_path))

        # create 'Zentren'-table
        arcpy.AddMessage('Ermittle Gemeinden im Umkreis von {} km...'.format(
            self._sk_radius/1000))
        self.communities_to_centers(self._project_centroid,
                                    radius=self._sk_radius)

    def set_projektrahmendaten(self,
                               ags_projekt,
                               project_name,
                               gemeindename_projekt):
        """add project-data to Projektrahmendaten"""
        arcpy.SetProgressorLabel('Projektrahmendaten berechnen')
        arcpy.SetProgressorPosition(50)

        gemeindetyp = get_gemeindetyp(ags_projekt)

        # loesche ggf. vorhandene zeilen in den Projektrahmendaten und fuege neue daten danach hinzu
        projektrahmendaten = self.folders.get_table(tablename="Projektrahmendaten",
                                                    project=project_name)
        arcpy.DeleteRows_management(projektrahmendaten)

        cursor = arcpy.InsertCursor(projektrahmendaten)
        row = cursor.newRow()
        row.GEMEINDENAME = gemeindename_projekt
        row.PROJEKTNAME = project_name
        row.AGS = ags_projekt
        row.GEMEINDETYP = gemeindetyp
        cursor.insertRow(row)
        del cursor, row

    def calculate_teilflaechen_attributes(self,
                                          tfl,
                                          ags_projekt,
                                          gemeindename_projekt):
        """Attribute berechnen"""
        arcpy.SetProgressorLabel('Teilflächen-Attribute berechnen')
        arcpy.SetProgressorPosition(40)

        # Berechne ha der Teilflaechen
        arcpy.CalculateField_management(tfl,
                                        "Flaeche_ha",
                                        "!SHAPE.AREA@HECTARES!",
                                        "PYTHON_9.3", "")


        # Berechne Umfang der Flächen
        arcpy.CalculateField_management(tfl, "umfang_meter",
                                        "!shape.length@METER!", "PYTHON_9.3")

        cursor = arcpy.UpdateCursor(tfl)
        for i, row in enumerate(cursor):
            row.setValue("id_teilflaeche", i + 1)
            row.setValue("Nutzungsart", Nutzungsart.UNDEFINIERT)
            row.setValue("Name", "Flaeche_" + str(i + 1))
            row.setValue("Aufsiedlungsdauer", 1)
            row.setValue("validiert", 0)
            row.setValue("Beginn_Nutzung", datetime.now().year)
            row.setValue("ags_bkg", ags_projekt)
            row.setValue("gemeinde_name", gemeindename_projekt)
            row.setValue("WE_gesamt", 0)
            row.setValue("AP_gesamt", 0)
            row.setValue("VF_gesamt", 0)
            row.setValue("ew", 0)
            row.setValue("Wege_gesamt", 0)
            row.setValue("Wege_MIV", 0)
            cursor.updateRow(row)

    def copy_teilflaechen_to_gdb(self, project_name, flaeche):
        """add layer teilflächen to gdb"""
        arcpy.SetProgressorLabel('Teilflächen laden')
        arcpy.SetProgressorPosition(30)

        tfl = self.folders.get_table('Teilflaechen_Plangebiet',
                                     project=project_name, check=False)
        if arcpy.Exists(tfl):
            arcpy.Delete_management(tfl)

        # epsg-code or the
        config = self.parent_tbx.config
        sr1 = arcpy.Describe(flaeche).spatialReference
        if not sr1.factoryCode:
            raise Exception(u'Den Teilflächen fehlen Angaben zur Projektion. '
                            u'Bitte definieren Sie die Projektion in der Quelle!')
        sr2 = arcpy.SpatialReference(config.epsg)
        possible_transformations = arcpy.ListTransformations(sr1, sr2)
        if not possible_transformations:
            temp_path = self.folders.get_temporary_projectpath()
            temp_shapefile = os.path.join(temp_path, 'tempfile.shp')
            sr0 = arcpy.SpatialReference(4326)
            possible_transformations = arcpy.ListTransformations(sr1, sr0)
            transform_method = possible_transformations[0]
            arcpy.Project_management(flaeche, temp_shapefile, sr0, transform_method)
            possible_transformations = arcpy.ListTransformations(sr0, sr2)
            transform_method = possible_transformations[0]
            arcpy.Project_management(temp_shapefile, tfl, sr2, transform_method)
            arcpy.Delete_management(temp_shapefile)
        else:
            transform_method = possible_transformations[0]
            arcpy.Project_management(flaeche, tfl, sr2, transform_method)

        gdbPfad = self.folders.get_db()
        arcpy.env.workspace = gdbPfad

        # Prepare Shapefile for use in RPC

        # delete unused fields
        fieldObjList = arcpy.ListFields(tfl)
        fieldNameList = []
        for field in fieldObjList:
            if not field.required:
                fieldNameList.append(field.name)

        if fieldNameList:
            arcpy.DeleteField_management(tfl, fieldNameList)

        # add needed fields
        arcpy.AddField_management(tfl, "id_teilflaeche", "LONG")
        arcpy.AddField_management(tfl, "Name", "TEXT")
        arcpy.AddField_management(tfl, "Beginn_Nutzung", "LONG")
        arcpy.AddField_management(tfl, "Aufsiedlungsdauer", "LONG")
        arcpy.AddField_management(tfl, "Flaeche_ha", "DOUBLE")
        arcpy.AddField_management(tfl, "umfang_meter", "FLOAT")
        arcpy.AddField_management(tfl, "Nutzungsart", "SHORT")
        arcpy.AddField_management(tfl, "ags_bkg", "TEXT")
        arcpy.AddField_management(tfl, "gemeinde_name", "TEXT")
        arcpy.AddField_management(tfl, "validiert", "SHORT")
        arcpy.AddField_management(tfl, "WE_gesamt", "LONG")
        arcpy.AddField_management(tfl, "AP_gesamt", "LONG")
        arcpy.AddField_management(tfl, "VF_gesamt", "LONG")
        arcpy.AddField_management(tfl, "ew", "LONG")
        arcpy.AddField_management(tfl, "Wege_gesamt", "LONG")
        arcpy.AddField_management(tfl, "Wege_MIV", "LONG")
        arcpy.AddField_management(tfl, "IDGebietstyp", "TEXT")
        
        #arcpy.AddField_management(teilfaechen_plangebiet, "Bilanzsumme", "FLOAT")
        return tfl, gdbPfad

    def copy_template(self, project_path):
        """copy template folder"""
        arcpy.SetProgressorLabel('Kopiere Template-Ordner')
        arcpy.SetProgressorPosition(20)

        try:
            shutil.copytree(self.folders.PROJECT_TEMPLATE, project_path)
        except Exception as e:
            arcpy.AddMessage(e)
            print e
            arcpy.AddMessage("Es ist ein Fehler beim Kopieren aufgetreten.")
            arcpy.AddMessage("Es scheint bereits ein Projekt mit diesem " +
                             "Namen zu existieren")
            arcpy.AddMessage("Bitte geben Sie einen anderen Namen ein oder " +
                             "nutzen Sie die 'Projekt löschen' Funktion in " +
                             "der Toolbox")
            sys.exit()

    def get_gemeinde(self, tfl, id_column, max_dist):
        """Verschneide Teilflächen mit Gemeinde"""
        # to do (Stefaan)
        arcpy.SetProgressorLabel('Verschneide Teilflächen mit Gemeinde')
        arcpy.SetProgressorPosition(10)

        # calculate Gauß-Krüger-Coordinates and append them to tfl
        arcpy.AddGeometryAttributes_management(
            Input_Features=tfl, Geometry_Properties="CENTROID_INSIDE")

        # Check if the distances between the centroids is smaller than max_dist
        toolbox = self.parent_tbx
        XY_INSIDE = toolbox.query_table("Teilflaechen_Plangebiet",
                                        ['INSIDE_X', 'INSIDE_Y'])
        INSIDE_X = [row[0] for row in XY_INSIDE]
        INSIDE_Y = [row[1] for row in XY_INSIDE]
        self._project_centroid = (np.mean(INSIDE_X), np.mean(INSIDE_Y))
        distances = []
        if len(XY_INSIDE) > 1:
            for i in range(len(XY_INSIDE)):
                for j in range(i):
                    dist = np.linalg.norm(np.subtract(XY_INSIDE[i], XY_INSIDE[j]))
                    distances.append(dist)
            if distances and max(distances) > max_dist:
                raise Exception("Der Abstand zwischen den Schwerpunkten der "
                                "Teilflächen darf nicht größer "
                                "als {} m sein!".format(max_dist))

        # get AGS and Gemeindename and check if AGS is unique
        ags_gen = get_ags(tfl, id_column)
        ags_project = [ID[0] for ID in ags_gen.values()]
        gen_project =  [ID[1] for ID in ags_gen.values()]
        if len(np.unique(ags_project)) != 1:
            raise Exception("Die Teilflächen müssen in der selben Gemeinde"
                            "liegen")

        return ags_project[0], gen_project[0]

    def set_source_xy(self):
        toolbox = self.parent_tbx
        in_workspace = 'FGDB_Definition_Projekt.gdb'
        out_workspace = 'FGDB_Verkehr.gdb'
        in_table = 'Teilflaechen_Plangebiet'
        out_table = 'Anbindungspunkte'
        in_data = toolbox.query_table(in_table,
                                      columns=['INSIDE_X',
                                               'INSIDE_Y',
                                               'id_teilflaeche'],
                                      workspace=in_workspace)
        for shape_x, shape_y, area in in_data:
            shape = arcpy.Point(shape_x, shape_y)
            toolbox.upsert_row_in_table(
                table_name=out_table,
                column_values={'Shape': shape,
                               'id_teilflaeche': area},
                pkey={'id_teilflaeche': area},
                workspace=out_workspace)

    def communities_to_centers(self, centroid, radius):
        '''get communities intersecting with bbox and write them as centers to
        the database'''
        import time
        start = time.time()
        vg = self.parent_tbx.folders.get_base_table(
            table='Verwaltungsgemeinschaften_dissolved',
            workspace='FGDB_Basisdaten_deutschland.gdb')
        gemeinden = self.parent_tbx.folders.get_base_table(
            table='bkg_gemeinden', workspace='FGDB_Basisdaten_deutschland.gdb')
        centroid = Point(centroid[0], centroid[1])
        # circular buffer for clipping
        centroid.create_geom()
        pntGeom = arcpy.PointGeometry(centroid.geom)
        circleGeom = pntGeom.buffer(radius)
        fc_bbox = 'in_memory/bbox'
        fc_clipped = 'in_memory/clipped'
        if arcpy.Exists(fc_bbox):
            arcpy.Delete_management(fc_bbox)
        if arcpy.Exists(fc_clipped):
            arcpy.Delete_management(fc_clipped)
        arcpy.CopyFeatures_management([circleGeom], fc_bbox)
        arcpy.Clip_analysis(vg, fc_bbox, fc_clipped)

        cursor = arcpy.da.SearchCursor(fc_clipped, ['SHAPE@', 'GEN', 'RS'])
        id = 1
        rs_list = []
        # add clipped vg as centers
        for shape, name, rs in cursor:
            rs_list.append(rs)
            c2 = arcpy.da.SearchCursor(vg, ['SHAPE@'],
                                       where_clause=''' "RS"='{}' '''.format(rs))
            shape = c2.next()[0]
            del(c2)
            self.parent_tbx.insert_rows_in_table(
                'Zentren',
                workspace='FGDB_Standortkonkurrenz_Supermaerkte.gdb',
                column_values={
                    'SHAPE@': shape,
                    'name': name,
                    'nutzerdefiniert': -1,  # -1 indicates that it is a vg for selection and output only
                    'umsatz_differenz': 0,
                    'umsatz_planfall': 0,
                    'umsatz_nullfall': 0,
                    'id': id,
                    'Auswahl': 0,
                    'AGS': '',
                    'RS': rs
                })
            id += 1

        del cursor
        arcpy.Delete_management(fc_bbox)
        arcpy.Delete_management(fc_clipped)

        rs_project = None

        cursor = arcpy.da.SearchCursor(gemeinden, ['SHAPE@', 'GEN', 'AGS', 'RS'])
        for shape, name, ags, rs in cursor:
            cut_rs = rs[:9]
            if cut_rs in rs_list:
                if ags == self._project_ags:
                    rs_project = cut_rs
                self.parent_tbx.insert_rows_in_table(
                    'Zentren',
                    workspace='FGDB_Standortkonkurrenz_Supermaerkte.gdb',
                    column_values={
                        'SHAPE@': shape,
                        'name': name,
                        'nutzerdefiniert': 0,  # 0 indicates gemeinden, for calculations only
                        'umsatz_differenz': 0,
                        'umsatz_planfall': 0,
                        'umsatz_nullfall': 0,
                        'id': id,
                        'Auswahl': 0,
                        'AGS': ags,
                        'RS': cut_rs,
                    }
                )
            id += 1

        # preselect the VG the project is in
        if rs_project:
            self.parent_tbx.update_table(
                'Zentren', {'Auswahl': -1},  # -1 : not unselectable
                where='"RS" = \'{}\''.format(rs_project),
                workspace='FGDB_Standortkonkurrenz_Supermaerkte.gdb')

        print('Dauer: {}'.format(time.time() - start))


class ProjektKopieren(Projektverwaltung):
    _param_projectname = 'name'

    def run(self):
        """"""
        self.output.define_projection()
        self.projekt_kopieren()
        #self.add_diagramm()
        self.parent_tbx.config.active_project = self.projectname

    def projekt_kopieren(self):
        """"""
        arcpy.SetProgressorLabel('Kopiere Projekt')
        arcpy.SetProgressorPosition(10)

        # get new Project Name as input
        projectNameOld = self.par.existing_project.value

        # copy template folder
        template_path = self.folders.get_projectpath(projectNameOld)
        project_path = self.folders.get_projectpath(check=False)

        try:
            def ignore_locks(path, filenames):
                return [f for f in filenames if f.endswith('.lock')]
            shutil.copytree(template_path, project_path, ignore=ignore_locks)
        except Exception as e:
            arcpy.AddMessage(e)
            arcpy.AddMessage("Es ist ein Fehler beim Kopieren aufgetreten.")
            arcpy.AddMessage("Es scheint bereits ein Projekt "
                             "mit diesem Namen zu existieren")
            arcpy.AddMessage("Bitte geben Sie einen anderen Namen ein "
                             "oder nutzen Sie die 'Projekt löschen' Funktion "
                             "in der Toolbox")
            sys.exit()

        arcpy.SetProgressorPosition(70)

        # output information to user
        arcpy.AddMessage("Succesfully copied")
        arcpy.AddMessage("New Project registered at {}".format(project_path))


class ProjektLoeschen(Tool):

    def add_outputs(self):
        pass

    def run(self):
        # prevent eventual locks
        gc.collect()
        self.fragments_left = []
        arcpy.AddMessage(encode('Lösche Projekte'))

        projects_to_delete = self.par.projekte.values
        step = 100 / len(projects_to_delete)
        pos = 0
        for project in projects_to_delete:
            pos += step
            arcpy.SetProgressorPosition(pos)
            arcpy.SetProgressorLabel(
                encode(u'Lösche Projekt {}'.format(project)))
            self.compact_gdbs(project)
            self.remove_project_from_output(project)
            self.projekt_loeschen(project)
        config = self.parent_tbx.config
        if len(self.fragments_left) > 0:
            arcpy.AddError(u'Folgende Projekte konnten aufgrund von '
                           u'Schemasperren nicht restlos entfernt werden:')
            arcpy.AddError(', '.join(self.fragments_left))
            arcpy.AddError('Bitte starten Sie ArcMap neu und '
                           'versuchen Sie es erneut!')

        # change active project, if it was deleted
        if config.active_project in projects_to_delete:
            projects = self.folders.get_projects()
            config.active_project = projects[0] if len(projects) > 0 else ''

    def compact_gdbs(self, project):
        """
        compact all filegeodatabases to remove locks
        """
        projektPfad = self.folders.get_projectpath(project)
        for root, dirs, files in os.walk(projektPfad):
            for folder in dirs:
                if folder.endswith(".gdb"):
                    gdb = join(root, folder)
                    arcpy.AddMessage(u'Compact {}'.format(gdb))
                    try:
                        res = arcpy.Compact_management(gdb)
                        # del res could help to avoid schema locks
                        del res
                        gc.collect()
                        arcpy.AddMessage(u'Delete {}'.format(gdb))
                        res = arcpy.Delete_management(gdb)
                        del res
                    except arcpy.ExecuteError:
                        # .gdb-folder is no valid fgdb
                        # try with shutil.rmtree instead
                        shutil.rmtree(gdb, ignore_errors=True)

    def remove_project_from_output(self, project):
        """Remove Layers under Project GroupLayer"""
        # entferne alle aktuellen Layer aus dem TOC (Locks aufheben)
        arcpy.AddMessage("Loese aktive Layer aus MXD \n")
        mxd = arcpy.mapping.MapDocument("CURRENT")
        for df in arcpy.mapping.ListDataFrames(mxd):
            project_layer = self.output.get_projectlayer(project)
            for lyr in arcpy.mapping.ListLayers(project_layer, "", df):
                arcpy.mapping.RemoveLayer(df, lyr)
            del(project_layer)
        del(mxd)

    def projekt_loeschen(self, project_name):
        arcpy.AddMessage(u"Projektname: " + project_name)
        # Mit dem Projektnamen zum neuen Projektpfad zusammenführen"
        projektPfad = self.folders.get_projectpath(project_name)
        arcpy.AddMessage(u"Suche Ordner: " + projektPfad)

        # Überprüfen, ob der Projektordner existiert
        if isdir(projektPfad):
            arcpy.AddMessage("Projektordner gefunden \n")
            shutil.rmtree(projektPfad, ignore_errors=True)
            try:
                arcpy.Delete_management(projektPfad)
            except:
                pass
            arcpy.AddMessage(u"Projektordner gelöscht \n")
        else:
            arcpy.AddMessage(u"Projektordner " + project_name + u" nicht gefunden \n")

        arcpy.AddMessage("*" * 45)
        if arcpy.Exists(projektPfad):
            self.fragments_left.append(project_name)
            arcpy.AddError(encode('Projekt {p} konnte nicht vollständig gelöscht '
                           'werden.'.format(p=project_name)))
        else:
            arcpy.AddMessage("Das Projekt " + project_name + " wurde erfolgreich entfernt \n")
