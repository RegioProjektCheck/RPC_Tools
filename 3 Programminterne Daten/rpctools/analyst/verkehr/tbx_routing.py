# -*- coding: utf-8 -*-
import os
import sys
import arcpy
import numpy as np

from rpctools.utils.params import Tbx
from rpctools.utils.encoding import encode

from rpctools.analyst.verkehr.routing import Routing


class TbxRouting(Tbx):

    @property
    def label(self):
        return encode(u'Straßenverkehrsbelastung schätzen')

    @property
    def Tool(self):
        return Routing

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

        # inner radius
        p = self.add_parameter('inner')
        p.name = u'inner_circle'
        p.displayName = u'Entfernung der Herkunfts-/Zielpunkte vom ' +\
            u'Mittelpunkt des Plangebiets (in Metern Straßenentfernung)'
        p.parameterType = 'Required'
        p.direction = 'Input'
        p.datatype = 'GPLong'
        p.filter.type = 'Range'
        p.filter.list = [1000, 3000]
        p.value = 1500

        return params

    def validate_inputs(self):
        source_table = 'Anbindungspunkte'
        source_ws = 'FGDB_Verkehr.gdb'
        table = self.query_table(source_table, columns=['Shape'],
                                 workspace=source_ws)
        max_dist = self.config.max_area_distance
        xy = [r[0] for r in table]
        distances = []
        for i in range(len(xy)):
            for j in range(i):
                dist = np.linalg.norm(np.subtract(xy[i], xy[j]))
                distances.append(dist)
        if max(distances) > max_dist:
            msg = (u'Der Abstand zwischen den Anbindungspunkten ist zu groß. '
                   u'Er darf für die Schätzung der Verkehrsbelastung jeweils '
                   u'nicht größer als {} m sein!'
                   .format(max_dist))
            return False, msg
        return True, ''

    def _updateParameters(self, params):
        return


if __name__ == "__main__":
    t = TbxRouting()
    t.getParameterInfo()
    t.par.project.value = t.config.active_project
    t.execute()

    print 'done'
