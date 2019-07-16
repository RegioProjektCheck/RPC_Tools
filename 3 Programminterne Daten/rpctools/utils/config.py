# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# REGIOPROJEKTCHECK
# project_lib.py
#
# Description:
# PROJECT URL: http://www.regioprojektcheck.de
#
# Author:
# ILS gGmbH / HCU Hamburg / GGR Planung
#
# LICENSE: The MIT License (MIT) Copyright (c) 2014 RPC Consortium
# ---------------------------------------------------------------------------
from os import listdir
import sys
from os.path import join, isdir, abspath, dirname, basename, exists
from os import mkdir, getenv
import arcpy
import json
import _winreg

from rpctools.utils.singleton import Singleton
from rpctools.utils.encoding import encode


class Config(object):
    __metaclass__ = Singleton

    _default = {
        'active_project': u'',
        'epsg': 31467,
        'transformation': "DHDN_To_WGS_1984_5x",
        'max_area_distance': 1000,
        'google_api_key': ' AIzaSyDL32xzaNsQmB_fZGU9SF_FtnvJ4ZrwP8g',
        'project_folder': u''
    }

    _config = {}

    # write changed config instantly to file
    _write_instantly = True

    def __init__(self):

        self.config_file = join(self.APPDATA_PATH, 'projektcheck-config.txt')
        self._callbacks = {}
        self.active_coord = (0, 0)
        if exists(self.config_file):
            self.read()
            # add missing Parameters
            changed = False
            for k, v in self._default.iteritems():
                if k not in self._config:
                    self._config[k] = v
                    changed = True
            if changed:
                self.write()

        # write default config, if file doesn't exist yet
        else:
            self._config = self._default.copy()
            self.write()

    @property
    def APPDATA_PATH(self):
        path = join(getenv('LOCALAPPDATA'), 'Projekt-Check')
        if not exists(path):
            mkdir(path)
        return path

    def read(self, config_file=None):
        if config_file is None:
            config_file = self.config_file
        try:
            with open(config_file, 'r') as f:
                self._config = json.load(f)
        except:
            self._config = self._default.copy()
            print('Error while loading config. Using default values.')

    def write(self, config_file=None):
        if config_file is None:
            config_file = self.config_file

        with open(config_file, 'w') as f:
            config_copy = self._config.copy()
            # pretty print to file
            json.dump(config_copy, f, indent=4, separators=(',', ': '))

    # access stored config entries like fields
    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        elif name in self._config:
            return self._config[name]
        raise AttributeError

    def __setattr__(self, name, value):
        if name in self._config:
            self._config[name] = value
            if self._write_instantly:
                self.write()
            if name in self._callbacks:
                for callback in self._callbacks[name]:
                    callback(value)
        else:
            self.__dict__[name] = value
        #if name in self._callbacks:
            #for callback in self._callbacks[name]:
                #callback(value)

    def __repr__(self):
        return repr(self._config)

    def on_change(self, attribute, callback):
        if attribute not in self._callbacks:
            self._callbacks[attribute] = []
        self._callbacks[attribute].append(callback)

    def remove_listeners(attribute):
        if attribute in self._callbacks:
            self._callbacks.pop(attribute)


