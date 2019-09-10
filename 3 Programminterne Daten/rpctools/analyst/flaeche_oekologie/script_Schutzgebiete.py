# -*- coding: utf-8 -*-
import os
import sys
import numpy as np
import arcpy
from rpctools.utils.params import Tool
import rpctools.utils.weighted_mean as wmean
import webbrowser

class Schutzgebiete(Tool):
    """Ueberschneidungen"""

    _param_projectname = 'name'
    _workspace = 'FGDB_Flaeche_und_Oekologie.gdb'

    def add_outputs(self):
        params = self.par

    def run(self):
        params = self.par
        projekt = self.projectname
        database = self.folders.get_db("FGDB_Definition_Projekt.gdb", projekt)
        table = 'Teilflaechen_Plangebiet'
        columns = np.array(['Nutzungsart', 'Flaeche_ha', 'INSIDE_X', 'INSIDE_Y'])
        Results = wmean.Read_FGDB(database, table, columns)
        Results.get_result_block()
        coordinates = (wmean.calc_weighted_mean(Results.result_block))
        x = coordinates[0]
        y = coordinates[1]
        url = "http://www.geodienste.bfn.de/schutzgebiete/#?centerX={}?centerY={}?scale=50000?layers=639".format(x, y)
        webbrowser.open(url, new=1, autoraise=True)









