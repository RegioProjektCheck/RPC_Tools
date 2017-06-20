# -*- coding: utf-8 -*-
import os
import sys
import arcpy
import shutil
import re

from rpctools.utils.params import Tbx, Tool
from rpctools.utils.encoding import encode
from rpctools.analyst.standortkonkurrenz.market_templates import MarketTemplate
from rpctools.analyst.standortkonkurrenz.tbx_osm_markteinlesen import MarktEinlesen


class MaerkteImportieren(MarktEinlesen):
    _param_projectname = 'projectname'
    _workspace = 'FGDB_Standortkonkurrenz_Supermaerkte.gdb'
    
    def run(self):
        path, filename = os.path.split(self.par.filepath.value.value)
        name, ext = os.path.splitext(filename)
        # get type of template by reverse looking up file extension
        idx = MarketTemplate.template_types.values().index(ext)
        template_type = MarketTemplate.template_types.keys()[idx]
        template = MarketTemplate(template_type, path, filename=filename,
                                  epsg=self.parent_tbx.config.epsg)
        arcpy.AddMessage('Lese Datei ein...')
        markets = template.get_markets()
        truncate = self.par.truncate.value
        markets = self.parse_meta_by_chain(markets)
        arcpy.AddMessage(u'Schreibe {} Märkte in die Datenbank...'
                         .format(len(markets)))
        self.markets_to_db(markets, truncate=truncate)
        arcpy.AddMessage(u'Aktualisiere die AGS der Märkte...')
        self.set_ags()


class TbxMaerkteImportieren(Tbx):

    @property
    def label(self):
        return encode(u'Marktstandorte aus Datei importieren')

    @property
    def Tool(self):
        return MaerkteImportieren

    def _getParameterInfo(self):

        params = self.par

        # Projekt_auswählen
        param = self.add_parameter('projectname')
        param.name = encode(u'Projekt_auswählen')
        param.displayName = encode(u'Projekt auswählen')
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'GPString'
        param.filter.list = []

        param = self.add_parameter('filepath')
        param.name = encode(u'Datei')
        param.displayName = encode(u'Datei')
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'DEFile'
        #param.filter.type = 'File'
        param.filter.list = [e.replace('.', '')
                             for e in MarketTemplate.template_types.values()]
        #param.value = 1000
        
        param = self.add_parameter('truncate')
        param.name = encode(u'truncate')
        param.displayName = encode(u'vorhandene Märkte entfernen')
        param.parameterType = 'Optional'
        param.direction = 'Input'
        param.datatype = u'GPBoolean'

        return params

    def _updateParameters(self, params):

        return params


if __name__ == '__main__':
    t = TbxMaerkteImportieren()
    t._getParameterInfo()
    t.par.filepath.value = r'C:\Users\ggr\Desktop\templates\maerkte_template.shp'
    #t.par.filepath.value = r'C:\Users\ggr\Desktop\templates\maerkte_template.csv'
    t.set_active_project()
    t.execute()
