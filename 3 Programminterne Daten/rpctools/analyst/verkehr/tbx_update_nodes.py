# -*- coding: utf-8 -*-
import os
import sys
import arcpy

from rpctools.utils.params import Tbx
from rpctools.utils.encoding import encode
from rpctools.analyst.verkehr.routing import Routing


class UpdateNodes(Routing):
    def run(self):
        toolbox = self.parent_tbx
        toolbox.dataframe_to_table('Zielpunkte', toolbox.df_transfer_nodes,
                                   ['node_id'])
        self.calculate_traffic_load()


class TbxUpdateNodes(Tbx):
    @property
    def label(self):
        return encode(u'Gewichtung der Herkunfts-/Zielpunkte')

    @property
    def Tool(self):
        return UpdateNodes

    def _open(self, params):
        self.df_transfer_nodes = self.table_to_dataframe(
            'Zielpunkte', columns=['node_id', 'weight', 'Name'])

        nodes = list(self.df_transfer_nodes['Name'].values)

        params.choose_node.filter.list = nodes

        if nodes:
            params.choose_node.value = nodes[0]
            weight = self.df_transfer_nodes['weight'].values[0]
            params.weight.value = weight

    def _getParameterInfo(self):
        params = self.par
        projekte = self.folders.get_projects()
        # Projekt_auswählen
        p = self.add_parameter('project')
        p.name = u'Projekt_auswählen'.encode('cp1252')
        p.displayName = u'Projekt'.encode('cp1252')
        p.parameterType = 'Required'
        p.direction = 'Input'
        p.datatype = u'GPString'

        p.filter.list = projekte
        if projekte:
            p.value = projekte[0]
        # Select Nodes
        p = self.add_parameter('choose_node')
        p.name = u'choose_node'.encode('cp1252')
        p.displayName = u'Herkunfts-/Zielpunkt auswählen'.encode('cp1252')
        p.parameterType = 'Required'
        p.direction = 'Input'
        p.datatype = u'GPString'
        # Set new value
        p = self.add_parameter('weight')
        p.name = u'weight'
        p.displayName = u'Neues Gewicht des ausgewählten Herkunfts-/Zielpunkts'
        p.parameterType = 'Required'
        p.direction = 'Input'
        p.datatype = 'GPLong'
        p.filter.type = 'Range'
        p.filter.list = [0, 100]

        # self.add_temporary_management()
        return params

    def _updateParameters(self, params):

        node_name = params.choose_node.value
        idx = self.df_transfer_nodes['Name'] == node_name
        if self.par.changed('choose_node'):
            weight = self.df_transfer_nodes.loc[idx, 'weight'].values[0]
            params.weight.value = int(weight)

        if self.par.changed('weight'):
            self.df_transfer_nodes.loc[idx, 'weight'] = params.weight.value

        return params

    def validate_inputs(self):
        table = self.query_table('RouteLinks')
        if len(table) == 0:
            msg = (u'Es existiert noch keine Berechnung der '
                   u'Straßenverkehrsbelastung! \nBitte schätzen Sie zuerst die '
                   u'Straßenverkehrsbelastung, bevor Sie die Verkehrsbelastung'
                   u' neu gewichten.')
            return False, msg
        return True, ''

if __name__ == "__main__":
    t = TbxUpdateNodes()
    t.getParameterInfo()
    t.set_active_project()
    t.open()
    t.execute()
