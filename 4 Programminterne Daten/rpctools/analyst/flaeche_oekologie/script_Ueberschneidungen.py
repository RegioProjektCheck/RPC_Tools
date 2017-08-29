# -*- coding: utf-8 -*-
import os
import sys
import numpy as np
import arcpy
from rpctools.utils.params import Tool
import rpctools.utils.weighted_mean as wmean
import webbrowser

class Ueberschneidungen(Tool):
    """Ueberschneidungen"""

    _param_projectname = 'name'
    _workspace = 'FGDB_Flaeche_und_Oekologie.gdb'

    def add_outputs(self):
        params = self.par

        if self.parent_tbx.layer_number == 1:
            path = "Waldgebiete"
        elif self.parent_tbx.layer_number == 2:
            path = "Natur_und_Artenschutz"
        elif self.parent_tbx.layer_number == 3:
            path = "Landschaftsschutz"
        elif self.parent_tbx.layer_number == 4:
            path = "Unzerschnittene_Freiraeume_100qkm"
        elif self.parent_tbx.layer_number == 5:
            path = "Unzerschnittene_Freiraeume_50qkm"
        elif self.parent_tbx.layer_number == 6:
            path = "Freiraumflaeche"
        elif self.parent_tbx.layer_number == 7:
            path = "Unzerschnittene_Waelder_50qkm"
        elif self.parent_tbx.layer_number == 8:
            path = "Hochspannungsleitungen"

        if self.parent_tbx.layer_number != 9:
            self.output.add_layer(groupname = "oekologie", template_layer = path, template_folder="oekologie", zoom=False, disable_other = True)
        #self.output.add_image("C:\\Temp\\hui.png", "Test")

            arcpy.RefreshTOC()
            arcpy.RefreshActiveView()


    def run(self):
        params = self.par
        projekt = self.projectname
        #self.output.enable_layer('projektdefinition')
        if self.parent_tbx.layer_number == 9:
            x = 3555857.414
            y = 5911101.900
            arcpy.AddMessage("hu: " + str(projekt))
            database = self.folders.get_db("FGDB_Definition_Projekt.gdb", projekt)
            table = 'Teilflaechen_Plangebiet'
            columns = np.array(['Nutzungsart', 'Flaeche_ha', 'INSIDE_X', 'INSIDE_Y'])
            Results = wmean.Read_FGDB(database, table, columns)
            Results.get_result_block()
            print(wmean.calc_weighted_mean(Results.result_block, Nutzungsart=0))
            url = "http://www.geodienste.bfn.de/schutzgebiete/#?centerX={}?centerY={}?scale=50000?layers=639".format(x, y)
            webbrowser.open(url, new=1, autoraise=True)










