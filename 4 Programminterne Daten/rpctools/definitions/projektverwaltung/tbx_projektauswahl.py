# -*- coding: utf-8 -*-

import sys

import arcpy
import datetime
from rpctools.utils.params import Tbx
from rpctools.utils.encoding import encode
from rpctools.definitions.projektverwaltung.projektauswahl import \
     Projektauswahl
from rpctools.definitions.projektverwaltung.projektverwaltung \
     import Projektverwaltung


class Projektauswahl(Projektverwaltung):
    _param_projectname = 'active_project'
    _workspace = 'FGDB_Definition_Projekt.gdb'

    def run(self):
        self.parent_tbx.config.active_project = self.par.active_project.value
        self.output.define_projection()
        #self.add_diagramm()
        

class TbxProjektauswahl(Tbx):
    """Toolbox Projektauswahl"""

    @property
    def label(self):
        return u'aktives Projekt wählen'

    @property
    def Tool(self):
        return Projektauswahl

    def __init__(self):
        super(TbxProjektauswahl, self).__init__()
        self.update_projects = False

    def _getParameterInfo(self):
        params = self.par
        # Bestehendes_Projekt_auswählen
        p = self.add_parameter('active_project')
        p.name = encode('aktives Projekt')
        p.displayName = encode('aktives Projekt auswählen')
        p.parameterType = 'Required'
        p.direction = 'Input'
        p.datatype = 'GPString'
        active = self.config.active_project
        projects = self.folders.get_projects()
        params.active_project.filter.list = projects
        if active and active in projects:
            params.active_project.value = active
        return params

    def _updateParameters(self, params):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        #active = self.config.active_project
        #projects = self.folders.get_projects()
        #if active not in projects:
            #active = ''
        #params.active_project.filter.list = projects
        #params.active_project.value = active

        #if self.recently_opened:
            #params.active_project.filter.list = self.folders.get_projects()
            #if self.config.active_project:
                #params.active_project.value = self.config.active_project


if __name__ == '__main__':
    t = TbxProjektauswahl()
    params = t.getParameterInfo()
    t.par.active_project.value = t.config.active_project
    t.execute()

