# -*- coding: utf-8 -*-

import os
import sys

import arcpy
from rpctools.utils.params import Tool
from rpctools.diagrams.diagram_oekologie import Dia_Nullfall
from rpctools.diagrams.diagram_oekologie import Dia_Planfall
import rpctools.utils.lib_oekologie as lib_oeko


class BodenbedeckungKontrolle(Tool):
    """BodenbedeckungKontrolle"""

    _param_projectname = 'name'
    _workspace = 'FGDB_Flaeche_und_Oekologie.gdb'

    def add_outputs(self):

        self.output.add_layer(groupname = "oekologie", featureclass = "Bodenbedeckung_Nullfall", template_layer = "Bodenbedeckung_Nullfall", template_folder="oekologie",  zoom=False, disable_other = True)
        self.output.add_layer(groupname = "oekologie", featureclass = "Bodenbedeckung_Planfall", template_layer = "Bodenbedeckung_Planfall", template_folder="oekologie",  zoom=False, disable_other = False)
        self.output.show_layers()

    def run(self):
        params = self.par
        projekt = self.projectname

        path_bodenbedeckung = self.folders.get_table('Bodenbedeckung_Anteile', "FGDB_Flaeche_und_Oekologie.gdb", projekt)

        fields = ["IDBodenbedeckung", "Planfall", "Bodenbedeckung_Anteil"]
        cursor = arcpy.da.UpdateCursor(path_bodenbedeckung, fields)
        for row in cursor:
            if row[1] == 0 and row[0] == 1:
                 row[2] = params.ueberbauteflaechen_alt.value
            elif row[1] == 0 and row[0] == 2:
                 row[2] = params.wasser_alt.value
            elif row[1] == 0 and row[0] == 3:
                 row[2] = params.platten_alt.value
            elif row[1] == 0 and row[0] == 4:
                 row[2] = params.baeume_alt.value
            elif row[1] == 0 and row[0] == 5:
                 row[2] = params.stauden_alt.value
            elif row[1] == 0 and row[0] == 6:
                 row[2] = params.wiese_alt.value
            elif row[1] == 0 and row[0] == 7:
                 row[2] = params.rasen_alt.value
            elif row[1] == 0 and row[0] == 8:
                 row[2] = params.rasengittersteine_alt.value
            elif row[1] == 0 and row[0] == 9:
                 row[2] = params.beton_alt.value
            elif row[1] == 0 and row[0] == 10:
                 row[2] =params.acker_alt.value
            elif row[1] == 0 and row[0] == 11:
                 row[2] = params.kleinpflaster_alt.value
            elif row[1] == 1 and row[0] == 1:
                 row[2] = params.ueberbauteflaechen_neu.value
            elif row[1] == 1 and row[0] == 2:
                 row[2] = params.wasser_neu.value
            elif row[1] == 1 and row[0] == 3:
                 row[2] = params.platten_neu.value
            elif row[1] == 1 and row[0] == 4:
                 row[2] =params.baeume_neu.value
            elif row[1] == 1 and row[0] == 5:
                 row[2] = params.stauden_neu.value
            elif row[1] == 1 and row[0] == 6:
                 row[2] = params.wiese_neu.value
            elif row[1] == 1 and row[0] == 7:
                 row[2] = params.rasen_neu.value
            elif row[1] == 1 and row[0] == 8:
                 row[2] = params.rasengittersteine_neu.value
            elif row[1] == 1 and row[0] == 9:
                 row[2] = params.beton_neu.value
            elif row[1] == 1 and row[0] == 10:
                 row[2] = params.acker_neu.value
            elif row[1] == 1 and row[0] == 11:
                 row[2] = params.kleinpflaster_neu.value

            cursor.updateRow(row)


class BodenbedeckungEntfernen(Tool):
    """BodenbedeckungEntfernen"""

    _param_projectname = 'name'
    _workspace = 'FGDB_Flaeche_und_Oekologie.gdb'

    def add_outputs(self):
        pass

    def run(self):
        params = self.par
        projekt = self.projectname

        table_nullfall = self.folders.get_table("Bodenbedeckung_Nullfall", "FGDB_Flaeche_und_Oekologie.gdb")
        table_planfall = self.folders.get_table("Bodenbedeckung_Planfall", "FGDB_Flaeche_und_Oekologie.gdb")

        if self.parent_tbx.nullfall == 1:
            cursor = arcpy.da.UpdateCursor(table_nullfall, ["*"])
            for row in cursor:
                cursor.deleteRow()
        else:
            cursor = arcpy.da.UpdateCursor(table_planfall, ["*"])
            for row in cursor:
                cursor.deleteRow()

        arcpy.RefreshTOC()
        arcpy.RefreshActiveView()


class BodenbedeckungAnzeigen(Tool):
    """BodenbedeckungAnzeigen"""

    _param_projectname = 'name'
    _workspace = 'FGDB_Flaeche_und_Oekologie.gdb'

    def add_outputs(self):

        if self.parent_tbx.nullfall == 1:
            self.output.add_layer(groupname = "oekologie", featureclass = "Bodenbedeckung_Nullfall", template_layer = "Bodenbedeckung_Nullfall", template_folder="oekologie", zoom=False, disable_other = True)
        else:
            self.output.add_layer(groupname = "oekologie", featureclass = "Bodenbedeckung_Planfall", template_layer = "Bodenbedeckung_Planfall", template_folder="oekologie", zoom=False, disable_other = True)
        self.output.show_layers()
        self.output.enable_layer('Hintergrund')
        self.output.enable_layer('Umriss des Plangebiets')

    def run(self):
        arcpy.AddMessage("Nullfall: " + str(self.parent_tbx.nullfall))


class BodenbedeckungZeichnen(Tool):
    """BodenbedeckungZeichnen"""

    _param_projectname = 'name'
    _workspace = 'FGDB_Flaeche_und_Oekologie.gdb'

    def add_outputs(self):

        if self.parent_tbx.nullfall == 1:
            diagram = Dia_Nullfall(projectname=self.par.name.value)
        else:
            diagram = Dia_Planfall(projectname=self.par.name.value)

        self.output.add_diagram(diagram)

        arcpy.RefreshTOC()
        arcpy.RefreshActiveView()

    def run(self):
        anteile_nullfall, anteile_planfall = lib_oeko.import_zeichenanteile(self.par.name.value)
        self.parent_tbx.delete_rows_in_table("Bodenbedeckung_Zeichnung")
        bodenarten = [u'Überbaut',
             u'Wasser',
             u'Platten',
             u'Bäume',
             u'Stauden',
             u'Wiese',
             u'Rasen',
             u'Gittersteine',
             u'Beton',
             u'Acker',
             u'Kleinpflaster',
            u'Undefiniert']
        column_values = {"Nullfall": anteile_nullfall,
                         "Planfall": anteile_planfall,
                         "Bodenbedeckung": bodenarten}
        self.parent_tbx.insert_rows_in_table("Bodenbedeckung_Zeichnung", column_values)