########################################################################
class Folders(object):
    """"""
    def __init__(self, params=None, projectname=None, workspace=None):
        """class that returns path"""
        try:
            self.BASE_PATH = _winreg.QueryValue(
                _winreg.HKEY_LOCAL_MACHINE, "Software\ProjektCheck PROFI")
            if not exists(self.BASE_PATH):
                self.BASE_PATH = _winreg.QueryValue(
                    _winreg.HKEY_LOCAL_MACHINE,
                    "Software\WOW6432Node\ProjektCheck PROFI")
            if not exists(self.BASE_PATH):
                raise WindowsError
        except WindowsError:
            self.BASE_PATH = abspath(join(dirname(__file__), '..', '..', '..'))

        self._INTERN = '3 Programminterne Daten'
        self._BASE_DBS = 'workspaces'
        self._TEMPORARY_GDB_PATH = 'temp_gdb'
        self._TEMPLATE_BASE_PATH = 'templates'
        self._TEMPLATE_FLAECHEN = 'projektflaechen_template.shp'
        self._PROJECT_TEMPLATE = 'Template'
        self._TEST_TEMPLATE = 'Test_Template'
        self._TEMPLATE_LAYERFOLDER = 'layers'
        self._TEMPLATE_DIAGRAMFOLDER = 'diagrams'
        self._TOCFOLDER = 'toc'
        self._TEST_TMP_PROJECT = '__unittest__'
        self._AUSGABE_PATH = 'Ergebnisausgabe'
        self._TEXTE = 'texte'
        self._MXDS = 'mxds'
        self._DEFINITION_PYT_PATH = '1 Planungsprojekte definieren'
        self._ANALYST_PYT_PATH = '2 Planungsprojekte analysieren'
        self._MANUALS_PATH = '0 Anleitung'
        # the params
        self._params = params
        self._projectname = projectname
        self._workspace = workspace
        self._invalid_paths = []
        self._CONFIG_FILE = 'projektcheck-config.txt'
        self._OTP_PICKLE_FILE = 'otpgraph.pickle'
        self._ZENSUS_FILE = r'ZensusGrid\Zensus2011GridWGS84_int.tif'
        self._ZENSUS_500_FILE = r'ZensusGrid\ZensusEinwohner500.tif'

    def join_and_check(self, *args, **kwargs):
        """
        Joins paths and checks if joined path points to existing resource
        (directory, database or table) if requested and stores the invalid
        paths

        Parameters
        ----------
        args: paths to join
        check : str, optional
            if True, checks if joined path points to existing resource
        Returns
        -------
        path : str
            the joined path
        """
        path = join(*args)
        check = kwargs.get('check', True)
        if check and not arcpy.Exists(path):
            self._invalid_paths.append(path)
        return path

    @property
    def projectname(self):
        """The project name"""
        projectname = self._projectname or self._params.get_projectname()
        return projectname

    @property
    def workspace(self):
        """The default database name"""
        workspace = self._workspace or self._params._workspace
        return workspace

    @property
    def INTERN(self):
        return self.join_and_check(self.BASE_PATH, self._INTERN)

    @property
    def BASE_DBS(self):
        return self.join_and_check(self.INTERN, self._BASE_DBS)

    @property
    def ZENSUS_RASTER_500_FILE(self):
        return self.join_and_check(self.BASE_DBS, self._ZENSUS_500_FILE)

    @property
    def ZENSUS_RASTER_FILE(self):
        return self.join_and_check(self.BASE_DBS, self._ZENSUS_FILE)

    @property
    def MXDS(self):
        return self.join_and_check(self.TEMPLATE_BASE_PATH, self._MXDS)

    @property
    def TEXTE(self):
        return self.join_and_check(self.INTERN, self._TEXTE)

    @property
    def PROJECT_BASE_PATH(self):
        config = Config()
        return config.project_folder

    @property
    def TEMPLATE_BASE_PATH(self):
        return self.join_and_check(self.BASE_PATH, self._INTERN,
                                   self._TEMPLATE_BASE_PATH)

    @property
    def TEMPORARY_GDB_PATH(self):
        path = join(self.PROJECT_BASE_PATH, self._TEMPORARY_GDB_PATH)
        if not exists(path):
            mkdir(path)
        return path

    @property
    def TEMPLATE_FLAECHEN(self):
        return self.join_and_check(self.TEMPLATE_BASE_PATH,
                                   self._TEMPLATE_FLAECHEN)

    @property
    def TEMPLATE_LAYERFOLDER(self):
        return self.join_and_check(self.TEMPLATE_BASE_PATH,
                                   self._TEMPLATE_LAYERFOLDER)

    @property
    def TEMPLATE_DIAGRAMFOLDER(self):
        return self.join_and_check(self.TEMPLATE_BASE_PATH,
                                   self._TEMPLATE_DIAGRAMFOLDER)

    @property
    def TOCFOLDER(self):
        return self.join_and_check(self.TEMPLATE_LAYERFOLDER, self._TOCFOLDER)

    @property
    def PROJECT_TEMPLATE(self):
        return self.join_and_check(self.TEMPLATE_BASE_PATH,
                                   self._PROJECT_TEMPLATE)

    @property
    def TEST_TEMPLATE(self):
        return self.join_and_check(self.TEMPLATE_BASE_PATH,
                                   self._TEST_TEMPLATE)

    @property
    def TEST_TMP_PROJECT(self):
        return self.join_and_check(self.PROJECT_BASE_PATH,
                                   self._TEST_TMP_PROJECT)

    @property
    def ANALYST_PYT_PATH(self):
        return self.join_and_check(self.BASE_PATH, self._ANALYST_PYT_PATH)

    @property
    def DEFINITION_PYT_PATH(self):
        return self.join_and_check(self.BASE_PATH, self._DEFINITION_PYT_PATH)

    @property
    def MANUALS_PATH(self):
        return self.join_and_check(self.BASE_PATH, self._MANUALS_PATH)

    def get_projects(self):
        '''
        returns all available projects inside the project folder
        (except the temp. projects which are not meant to be edited)
        '''
        base_path = self.PROJECT_BASE_PATH
        if not exists(self.PROJECT_BASE_PATH):
            return []
        project_folders = []
        for f in listdir(base_path):
            path = join(base_path, f)
            if isdir(path) and f != self._TEST_TMP_PROJECT:
                subfolders = listdir(path)
                # folder has to contain at least one template file-geodatabase
                # (starting with FGDB_)
                for s in subfolders:
                    if (s.startswith('FGDB_')):
                        project_folders.append(f)
                        break
        return sorted(project_folders)

    def get_temporary_projects(self):
        '''
        returns all projects for which temporary databases exist
        '''
        subfolders = [f for f in listdir(self.TEMPORARY_GDB_PATH)
                      if isdir(self.get_temporary_projectpath(f))]
        return sorted(subfolders)

    def get_projectpath(self, project=None, check=True):
        """
        The Path to the Project Folder

        Parameters
        ----------
        project : str
            the project name
        Returns
        -------
        projectpath : str
            the full path of the Project folder
        """
        projectname = project or self.projectname
        return self.join_and_check(self.PROJECT_BASE_PATH,
                                   projectname,
                                   check=check)

    def get_projectpath(self, project=None, check=True):
        """
        The Path to the Project Folder

        Parameters
        ----------
        project : str
            the project name
        Returns
        -------
        projectpath : str
            the full path of the Project folder
        """
        projectname = project or self.projectname
        return self.join_and_check(self.PROJECT_BASE_PATH,
                                   projectname,
                                   check=check)

    def get_otp_pickle_filename(self, project=None, check=True):
        return self.join_and_check(
            self.get_projectpath(project=project),
            self._OTP_PICKLE_FILE,
            check=check)

    def get_temporary_projectpath(self, project=None):
        projectname = project or self.projectname
        path = join(self.TEMPORARY_GDB_PATH, projectname)
        if not exists(path):
            mkdir(path)
        return path

    def get_temporary_db(self, project=None, workspace='', check=True):
        workspace = basename(workspace) or self.workspace
        return self.join_and_check(
            self.get_temporary_projectpath(project=project),
            workspace, check=check)

    def get_temporary_table(self, table_name, workspace='',
                            project=None, check=True):
        return self.join_and_check(
            self.get_temporary_db(workspace=workspace, project=project,
                                  check=True),
            table_name, check=check)

    @property
    def PROJECT_PATH(self):
        """The Projectpath"""
        return self.get_projectpath()

    @property
    def AUSGABE_PATH(self):
        """The Projectpath"""
        return self.join_and_check(self.PROJECT_PATH, self._AUSGABE_PATH)

    def get_db(self, workspace='', project=None, check=True):
        """
        A Workspace in the Project Folder

        Parameters
        ----------
        workspace : str, optional
            the name of the Workspace
        project : str, optional
            the project name

        Returns
        -------
        projectdb : str
            the full path of the Workspace
        """
        workspace = basename(workspace) or self.workspace
        projectname = project or self.projectname
        return self.join_and_check(self.get_projectpath(projectname), workspace,
                                   check=check)

    def get_table(self, tablename, workspace='', project='', check=True):
        """
        A Table in a Workspace in the Project Folder

        Parameters
        ----------
        tablename : str
        workspace : str, optional
            the name of the Workspace
        project : str, optional
            the project name

        Returns
        -------
        table : str
            the full path to a table in the Workspace
        """
        workspace = basename(workspace) or self.workspace
        projectname = project or self.projectname
        table = self.join_and_check(self.get_db(workspace, projectname),
                                    tablename,
                                    check=check)
        return table

    def get_basedb(self, workspace, check=True):
        """
        A Base Workspace

        Parameters
        ----------
        workspace : str
            the name of the Workspace

        Returns
        -------
        basedb : str
            the full path of the Workspace
        """
        return self.join_and_check(self.BASE_DBS, workspace, check=check)

    def get_base_table(self, workspace, table, check=True):
        """
        A Table in a Base Workspace

        Parameters
        ----------
        workspace : str
            the name of the Workspace
        tablename : str
            the name of the table
        check : bool
            if false, don't check if table exists

        Returns
        -------
        base_table : str
            the full path to the table in the Base Workspace
        """
        workspace = basename(workspace)
        table = self.join_and_check(self.get_basedb(workspace), table,
                                    check=check)
        return table

    def update_table(self, table, column_values, where=None, workspace='',
                     project='', check=True):
        """
        Update rows in a Workspace in the Project Folder

        Parameters
        ----------
        table : str
            the name of the table
        column_values: dict,
            the columns and the values to update them with as key/value-pairs
        where: str, optional
            a where clause to pick single rows
        workspace : str, optional
            the name of the Workspace
        project : str, optional
            the project name
        check : bool, optional
            if false, don't check if table exists
        """
        table = self.get_table(table, workspace=workspace, project=project, check=True)
        columns = column_values.keys()
        cursor = arcpy.da.UpdateCursor(table, columns, where_clause=where)
        for row in cursor:
            for i, column in enumerate(columns):
                row[i] = column_values[column]
            cursor.updateRow(row)
        del cursor

    def get_layer(self, layername, folder='', enhance = True):
        """
        A lyr-file

        Parameters
        ----------
        layername : str
            the name of the lyr-file

        folder : str, optional
            a subfolder

        enhance = boolean, optional
            True -> ".lyr" will be added to layername

        Returns
        -------
        layer : str
            the full path to the lyr-file
        """
        layername = encode(layername)
        if (enhance == True):
            layerfile = '{}.lyr'.format(layername)
        else:
            layerfile = layername

        layer = self.join_and_check(self.TEMPLATE_LAYERFOLDER, folder, layerfile)
        return layer

    def get_diagram_template(self, name, subfolder='', enhance=True):
        """
        Return a diagram from the templates

        Parameters
        ----------
        name : str
            the name of the diagram
        subfolder : str, optional
            a subfolder for a specific diagram
        enhance : bool, optional (Default=True)
            if true, add .grf as extension to the diagram name

        Returns
        -------
        path : str
            the full path to the diagram
        """
        filename = encode(name)
        if enhance:
            filename = '{}.grf'.format(filename)
        diagram_path = self.join_and_check(self.TEMPLATE_DIAGRAMFOLDER,
                                           subfolder,
                                           filename)
        return diagram_path

if __name__ == '__main__':
    c = Config()
    f = Folders(projectname=c.active_project)
    projects = f.get_projects()
    print(projects)
