# -*- coding: utf-8 -*-

import arcpy, sys
import numpy as np
import arcpy, os, inspect, pyodbc, shutil, gc, sys, datetime, xlsxwriter, imp
from xlsxwriter.utility import xl_rowcol_to_cell
from os.path import join, isdir, abspath, dirname, basename
import rpctools.utils.output as output
from rpctools.utils.params import Tool
import rpctools.utils.weighted_mean as wmean
import rpctools.utils.tempmdb_lib as mdb
import rpctools.utils.allgemeine_Rahmendaten as rahmendaten
import rpctools.utils.chronik as c
import rpctools.utils.layer_einnahmen as lib_einnahmen

class Wanderungssalden1(Tool):

    _param_projectname = 'name'
    _workspace = 'FGDB_Einnahmen.gdb'

    def run(self):

        parameters = self.par
        projektname = self.projectname

        lib_einnahmen.create_gemeindebilanzen(self, projektname)

        workspace_projekt_definition = self.folders.get_db('FGDB_Definition_Projekt.gdb', projektname)
        workspace_projekt_einnahmen = self.folders.get_db('FGDB_Einnahmen.gdb', projektname)
        wanderungssalden = os.path.join(workspace_projekt_einnahmen, "Gemeindebilanzen")

        projektflaechen = join(workspace_projekt_definition, 'Teilflaechen_Plangebiet')
        if  arcpy.Exists("projektflaechen_lyr"):
            arcpy.Delete_management("projektflaechen_lyr")
        arcpy.MakeFeatureLayer_management(projektflaechen, "projektflaechen_lyr")

        fields = ["Einw_Zuzug", "Einw_Fortzug", "Einw_Saldo", "Wanderungsanteil_Ew", "Gewichtete_Ew"]
        cursor = arcpy.da.UpdateCursor(wanderungssalden, fields)
        for gemeinde in cursor:
            gemeinde[0] = 0
            gemeinde[1] = 0
            gemeinde[2] = 0
            gemeinde[3] = 0
            gemeinde[4] = 0
            cursor.updateRow(gemeinde)

        km = 20
        umkreis_km = str(km) + " Kilometers"

    #Alte Layer löschen
        self.output.delete_output("Wanderungssalden Einwohner")

    # Anteile der Herkunftsgemeinden an Einwohner bestimmen

        # Buffer um Teilflächen
        pfad_buffer = os.path.join(workspace_projekt_einnahmen, "Buffer")
        if arcpy.Exists(pfad_buffer):
            arcpy.Delete_management(pfad_buffer)

        arcpy.Buffer_analysis(
                                in_features = "projektflaechen_lyr",
                                out_feature_class = pfad_buffer,
                                buffer_distance_or_field = umkreis_km,
                                dissolve_option = "ALL")

        # Verschneiden von Buffer und Gemeindebilanzen-Gemeinde-Layer
        pfad_verschnitt = os.path.join(workspace_projekt_einnahmen, "Verschnitt")
        if arcpy.Exists(pfad_verschnitt):
            arcpy.Delete_management(pfad_verschnitt)

        arcpy.Intersect_analysis([wanderungssalden, pfad_buffer], pfad_verschnitt)

        # Parameter: Exponentialfaktoren für Umzugsweiten Wohnen und Gewerbe
        exponentialfaktor_wohnen = -0.1
        konstant_bis_km_wohnen = 3

        # Mittelpunkt der Projektflächen
        table = 'Teilflaechen_Plangebiet'
        columns = np.array(['Nutzungsart', 'Flaeche_ha', 'INSIDE_X', 'INSIDE_Y'])
        Results = wmean.Read_FGDB(workspace_projekt_definition, table, columns)
        Results.get_result_block()
        gewichtete_koordinaten = wmean.calc_weighted_mean(Results.result_block)
        x_projektflaeche = gewichtete_koordinaten[0]
        y_projektflaeche = gewichtete_koordinaten[1]

        # Gewichtete Einwohner bestimmen
        gewichtete_ew_gesamt = 0
        fields = ["AGS", "Einwohner", "Shape_Area", "Gewichtete_Ew", "GK3_X", "GK3_Y"]
        cursor = arcpy.da.UpdateCursor(wanderungssalden, fields)
        for gemeinde in cursor:
            flaeche_verschnitt = 0
            cursor_verschnitt = arcpy.da.SearchCursor(pfad_verschnitt, ["AGS", "Shape_Area"])
            for gemeinde_verschnitt in cursor_verschnitt:
                if gemeinde[0] == gemeinde_verschnitt[0]:
                    flaeche_verschnitt += gemeinde_verschnitt[1]
            entfernung_km = (((x_projektflaeche - gemeinde[4]) ** 2 +  (y_projektflaeche - gemeinde[5]) ** 2) ** 0.5) / 1000
            # Einwohner
            if entfernung_km < konstant_bis_km_wohnen:
                entfernungsgewichtung_wohnen = 1
            else:
                entfernungsgewichtung_wohnen = np.exp((entfernung_km - konstant_bis_km_wohnen) * exponentialfaktor_wohnen)
            gewichtete_ew = gemeinde[1] * (flaeche_verschnitt / gemeinde[2]) * entfernungsgewichtung_wohnen
            gemeinde[3] = gewichtete_ew
            gewichtete_ew_gesamt += gewichtete_ew
            cursor.updateRow(gemeinde)

        # Wanderungsanteile bestimmen
        fields = ["Gewichtete_Ew", "Wanderungsanteil_Ew"]
        cursor = arcpy.da.UpdateCursor(wanderungssalden, fields)
        for gemeinde in cursor:

            gemeinde[1] = gemeinde[0] / gewichtete_ew_gesamt
            cursor.updateRow(gemeinde)

        # Berechnung der Einwohner im Plangebiet
        einwohner_projekt = rahmendaten.Bewohner_referenz_plangebiet(self, projektname)

        # Bestimme AGS der Projektgemeinde
        pfad_rahmendaten = self.folders.get_table(
            tablename='Projektrahmendaten',
            workspace="FGDB_Definition_Projekt.gdb",
            project=projektname)
        cursor = arcpy.da.SearchCursor(pfad_rahmendaten, ["AGS"])
        for projekt in cursor:
            ags_projekt = projekt[0]


        #Ergebnis einfügen
        liste_salden = []
        fields = ["Einw_Zuzug", "Einw_Fortzug", "Einw_Saldo", "Wanderungsanteil_Ew", "AGS"]
        cursor = arcpy.da.UpdateCursor(wanderungssalden, fields)
        for gemeinde in cursor:
            gemeinde[1] = einwohner_projekt * gemeinde[3] * -1
            if gemeinde[4] == ags_projekt:
                gemeinde[0] = einwohner_projekt
            else:
                gemeinde[0] = 0
            gemeinde[2] = gemeinde[0] + gemeinde[1]
            liste_salden.append(gemeinde[2])
            cursor.updateRow(gemeinde)



        #Prüfen, ob  Wohngebiete existieren
        wohnen_exists = False

        table_teilflaechen = self.folders.get_table(
            tablename='Teilflaechen_Plangebiet',
            workspace="FGDB_Definition_Projekt.gdb",
            project=projektname)
        fields = "Nutzungsart"
        cursor = arcpy.da.SearchCursor(table_teilflaechen, fields)
        wohnen_gewerbe_exists = False

        for flaeche in cursor:
            if flaeche[0] == 1:
                wohnen_exists = True

##        groupname = "einnahmen"
##        tbl_wanderungssalden = self.folders.get_table("Gemeindebilanzen")
##        folder = "einnahmen"
##        disable_other = False
##        layer = lib_einnahmen.get_symbology(liste_salden, 1)
##        arcpy.AddMessage("Layer-Pfad:" + layer)
##        arcpy.AddMessage("tbl-Pfad:" + str(tbl_wanderungssalden))
##        #Einwohnersaldo-Layer hinzufügen
##        if wohnen_exists:
##                self.output.replace_output(
##                    groupname, tbl_wanderungssalden, "Skala_minus_x",
##                    folder, disable_other)
##
##        lyr = output.get_layers("Skala_minus_x", projektname)[0]
##
##        lyr.symbology.valueField = "Einw_Saldo"
##        lyr.symbology.classBreakValues = [-10, -8, -6, -4, -3, -2, -1, 0, 999999999]
##
##        arcpy.RefreshTOC()

        c.set_chronicle("Wanderung Einwohner", self.folders.get_table(tablename='Chronik_Nutzung',workspace="FGDB_Einnahmen.gdb",project=projektname))




