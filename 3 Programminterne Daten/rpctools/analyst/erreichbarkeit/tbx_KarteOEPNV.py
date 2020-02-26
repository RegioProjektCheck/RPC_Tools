# -*- coding: utf-8 -*-

import arcpy
from pyproj import Proj, transform
from rpctools.utils.params import Tbx
from rpctools.utils.encoding import encode
import rpctools.utils.chronik as c
import numpy as np
import rpctools.utils.weighted_mean as wmean
import webbrowser
import os
import sys
from rpctools.utils.params import Tool

class KarteOEPNV(Tool):
    _param_projectname = 'projectname'
    _workspace = 'FGDB_Erreichbarkeit.gdb'

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
        arcpy.AddMessage(x)
        arcpy.AddMessage(y)
        inProj = Proj(init='epsg:31466')
        outProj = Proj(init='epsg:4326')
        x,y = transform(inProj,outProj,x,y)
        arcpy.AddMessage(x)
        arcpy.AddMessage(y)
        url = "https://www.xn--pnvkarte-m4a.de/#{};{};15".format(x, y)
        webbrowser.open(url, new=1, autoraise=True)

    def add_outputs(self):
        return



class TbxKarteOEPNV(Tbx):
    """Toolbox OEPNV-Karte"""

    @property
    def label(self):
        return u'OEPNV-Karte'

    @property
    def Tool(self):
        return(KarteOEPNV)


    def _getParameterInfo(self):

        par = self.par
        params = self.par

        param = self.add_parameter('projectname')
        param.name = encode(u'Projekt_auswählen')
        param.displayName = encode(u'Projekt')
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'GPString'
        param.filter.list = []


        return params


    def _updateMessages(self, params):

        par = self.par
      
