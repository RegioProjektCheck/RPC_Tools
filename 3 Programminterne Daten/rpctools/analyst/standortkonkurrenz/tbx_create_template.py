# -*- coding: utf-8 -*-
import arcpy

from rpctools.utils.params import Tbx, Tool
from rpctools.utils.encoding import encode
from rpctools.analyst.standortkonkurrenz.market_templates import MarketTemplate
import os


class CreateTemplate(Tool):

    def add_outputs(self):
        pass

    def run(self):
        typ = self.par.template_type.value
        arcpy.AddMessage('Template wird erzeugt...')

        path = self.par.folder.value.value
        template = MarketTemplate(typ, path, epsg=self.parent_tbx.config.epsg)
        template.create()

        arcpy.AddMessage('Template wird geöffnet, bitte warten...')
        template.open()

        if self.par.show_help.value:
            fn = MarketTemplate.template_types[typ][1]
            fp = os.path.join(self.folders.MANUALS_PATH, fn)
            os.startfile(fp)


class TbxCreateTemplate(Tbx):

    @property
    def label(self):
        return u'Leere Erfassungsvorlage für Bestandsmärkte erzeugen'

    @property
    def Tool(self):
        return CreateTemplate

    def _getParameterInfo(self):

        # Projekt_auswählen
        param = self.add_parameter('projectname')
        param.name = encode(u'Projekt_auswählen')
        param.displayName = encode(u'Projekt')
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

        param = self.add_parameter('folder')
        param.name = encode(u'folder')
        param.displayName = encode(u'Zielordner')
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'DEFolder'

        param = self.add_parameter('show_help')
        param.name = encode(u'Hilfe')
        param.displayName = encode(u'Kurzanleitung zum Ausfüllen anzeigen')
        param.parameterType = 'Optional'
        param.direction = 'Input'
        param.datatype = u'GPBoolean'

        return self.par

    def _open(self, params):
        param = self.par.folder
        subfolder = 'input_templates'
        param.value = os.path.join(self.folders.get_projectpath(),
                                   subfolder)

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
    t._open(t.par)
    t.par.template_type.value = 'CSV-Datei'
    t.set_active_project()
    t.execute()
