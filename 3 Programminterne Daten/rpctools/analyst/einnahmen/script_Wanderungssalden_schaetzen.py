# -*- coding: utf-8 -*-
import arcpy, sys
import numpy as np
import os, inspect, pyodbc, shutil, gc, datetime, xlsxwriter, imp
from xlsxwriter.utility import xl_rowcol_to_cell
from os.path import join, isdir, abspath, dirname, basename

import rpctools.utils.weighted_mean as wmean
import rpctools.utils.tempmdb_lib as mdb
import rpctools.utils.allgemeine_Rahmendaten as rahmendaten
import rpctools.utils.chronik as c
import rpctools.utils.layer_einnahmen as lib_einnahmen

def Wanderungssalden_schaetzen(self):

    parameters = self.par
    projektname = self.projectname

    cursor = self.parent_tbx.query_table(table_name = 'Chronik_Nutzung',
                            columns = ['Arbeitsschritt', 'Letzte_Nutzung'],
                            workspace='FGDB_Einnahmen.gdb')
    salden_berechnet = True
    for row in cursor:
        if row[0] == "Wanderung Einwohner" and row[1] is None:
            salden_berechnet = False

    if self.par.aktualisieren.value == True or salden_berechnet == False:
        lib_einnahmen.create_gemeindebilanzen(self, projektname)

        workspace_projekt_definition = self.folders.get_db('FGDB_Definition_Projekt.gdb', projektname)
        workspace_projekt_einnahmen = self.folders.get_db('FGDB_Einnahmen.gdb', projektname)
        wanderungssalden = os.path.join(workspace_projekt_einnahmen, "Gemeindebilanzen")

        projektflaechen = join(workspace_projekt_definition, 'Teilflaechen_Plangebiet')
        if  arcpy.Exists("projektflaechen_lyr"):
            arcpy.Delete_management("projektflaechen_lyr")
        arcpy.MakeFeatureLayer_management(projektflaechen, "projektflaechen_lyr")

        fields = ["Einw_Zuzug", "Einw_Fortzug", "Einw_Saldo", "Wanderungsanteil_Ew", "Gewichtete_Ew", "SvB_Zuzug", "SvB_Fortzug", "SvB_Saldo"]
        cursor = arcpy.da.UpdateCursor(wanderungssalden, fields)
        for gemeinde in cursor:
            gemeinde[0] = 0
            gemeinde[1] = 0
            gemeinde[2] = 0
            gemeinde[3] = 0
            gemeinde[4] = 0
            gemeinde[5] = 0
            gemeinde[6] = 0
            gemeinde[7] = 0
            cursor.updateRow(gemeinde)


        #Wichtungsfaktoren auslesen
        Wichtungen_Gewerbe = {}
        Wichtungen_Wohnen = {}

        path_distanzen = self.folders.get_base_table("FGDB_Einnahmen_Tool.gdb", "Wanderung_Entfernungswichtung")
        cursor = arcpy.da.SearchCursor(path_distanzen, ["Distance", "Wichtung_Wohnen", "Wichtung_Gewerbe"])
        for distanz in cursor:
            Wichtungen_Wohnen[str(int(distanz[0]))] = distanz[1]
            Wichtungen_Gewerbe[str(int(distanz[0]))] = distanz[2]
        #arcpy.AddMessage(Wichtungen_Wohnen)


        #Randsummen Wanderung auslesen (Anteile innerhalb/außerhalb 25km und Neugründungen [nur Gewerbe])
        Randsummen_Gewerbe = {}
        Randsummen_Wohnen = {}
        path_randsummen = self.folders.get_base_table("FGDB_Einnahmen_Tool.gdb", "Wanderung_Randsummen")
        cursor = arcpy.da.SearchCursor(path_randsummen, ["IDWanderungstyp", "Anteil_Wohnen", "Anteil_Gewerbe"])
        for randsumme in cursor:
            Randsummen_Wohnen[randsumme[0]] = randsumme[1]
            Randsummen_Gewerbe[randsumme[0]] = randsumme[2]
        #arcpy.AddMessage(Randsummen_Wohnen)


        #Anteile der Herkunftsgemeinden an Einwohner bestimmen
        pfad_buffer = os.path.join(workspace_projekt_einnahmen, "buffer_25km")
        if arcpy.Exists(pfad_buffer):
            arcpy.Delete_management(pfad_buffer)

        pfad_Rasterausschnitt = os.path.join(workspace_projekt_einnahmen, "Rasterausschnitt")
        if arcpy.Exists(pfad_Rasterausschnitt):
            arcpy.Delete_management(pfad_Rasterausschnitt)

        pfad_Rasterausschnitt_25km = os.path.join(workspace_projekt_einnahmen, "Rasterausschnitt_25km")
        if arcpy.Exists(pfad_Rasterausschnitt_25km):
            arcpy.Delete_management(pfad_Rasterausschnitt_25km)

        pfad_Punktlayer_25km_posWerte = os.path.join(workspace_projekt_einnahmen, "Punktlayer_25km_posWerte")
        if arcpy.Exists(pfad_Punktlayer_25km_posWerte):
            arcpy.Delete_management(pfad_Punktlayer_25km_posWerte)

        pfad_Entfernungsringe = os.path.join(workspace_projekt_einnahmen, "Entfernungsringe")
        if arcpy.Exists(pfad_Entfernungsringe):
            arcpy.Delete_management(pfad_Entfernungsringe)

        pfad_Herkunftsraeume = os.path.join(workspace_projekt_einnahmen, "Herkunftsgebiete")
        if arcpy.Exists(pfad_Herkunftsraeume):
            arcpy.Delete_management(pfad_Herkunftsraeume)

        pfad_Herkunftsraeume_mit_Ew = os.path.join(workspace_projekt_einnahmen, "Herkunftsgebiete_mit_Ew")
        if arcpy.Exists(pfad_Herkunftsraeume_mit_Ew):
            arcpy.Delete_management(pfad_Herkunftsraeume_mit_Ew)

        pfad_zensusgrid = self.folders.ZENSUS_RASTER_FILE
        pfad_bkggemeinden = self.folders.get_base_table("FGDB_Basisdaten_deutschland.gdb", "bkg_gemeinden")


        #25km Buffer um Projektflaeche
        arcpy.Buffer_analysis(projektflaechen, pfad_buffer, "25000 Meters", "FULL", "ROUND", "ALL", "", "PLANAR")

        #Extent des Buffers auslesen
        desc = arcpy.Describe(pfad_buffer)
        xmin = desc.extent.XMin
        xmax = desc.extent.XMax
        ymin = desc.extent.YMin
        ymax = desc.extent.YMax

        #Verschneidung mit Zensusraster
        arcpy.Clip_management(pfad_zensusgrid, "%s %s %s %s" % (xmin, ymin, xmax, ymax), pfad_Rasterausschnitt, pfad_buffer, "2147483647", "ClippingGeometry", "NO_MAINTAIN_EXTENT")

        #Raterausschnitt in Punktlayer konvertieren
        arcpy.RasterToPoint_conversion(pfad_Rasterausschnitt, pfad_Rasterausschnitt_25km, "Value")

        #LeereSiedlungszellen entfernen
        arcpy.Select_analysis(pfad_Rasterausschnitt_25km, pfad_Punktlayer_25km_posWerte, '"grid_code" > 0')

        #Mehrere Buffer um Projektflaeche erzeugen
        arcpy.MultipleRingBuffer_analysis(projektflaechen, pfad_Entfernungsringe, "1500;2500;3500;4500;6500;8500;11500;14500;18500;25000", "Meters", "distance", "ALL", "FULL")

        #Buffer mit Gemeinden verschneiden
        arcpy.Intersect_analysis([pfad_bkggemeinden, pfad_Entfernungsringe], pfad_Herkunftsraeume, "NO_FID", "", "INPUT")

        #Verschneiden der Herkunftsraume mit den Summen der jeweiligen Punktfeatures

        fieldmappings = arcpy.FieldMappings()
        fieldmappings.addTable(pfad_Herkunftsraeume)
        fieldmappings.addTable(pfad_Punktlayer_25km_posWerte)

        gridcode_FieldIndex = fieldmappings.findFieldMapIndex("grid_code")
        fieldmap = fieldmappings.getFieldMap(gridcode_FieldIndex)
        field = fieldmap.outputField
        field.name = "Summe_Ew"
        field.aliasName = "Summe_Ew"
        fieldmap.outputField = field
        fieldmap.mergeRule = "sum"
        fieldmappings.replaceFieldMap(gridcode_FieldIndex, fieldmap)

        arcpy.SpatialJoin_analysis(pfad_Herkunftsraeume, pfad_Punktlayer_25km_posWerte, pfad_Herkunftsraeume_mit_Ew, "JOIN_ONE_TO_ONE", "KEEP_ALL", fieldmappings)


        #SvB_je_EW

        Summe_Wichtungsfaktoren_Gesamtraum_Wohnen = 0
        Summe_Wichtungsfaktoren_Gesamtraum_Gewerbe = 0
        Summe_Wichtungsfaktoren_Gemeinde_Wohnen = 0
        Summe_Wichtungsfaktoren_Gemeinde_Gewerbe = 0
        SvB_je_EW = 0
        herkunftsraeume = []

        cursor_gemeindebilanz = arcpy.da.SearchCursor(wanderungssalden, ["AGS", "SvB_pro_Ew"])
        for gemeinde in cursor_gemeindebilanz:
            where = '"AGS"' + "='" + gemeinde[0] +"'"
            cursor_Summe_Ew = arcpy.da.SearchCursor(pfad_Herkunftsraeume_mit_Ew, ["AGS", "Summe_Ew", "distance"], where)
            for gemeindeteil in cursor_Summe_Ew:
                if gemeindeteil[1] >= 1:
                    Wichtungsfaktor_Wohnen = gemeindeteil[1] * Wichtungen_Wohnen[str(int(gemeindeteil[2]))]
                    Wichtungsfaktor_Gewerbe = gemeindeteil[1] * gemeinde[1] *  Wichtungen_Gewerbe[str(int(gemeindeteil[2]))]
                    herkunftsraeume.append([gemeindeteil[0], Wichtungsfaktor_Wohnen, Wichtungsfaktor_Gewerbe])
                    Summe_Wichtungsfaktoren_Gesamtraum_Wohnen += Wichtungsfaktor_Wohnen
                    Summe_Wichtungsfaktoren_Gesamtraum_Gewerbe += Wichtungsfaktor_Gewerbe

        ap = 0
        bewohner = 0
        teilflaechen = self.folders.get_table("Teilflaechen_Plangebiet", "FGDB_Definition_Projekt.gdb")
        rahmendaten = self.folders.get_table("Projektrahmendaten", "FGDB_Definition_Projekt.gdb")
        cursor = arcpy.da.SearchCursor(rahmendaten,["AGS"])
        for row in cursor:
            ags_projekt = row[0]
        cursor = arcpy.da.SearchCursor(teilflaechen, ["ew", "AP_gesamt"])
        for flaeche in cursor:
            ap += flaeche[1]
            bewohner += flaeche[0]

        #Aufteilung Fortzug (und Zuzug [nur Projektgemeinde])
        cursor_gemeindebilanz = arcpy.da.UpdateCursor(wanderungssalden, ["AGS", "SvB_pro_Ew", "Einw_Fortzug", "SvB_Fortzug", "Einw_Zuzug", "SvB_Zuzug", "SvB_Saldo", "Einw_Saldo", "Wanderungsanteil_Ew", "Wanderungsanteil_SvB"])
        for gemeinde in cursor_gemeindebilanz:
            Summe_Wichtungsfaktoren_Gemeinde_Wohnen = 0
            Summe_Wichtungsfaktoren_Gemeinde_Gewerbe = 0
            for raum in herkunftsraeume:
                if raum[0] == gemeinde[0]:
                    Summe_Wichtungsfaktoren_Gemeinde_Wohnen += raum[1]
                    Summe_Wichtungsfaktoren_Gemeinde_Gewerbe += raum[2]
            Einw_Fortzug_neu = -1 * (bewohner * Randsummen_Wohnen[1] * Summe_Wichtungsfaktoren_Gemeinde_Wohnen / Summe_Wichtungsfaktoren_Gesamtraum_Wohnen)
            if Einw_Fortzug_neu != 0:
                gemeinde[2] = Einw_Fortzug_neu# - 0.5
            else:
                gemeinde[2] = Einw_Fortzug_neu
            SvB_Fortzug_neu = -1 * (ap * Randsummen_Gewerbe[1] * Summe_Wichtungsfaktoren_Gemeinde_Gewerbe / Summe_Wichtungsfaktoren_Gesamtraum_Gewerbe)
            if SvB_Fortzug_neu != 0:
                gemeinde[3] = SvB_Fortzug_neu# - 0.5
            else:
                gemeinde[3] = SvB_Fortzug_neu
            if gemeinde[0] == ags_projekt:
                gemeinde[4] = bewohner
                gemeinde[5] = ap
            else:
                gemeinde[8] = Summe_Wichtungsfaktoren_Gemeinde_Wohnen / Summe_Wichtungsfaktoren_Gesamtraum_Wohnen
                gemeinde[9] = Summe_Wichtungsfaktoren_Gemeinde_Gewerbe / Summe_Wichtungsfaktoren_Gesamtraum_Gewerbe
            gemeinde[6] = gemeinde[3] + gemeinde[5]
            gemeinde[7] = gemeinde[4] + gemeinde[2]
            cursor_gemeindebilanz.updateRow(gemeinde)

        #Summe der zugeordneten Fortzüge (innerhalb 25 km) und Zuzüge [jeweils inkl. Rundungseffekte]
        Summe_Zugeordneter_Fortzug_Ew = 0.0
        Summe_Zugeordneter_Zuzug_Ew = 0.0
        Summe_Zugeordneter_Fortzug_AP = 0.0
        Summe_Zugeordneter_Zuzug_AP = 0.0
        cursor_summe = arcpy.da.SearchCursor(wanderungssalden, ["AGS", "SvB_pro_Ew", "Einw_Fortzug", "SvB_Fortzug", "Einw_Zuzug", "SvB_Zuzug", "SvB_Saldo", "Einw_Saldo"])
        for gemeinde in cursor_summe:
            Summe_Zugeordneter_Fortzug_Ew += gemeinde[2]
            Summe_Zugeordneter_Zuzug_Ew += gemeinde[4]
            Summe_Zugeordneter_Fortzug_AP += gemeinde[3]
            Summe_Zugeordneter_Zuzug_AP += gemeinde[5]
        Differenz_Ew = Summe_Zugeordneter_Zuzug_Ew + Summe_Zugeordneter_Fortzug_Ew
        Differenz_AP = Summe_Zugeordneter_Zuzug_AP + Summe_Zugeordneter_Fortzug_AP

        #Neugruendungen (nur Gewerbe)
        Neugruendungen_AP = ap * Randsummen_Gewerbe[3] + 0.5

        #Fortzüge aus dem restlichen Bundesgebiet/Welt (hier werden auch die Rundungsverluste ungebracht)
        Fortzuege_restliches_Bundesgebiet_und_Welt_Ew = -1 * Differenz_Ew
        Fortzuege_restliches_Bundesgebiet_und_Welt_AP = -1 * (Differenz_AP - Neugruendungen_AP)
        #arcpy.AddMessage("Wohnen: Fortzüge restliches Bundesgebiet = {0}".format(Fortzuege_restliches_Bundesgebiet_und_Welt_Ew))
        #arcpy.AddMessage("Gewerbe: Fortzüge restliches Bundesgebiet = {0}".format(Fortzuege_restliches_Bundesgebiet_und_Welt_AP))
        #arcpy.AddMessage("Gewerbe: Neugründungen = {0}".format(Neugruendungen_AP))

        self.parent_tbx.delete_rows_in_table("Zuzugsstatistik_Ew")
        column_values = {"Kategorie": [u"Projektgemeinde/Region", u"Restliches Bundesgebiet/Ausland"],
                            "Anzahl": [int(round(Summe_Zugeordneter_Fortzug_Ew * -1)), int(round(Differenz_Ew))]}
        self.parent_tbx.insert_rows_in_table("Zuzugsstatistik_Ew", column_values)

        self.parent_tbx.delete_rows_in_table("Zuzugsstatistik_SvB")
        column_values = {"Kategorie": [u"Projektgemeinde/Region", u"Restliches Bundesgebiet/Ausland", u"Neugründungen"],
                         "Anzahl": [int(round(Summe_Zugeordneter_Fortzug_AP * -1)), int(round((Differenz_AP - Neugruendungen_AP))), int(round(Neugruendungen_AP))]}
        self.parent_tbx.insert_rows_in_table("Zuzugsstatistik_SvB", column_values)

        c.set_chronicle("Wanderung Einwohner", self.folders.get_table(tablename='Chronik_Nutzung',workspace="FGDB_Einnahmen.gdb",project=projektname))
        c.set_chronicle("Wanderung Beschaeftigte", self.folders.get_table(tablename='Chronik_Nutzung',workspace="FGDB_Einnahmen.gdb",project=projektname))
