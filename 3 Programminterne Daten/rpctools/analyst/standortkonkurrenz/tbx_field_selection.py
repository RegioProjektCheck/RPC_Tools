# -*- coding: utf-8 -*-
import arcpy
from rpctools.utils.params import Tbx, Tool


class TbxFieldSelection(Tbx):

    @property
    def label(self):
        return encode(u'Gemeinden auswählen')

    @property
    def Tool(self):
        return FieldSelectionTool

    def _getParameterInfo(self):

        params = self.par
        projekte = self.folders.get_projects()

        # Projekt_auswählen
        p = self.add_parameter('projectname')
        p.name = u'Projekt_auswählen'.encode('cp1252')
        p.displayName = u'Projekt'.encode('cp1252')
        p.parameterType = 'Required'
        p.direction = 'Input'
        p.datatype = u'GPString'

        return params


class FieldSelectionTool(Tool):
    _workspace = 'FGDB_Standortkonkurrenz_Supermaerkte.gdb'
    _table = "Zentren"
    def add_outputs(self):
        self.output.add_layer('standortkonkurrenz', 'Zentren_selected',
                             template_folder='Standortkonkurrenz',
                             featureclass=self._table,
                             workspace=self._workspace,
                             name='Ausgewählte Gemeinden/Verw.Gemeinschaften '
                             'im Betrachtungsraum',
                             subgroup='Betrachtungsraum')
        self.output.add_layer('standortkonkurrenz', 'Zentren_background',
                             template_folder='Standortkonkurrenz',
                             featureclass=self._table,
                             workspace=self._workspace,
                             name='Nicht ausgewählte Gemeinden/'
                             'Verw.Gemeinschaften',
                             subgroup='Betrachtungsraum',
                             zoom=True)

    def run(self):
        pass
