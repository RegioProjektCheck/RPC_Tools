# -*- coding: utf-8 -*-
import arcpy

from rpctools.utils.params import Tbx, Tool
from rpctools.utils.encoding import encode
from rpctools.analyst.standortkonkurrenz.market_templates import MarketTemplate
import os


class CreateTemplate(Tool):
    subfolder = 'input_templates'

    def add_outputs(self):
        pass

    def run(self):
        typ = self.par.template_type.value
        arcpy.AddMessage('Template wird erzeugt...')
    
        path = os.path.join(self.folders.get_projectpath(), self.subfolder)
        template = MarketTemplate(typ, path, epsg=self.parent_tbx.config.epsg)
        template.create()
        template.open()


class TbxCreateTemplate(Tbx):
    
    @property
    def label(self):
        return u'Template für Bestandsmärkte erzeugen'

    @property
    def Tool(self):
        return CreateTemplate

    def _getParameterInfo(self):
        
        # Projekt_auswählen
        param = self.add_parameter('projectname')
        param.name = encode(u'Projekt_auswählen')
        param.displayName = encode(u'Projekt auswählen')
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'GPString'
        param.filter.list = []
    
        param = self.add_parameter('template_type')
        param.name = encode(u'type')
        param.displayName = encode(u'Dateiformat des zu erzeugenden Templates')
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'GPString'
        param.filter.list = MarketTemplate.template_types.keys()
        param.value = param.filter.list[1]
        
        return self.par
    
    def _open(self, params):
        pass
    
    def validate_inputs(self):
        return True, ''
        
    def _updateParameters(self, params):
        return params

    def _updateMessages(self, params):
        pass

if __name__ == '__main__':
    t = TbxCreateTemplate()
    t._getParameterInfo()
    t.set_active_project()
    t.execute()