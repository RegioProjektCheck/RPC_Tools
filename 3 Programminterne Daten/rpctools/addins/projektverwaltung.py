# -*- coding: utf-8 -*-

from rpctools.addins.common import ToolboxButton, folders, config
from rpctools.addins.outputs import ProjektAnzeigen
import pythonaddins
from os.path import exists

__all__ = ['ProjektAnlegen', 'ProjektAuswahl',
           'ProjektKopieren', 'ProjektLoeschen',
           'RefreshLayers', 'ProjektOrdner']

class ProjektOrdner(ToolboxButton):
    """Implementation for rpc_tools.neues_projekt (Button)"""
    _path = folders.DEFINITION_PYT_PATH
    _pyt_file = 'Projektverwaltung.pyt'
    _toolbox_name = 'TbxProjectFolder'


class ProjektAnlegen(ToolboxButton):
    """Implementation for rpc_tools.neues_projekt (Button)"""
    _path = folders.DEFINITION_PYT_PATH
    _pyt_file = 'Projektverwaltung.pyt'
    _toolbox_name = 'TbxProjektAnlegen'


class ProjektAuswahl(ProjektAnzeigen):
    _path = folders.DEFINITION_PYT_PATH
    _pyt_file = 'Projektverwaltung.pyt'
    _toolbox_name = 'TbxProjektauswahl'
    """Implementation for rpc_tools.projekt_auswahl (ComboBox)"""
    def __init__(self):
        super(ProjektAuswahl, self).__init__()
        self.editable = True
        self.enabled = True
        self.dropdownWidth = 'WWWWWWWWWWWWWWWWWWWWWWW'
        self.width = 'WWWWWWWWWWWWWWWW'
        # connect the change of the active project to a refresh of the project-
        # list (esp. to auto. select the active project)
        config.on_change('active_project', lambda active: self.refresh())
        self.refresh()

    def onSelChange(self, selection):
        if selection != config.active_project:
            self.activate_project(project=selection)
        self.value = selection

    def activate_project(self, project=None):
        if project is None:
            project = self.value
        config.active_project = project
        try:
            self.show()
        except IOError:
            msg = (u'Das Projekt ist fehlerhaft aufgrund fehlender Daten.\n'
                   u'Bitte löschen Sie es bei Gelegenheit!')
            pythonaddins.MessageBox(msg, 'Fehler', 0)
            config.active_project = self.value = ''
    
    def onFocus(self, focused):
        if focused:
            # doesn't work, arcpy get's stuck in focus when showing messagebox
            #folder = config.project_folder
            #err = ''
            #if not folder:
                #err = (u'Es wurde noch kein Speicherort für die Projekte definiert.')
            #elif not exists(folder):
                #err = (u'Der angegebene Speicherort für die Projekte existiert nicht.')
            #print folder
            #print(err)
            #if err:
                #err += (u'\nBitte geben Sie im Menü Verwalten '
                        #u'einen validen Speicherort an')
                #pythonaddins.MessageBox(err, 'Fehler', 0)
            #else:
            self.refresh()

    def refresh(self):
        """refresh the list of available projects and select the active one"""
        projects = folders.get_projects()
        self.items = sorted(projects)
        active = config.active_project
        if active not in projects:
            active = ''
        self.value = active


class ProjektKopieren(ToolboxButton):
    """Implementation for rpc_tools.projekt_kopieren (Button)"""
    _path = folders.DEFINITION_PYT_PATH
    _pyt_file = 'Projektverwaltung.pyt'
    _toolbox_name = 'TbxProjektKopieren'


class ProjektLoeschen(ToolboxButton):
    """Implementation for rpc_tools.projekt_loeschen (Button)"""
    _path = folders.DEFINITION_PYT_PATH
    _pyt_file = 'Projektverwaltung.pyt'
    _toolbox_name = 'TbxProjekteLoeschen'


class RefreshLayers(ProjektAnzeigen):
    ''''''