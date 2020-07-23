# -*- coding: utf-8 -*-
import os
import sys
import arcpy

from rpctools.utils.params import Tbx
from rpctools.utils.encoding import encode

from rpctools.analyst.verkehr.UpdateNodes import UpdateNodes


class TbxUpdateNodes(Tbx):
    _opened_for_first_time = True
    @property
    def label(self):
        return encode(u'Gewichtung der Herkunfts-/Zielpunkte')

    @property
    def Tool(self):
        return UpdateNodes


    def _open(self, params):
        nodes = self.query_table('Zielpunkte', ['Name'])
        nodes = [tup[0] for tup in nodes]

        params.choose_node.filter.list = nodes
        if nodes:
            params.choose_node.value = nodes[0]

        weight = self.query_table('Zielpunkte',
                                  ['weight'],
                                  where="Name = '{}'".format(
                                      params.choose_node.value))[0]
        params.new_weight.value = 0
        return

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
        p = self.add_parameter('new_weight')
        p.name = u'new_weight'
        p.displayName = u'Neues Gewicht des ausgewählten Herkunfts-/Zielpunkts'
        p.parameterType = 'Required'
        p.direction = 'Input'
        p.datatype = 'GPLong'
        p.filter.type = 'Range'
        p.filter.list = [0, 100]

        # self.add_temporary_management()
        return params


    def _updateParameters(self, params):

        where="Name = '{}'".format(params.choose_node.value)
        if self.par.changed('choose_node'):
            man_weight =  self.query_table('Zielpunkte',
                                ['Manuelle_Gewichtung'],
                                where=where)[0][0]
            if man_weight:
                params.new_weight.value = int(man_weight)
            else:
                old_weight = self.query_table('Zielpunkte',
                                              ['Gewicht'],
                                              where=where)[0][0]
                params.new_weight.value = int(round(old_weight, 0))


        if self.par.changed('new_weight') and not self._opened_for_first_time:
            man_weight = params.new_weight.value
            self.update_table('Zielpunkte',
                              {'Manuelle_Gewichtung': man_weight}, where=where)

        self._opened_for_first_time = False
        return

    def validate_inputs(self):
        pickle_path = self.folders.get_otp_pickle_filename(check=False)
        if not os.path.exists(pickle_path):
            msg = (u'Es existiert noch keine Berechnung der '
                   u'Straßenverkehrsbelastung! \nBitte schätzen Sie zuerst die '
                   u'Straßenverkehrsbelastung, bevor Sie die Verkehrsbelastung'
                   u' neu gewichten.')
            return False, msg
        return True, ''


if __name__ == "__main__":
    t = TbxUpdateNodes()
    t.getParameterInfo()
    print(t.par.get_projectname())
    t.execute()

    print 'done'
