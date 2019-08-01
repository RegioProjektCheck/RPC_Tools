# -*- coding: utf-8 -*-

import gc
import sys
import os
from abc import ABCMeta, abstractmethod, abstractproperty
from rpctools.utils.config import Folders
from rpctools.utils.config import Config
from rpctools.utils.output import ArcpyEnv
from rpctools.utils.message import Message
from rpctools.utils.singleton import Singleton
from rpctools.utils.param_module import Params
from rpctools.utils.arcpy_parameter import Parameter
from rpctools.utils.output import Output
import pandas as pd
import numpy as np
import arcpy
import gc


class ToolFolders(Folders):
    def join_and_check(self, *args, **kwargs):
        """
        Joins paths and checks if joined path points to existing resource
        (directory, database or table) if requested

        overrides check function to show path errors while running and exit
        when first error occurs

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
        path = os.path.join(*args)
        check = kwargs.get('check', True)
        if check and not arcpy.Exists(path):
            arcpy.AddError(
                'Pfad oder Tabelle existiert nicht: "{}"'.format(path))
            sys.exit()
        return path


class Tool(object):
    """
    Base Class for a ArcGIS Tool

    Attributes
    ----------
    folders : Folders object
        gives access to relative paths

    mes : Message object
        for sending messages to ArcGIS
    """
    __metaclass__ = ABCMeta

    _param_projectname = 'projectname'
    """The parameter that holds the projectname"""
    _workspace = None
    """the name of the default database of the tool"""

    def __init__(self, params=None, parent_tbx=None, projectname=None):
        """
        Parameters
        ----------
        params : Params object
        parent_tbx: Tbx object, the toolbox the Tool belongs to
                    (=the calling toolbox)
        """
        self.par = params if params is not None else Params()
        self.mes = Message()
        self.folders = ToolFolders(params=self.par)

        if projectname:
            self.folders._projectname = projectname
        self.folders._workspace = self._workspace
        self.output = Output(params)

        # create a dummy toolbox, so that a tool may be able to function
        # without a 'real' one
        if not parent_tbx:
            parent_tbx = DummyTbx()
            parent_tbx.tool = self
            parent_tbx.folders = Folders(projectname=self.folders._projectname,
                                         workspace=self._workspace)

        self.parent_tbx = parent_tbx

    def main(self, par, parameters=None, messages=None):
        """
        The main method

        Parameters
        ----------
        par : the Params-object

        parameters : the list of parameters sent by ArcGIS

        messages : the messages-object sent by ArcGIS
        """
        self.par = par
        if parameters:
            self.par._update_parameters(parameters)
        if messages:
            self.mes = messages
        gc.collect()
        # Set the progressor
        arcpy.SetProgressor("step",
                            "Executing Tool {}...".format(self.__class__),
                            0, 100, 1)
        self.run()
        arcpy.ResetProgressor()

    @property
    def db(self):
        """ The full path to the default Database of the tool"""
        return self.folders.get_db()

    @property
    def projectname(self):
        """Return the current projectname"""
        return self.par.get_projectname()

    @abstractmethod
    def add_outputs(self):
        """method defining layers, diagrams, etc. as a result of the
        calculations of the toolbox and adding them to outputs
        - has to be implemented in the subclass"""

    @abstractmethod
    def run(self):
        """The run method - has to be implemented in the subclass"""


class Dependency(object):
    """Class for defining dependencies between multiple paramaters and updating
    their values according to the defined target"""
    def __init__(self, param_names, target_value, type='sum'):
        """
        Parameters
        ----------
        param_names : list of str
                names of the parameters depending on each other
        target_value : the targeted value
        type : str, optional
               the type of the dependency
               'sum' - sum parameter values up to given target_value
                      (adding/subtracting from bottom to top)
               'distributed_sum' - same as 'sum' but adding/subtracting weighted
                    from all other parameters at the same time
        """

        self.param_names = param_names
        self.target_value = target_value
        self.type = type

    def update(self, params):
        """
        check if dependent params were altered and set them to target value

        Parameters
        ----------
        params : Param object
        """
        if self.type == 'sum':
            self._set_sum(params)
        elif self.type == 'distributed_sum':
            self._set_distributed_sum(params)

    def _set_sum(self, params):
        """set values of dependent parameters to sum up to target value"""
        actual_sum = 0
        altered = False
        for name in self.param_names:
            param = params[name]
            altered = altered or param.altered
            actual_sum += param.value

        if not altered:
            return

        if actual_sum != self.target_value:
            difference = self.target_value - actual_sum
            for name in reversed(self.param_names):
                param = params[name]
                old_val = param.value
                new_val = param.value + difference
                if new_val < 0:
                    new_val = 0
                elif new_val > self.target_value:
                    new_val = self.target_value
                difference = difference + old_val - new_val
                param.value = new_val

    def _set_distributed_sum(self, params):
        """set values of dependent parameters to sum up to target value;
        ToDo: needs to be fixed
        """
        actual_sum = 0
        altered_param = None

        values = []
        for name in self.param_names:
            param = params[name]
            # get values, mark an altered parameter with NaN
            value = np.nan if params.changed(name) else param.value
            values.append(value)
            actual_sum += param.value

        # continue only if ONE parameter is changed
        if np.isnan(values).sum() != 1:
            return

        # anteil an differenz
        difference = self.target_value - actual_sum
        if not difference:
            return
        if difference > 0:
            values = 100 - np.array(values)
        nansum = np.nansum(values)
        # subtract weighted difference
        res = values / nansum * (nansum - abs(difference))
        res = res.round()
        # add/subtract rounding errors to/from highest value
        rdiff = nansum - abs(difference) - np.nansum(res)
        res[np.nanargmax(res)] -= rdiff
        if difference > 0:
            res = 100 - np.array(res)

        for i, name in enumerate(self.param_names):
            new_val = res[i]
            if np.isnan(new_val):
                continue
            param = params[name]
            param.value = int(new_val)


class Tbx(object):
    """Base Class for a ArcGIS Toolbox"""
    __metaclass__ = ABCMeta
    __metaclass__ = Singleton

    _temp_table_prefix = 'RPC_Tools'
    # name of temp. tables, project needs to be appended
    _temp_table_name = (
        _temp_table_prefix +
        '_{class_name}_{source_db}_{source_table}_'
    )

    config = Config()

    @abstractproperty
    def Tool(self):
        """
        Returns the Toolclass

        To be defined in the subclass
        """

    @abstractproperty
    def label(self):
        """
        Returns the label as string

        To be defined in the subclass
        """

    @property
    def projects_changed(self):
        """projects that were changed (only works if toolbox works with
        temporary databases)"""
        return self.folders.get_temporary_projects()

    @property
    def output(self):
        return self.tool.output

    def show_outputs(self, show_layers=True, show_diagrams=True, redraw=True):
        '''
        show the outputs of the tool (as defined in add_outputs() of Tool)

        Parameters
        ----------
        show_layers : bool, default: True
                show the defined layers
        show_diagrams : bool, default: True
                show the defined diagrams
        redraw : bool, default: True
                if False don't add the layers if they are already in TOC
        Returns
        -------
        parameter : arcpy.Parameter-instance

        '''
        self.output.clear()
        self.tool.add_outputs()
        if show_layers:
            self.output.show_layers(redraw=redraw)
        if show_diagrams:
            self.output.show_diagrams()
        self.output.show_images()

    def __init__(self):

        Tool = self.Tool

        # the parameters
        self.par = Params(param_projectname=Tool._param_projectname,
                          workspace=Tool._workspace)
        # define the folders
        self.folders = Folders(params=self.par)
        self.projects = []
        # an instance of the tool
        self.tool = Tool(self.par, self)
        self.canRunInBackground = False
        # update projects on call of updateParameters
        self.requires_existing_project = True
        self.requires_existing_project_path = True
        self._dependencies = []
        # updates to these tables are written to temp. tables and written to
        # project db only on execution of tool
        self._temporary_gdbs = []
        self._is_executing = False

    @abstractmethod
    def _getParameterInfo(self):
        """
        Define the Parameters and return a list or Params()-instance with the
        parameter
        """

    def add_parameter(self, param_name):
        """
        Add a (patched) arcpy-parameter and return this parameter

        Parameters
        ----------
        param_name : str

        Returns
        -------
        parameter : arcpy.Parameter-instance
        """
        parameter = self.par[param_name] = Parameter()
        return parameter

    def remove_parameter(self, param_name):
        """
        Remove a (patched) arcpy-parameter from toolbox

        Parameters
        ----------
        param_name : str
        """
        del self.par[param_name]

    def getParameterInfo(self):
        """
        Define the Parameters and return a list or Params()-instance with the
        parameter
        """
        self.folders._invalid_paths = []
        params = self._getParameterInfo()._od.values()
        return params

    def isLicensed(self):
        """If toolbox is licenced"""
        return True

    def updateParameters(self, parameters):
        """
        The updateParameters-method called by ArcGIS

        Parameters
        ----------
        parameters : list of ArcGIS-Parameters
        """

        self.par._update_parameters(parameters)

        if self.par.toolbox_opened():
            self.open()
        # updating projects messes up the initial project management
        if self.requires_existing_project:
            self._update_project_list()
        self._update_dependencies(self.par)
            #self._create_temporary_copies()
        # check for invalid manual entries in dropdowns
        #for param in self.par:
            #if (param.datatype == 'Zeichenfolge' and param.filter.list and
                #not param.multiValue and
                #param.altered and param.value not in param.filter.list):
                #return
        self._updateParameters(self.par)

    def open(self):
        """
        called on open of toolbox (custom function, no ArcGIS method)
        """
        # if a toolbox is opened, remove ALL temporary databases
        self.clear_temporary_dbs()
        # reset the invalid paths
        self.folders._invalid_paths = []
        # set the active project on open (do not do this in project management
        # toolboxes, updating projects messes them up, that's what the boolean
        # self.update_projects is for)
        if  (not self.requires_existing_project_path or
            (self.requires_existing_project and
            self.par._get_param_project() is not None)):
            self.set_active_project()
            # don't call _open of subclass if there is only one parameter
            if len(self.par) > 1:
                self._open(self.par)

    def set_active_project(self, projectname=None):
        project_param = self.par._param_projectname
        if not project_param or not self.par._od.has_key(project_param):
            return
        active_project = projectname or self.config.active_project
        projects = self.folders.get_projects()
        # fix active project if it was set to test project by a tool
        # (may happen while testing)
        is_tmp_project = active_project == self.folders._TEST_TMP_PROJECT
        if is_tmp_project or active_project not in projects:
            active_project = self.config.active_project = ''
        project_param = self.par[project_param]
        project_param.filter.list = []
        project_param.value = active_project
        project_param.enabled = False

    def validate_active_project(self):
        if not self.requires_existing_project:
            return True, ''
        active_project = self.config.active_project
        projects = self.folders.get_projects()
        if not active_project:
            return False, (u'Es ist kein aktives Projekt ausgewählt!')
        elif active_project not in projects:
            return False, (u'Das aktive Projekt kann nicht gefunden werden!')
        return True, ''

    def validate_project_folder(self):
        if not self.requires_existing_project_path:
            return True, ''
        project_folder = self.config.project_folder
        msg = (u'\nBitte geben Sie im Menü Verwalten einen '
               u'validen Speicherort an.')
        if not project_folder:
            return False, (u'Es ist kein Speicherort für Ihre Projekte definiert!')
        elif not os.path.exists(project_folder):
            return False, (u'Der angegebene Speicherort für Ihre Projekte '
                           u'existiert nicht (mehr)!')
        return True, ''

    def _update_project_list(self):
        """
        Update the parameter list of existing projects
        """
        if self.par._param_projectname not in self.par:
            return
        projects = self.folders.get_projects()
        project_param = self.par[self.par._param_projectname]
        if projects == project_param.filter.list:
            return
        project_param.filter.list = projects
        if len(projects) == 0:
            project_param.value = ''
        # if previously selected project was deleted in the meantime
        elif project_param.value not in projects:
            project_param.value = projects[0]

    def _check_project(self):
        pass

    def add_dependency(self, param_names, target_value, type='sum'):
        """
        define a dependency between different parameters, they have to sum up
        to a target value.
        if one of them is changed, the others will be auto set while updating
        the parameters

        Parameters
        ----------
        param_names : list,
               qualified names of the parameters

        target_value : int
               the target value the parameters sum up to

        type : str, optional
               'sum' - sum parameter values up to given target_value
                      (adding/subtracting from bottom to top)
               'distributed_sum' - same as 'sum' but adding/subtracting weighted
                    from all other parameters at the same time (not fully
                    functional atm, needs to be fixed)
        """
        dependency = Dependency(param_names, target_value, type=type)
        self._dependencies.append(dependency)

    def _update_dependencies(self, params):
        """check if dependent params were altered and set them to target sum"""
        for dependency in self._dependencies:
            dependency.update(params)

    def _open(self, params):
        """
        do something, if toolbox was recently opened (only works, if toolbox
        owns more than one parameter)

        To define in the subclass
        """

    def _updateParameters(self, params):
        """
        Update the Parameters if something changed

        To define in the subclass
        """

    def updateMessages(self, parameters):
        """
        The updateMessages-method called by ArcGIS

        Parameters
        ----------
        parameters : list of ArcGIS-Parameters
        """
        self.par._update_parameters(parameters)
        params = self.par._od.values()
        if self.requires_existing_project_path:
            valid, message = self.validate_project_folder()
            if not valid:
                params[0].setErrorMessage(message)
                return
        if self.requires_existing_project:
            valid, message = self.validate_active_project()
            if not valid:
                params[0].setErrorMessage(message)
                return
        # check if toolbox contains invalid paths, add errors to first param.
        if params and self.folders._invalid_paths:
            invalid = ', '.join(self.folders._invalid_paths)
            params[0].setErrorMessage(
                u'Es fehlen für die Berechnungen benötigte Daten. '
                u'Möglicherweise wurden vorausgesetzte Schritte noch '
                u'nicht korrekt durchgeführt.\n\r '
                u'Folgende Pfade oder Tabellen wurden nicht gefunden: {}'
                .format(invalid))

        # check for invalid manual entries in dropdowns
        #for param in self.par:
            #if (param.datatype == 'Zeichenfolge' and param.filter.list and
                #not param.multiValue and
                #param.altered and param.value not in param.filter.list):
                #param.setErrorMessage(
                    #u'Bitte ändern Sie nicht manuell Einträge in den '
                    #u'Dropdown-Menüs! Für eventuelle Umbenennungen sind in der '
                    #u'Regel eigene Eingabefelder vorgesehen.')
                #return
        self._updateMessages(self.par)

    def validate_inputs(self):
        """
        to be implemented in derived toolbox
        """
        return True, ''

    def _updateMessages(self, parameters):
        """ to define in the subclass """

    def update_table(self,
                     table_name,
                     column_values,
                     where=None,
                     pkey=None,
                     workspace=''):
        """
        Update rows of a table in a Workspace in the Project Folder

        Parameters
        ----------
        table_name : str
            name of the table
        column_values: dict,
            the columns and the values to update them with as key/value-pairs
        where: str, optional
            a where clause to pick single rows
        pkey: dict, optional
            the columns and the values of the primary key as key/value-pairs
        workspace : str, optional
            the database name

        Returns
        -------
        r : int
            the number of updated rows, -1 if table does not exist
        """
        table_path = self._get_table_path(table_name, workspace=workspace)
        return self._update_table(table_path, column_values, where=where,
                                  pkey=pkey)

    def _update_table(self,
                     table_path,
                     column_values,
                     where=None,
                     pkey=None):
        """
        Update rows of a table

        Parameters
        ----------
        table_path : str
            full path to the table
        column_values: dict,
            the columns and the values to update them with as key/value-pairs
        where: str, optional
            a where clause to pick single rows
        pkey: dict, optional
            the columns and the values of the primary key as key/value-pairs

        Returns
        -------
        r : int
            the number of updated rows, -1 if table does not exist
        """
        where = where or self.get_where_clause(pkey)
        if not table_path:
            return -1
        columns = column_values.keys()
        cursor = arcpy.da.UpdateCursor(table_path, columns, where_clause=where)
        r = 0
        for row in cursor:
            for i, column in enumerate(columns):
                row[i] = column_values[column]
            cursor.updateRow(row)
            r += 1
        del cursor
        return r

    def copy_column(self, table, in_column, out_column, workspace=''):
        """
        copy all values of a column to another column in the same
        FileGeodatabase (create column if not exists, overwrite else)

        Parameters
        ----------
        table : str
            table name
        in_column : str
            name of the column to copy
        out_column : str
            name of the column to copy to
        workspace : str, optional
            the database name
        """
        table_path = self._get_table_path(table, workspace=workspace)
        if not table_path:
            return
        in_field = arcpy.ListFields(table_path, in_column)
        if not in_field:
            raise Exception('Column {} does not exist in {}'.format(in_column))
        out_field = arcpy.ListFields(table_path, out_column)
        if not out_field:
            arcpy.AddField_management(table_path, out_column, in_field[0].type)
        cursor = arcpy.da.UpdateCursor(table_path, [in_column, out_column])
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)
        del cursor


    def delete_rows_in_table(self,
                             table,
                             where=None,
                             pkey=None,
                             workspace='',
                             ):
        """
        Delete rows in project table which match the where-clause or the
        primary key (if no pkey or where clause are given, all rows will be
        deleted!)

        Parameters
        ----------
        table : str
             name of the table
        pkey: dict, optional
            the columns and the values of the primary key as key/value-pairs
        where: str, optional
            a where clause to delete specific rows
        workspace : str, optional
            the database name

        Returns
        -------
        r : int
            the number of deleted rows
        """
        gc.collect()
        table_path = self._get_table_path(table, workspace=workspace)
        if not table_path:
            return 0
        return self._delete_rows_in_table(table_path, where=where, pkey=pkey)

    def _delete_rows_in_table(self, table_path, where=None, pkey=None):
        """
        Delete rows in a FileGeodatabase which match the where-clause or the
        primary key (if no pkey or where clause are given, all rows will be
        deleted!)

        Parameters
        ----------
        table_path : str
            full path to the table
        pkey: dict, optional
            the columns and the values of the primary key as key/value-pairs
        where: str, optional
            a where clause to delete specific rows

        Returns
        -------
        r : int
            the number of deleted rows
        """

        where = where or self.get_where_clause(pkey)
        columns = pkey.keys() if pkey else '*'
        cursor = arcpy.da.UpdateCursor(table_path, columns, where_clause=where)
        r = 0
        for row in cursor:
            cursor.deleteRow()
            r += 1
        del cursor
        return r

    def _get_table_path(self, table_name, workspace=''):
        """
        return the full table path,
        return the temporary fgdb, if db is handled temporarly (creates the
        temporary table if it does not exist yet),
        return None if table does not exist
        """
        workspace = os.path.basename(workspace) or self.tool._workspace
        table_name = os.path.basename(table_name)
        # if table is in temp. management -> write to temporary table instead
        # don't do this while executing toolbox, temp. management is meant for
        # undoing user inputs in toolboxes
        if not self._is_executing and workspace in self._temporary_gdbs:
            temp_db = self.folders.get_temporary_db(workspace=workspace,
                                                    check=False)
            # create on demand
            if not arcpy.Exists(temp_db):
                self._create_temporary_copy(workspace)
            table_path = self.folders.get_temporary_table(table_name,
                                                          workspace=workspace)
        else:
            table_path = self.folders.get_table(table_name, workspace=workspace)

        #if not arcpy.Exists(table_path):
            #table_path = None
        return table_path

    def insert_rows_in_table(self, table_name, column_values, workspace=''):
        """
        insert new row into a table in a Workspace in the Project Folder

        Parameters
        ----------
        table_name : str
            name of the table
        column_values: dict,
            the columns and the values to insert as key/value-pairs
        workspace : str, optional
            the database name
        """
        table_path = self._get_table_path(table_name, workspace=workspace)
        if not table_path:
            return
        columns = column_values.keys()
        values = column_values.values()
        try:
            # transpose list of values
            rows = zip(*values)
        except:
            rows = [values]

        self._insert_rows_in_table(table_path, columns, rows)

    def _insert_rows_in_table(self, table_path, columns, rows):
        """
        insert rows into a table

        Parameters
        ----------
        table_path : str
            full path to the table
        columns: list of str,
            the columns
        rows: list of lists,
            the rows to insert as key/value-pairs
        """
        cursor = arcpy.da.InsertCursor(table_path, columns)
        for row in rows:
            cursor.insertRow(row)
        del cursor

    def upsert_row_in_table(self, table_name, column_values, pkey, workspace=''):
        """
        update a row, or - if it does not exist yet - insert the row
        into a table in a Workspace in the Project Folder

        Parameters
        ----------
        table_name : str
            name of the table
        column_values: dict,
            the columns and the values to insert as key/value-pairs
        pkey: dict,
            the columns and the values of the primary key as key/value-pairs
        workspace : str, optional
            the database name
        """
        where_clause = self.get_where_clause(pkey)
        # try to update the row
        r = self.update_table(table_name, column_values, where=where_clause,
                              workspace=workspace)
        if r < 0:
            return
        # if there are no rows matching the primary key
        if not r:
            # insert new row
            column_values.update(pkey)
            self.insert_rows_in_table(table_name, column_values, workspace)

    def get_where_clause(self, pkey):
        """
        convert a primary key dict to a where_clause

        Parameters
        ----------
        pkey : dict
            key-value-Pairs of columns and values

        Returns
        -------
        where_clause : str
        """
        if pkey is None:
            return None
        where_clause = ' AND '.join(["{} = {}".format(k, v)
                                     if not isinstance(v, (str, unicode))
                                     else "{} = '{}'".format(k, v)
                                     for (k, v) in pkey.iteritems()
                                     ])
        return where_clause

    def table_to_dataframe(self, table_name, columns=[], workspace='',
                           where=None, pkey=None, project='',
                           is_base_table=False):
        """
        get rows from a FileGeodatabase as a pandas dataframe,
        defaults to a Workspace in the Project Folder, if base table is
        requested workspace is required

        Parameters
        ----------
        table_name : str
            name of the table
        columns: list, optional
            the requested columns, if not given or empty: return all columns
        where: str, optional
            a where clause to pick single rows
        pkey: dict, optional
        workspace : str, optional
            the database name
        project : str, optional
            the project (set project is taken if not given)
        is_base_table : bool, optional, default = False
            if True a base table is queried, else a project table

        Returns
        -------
        rows : dataframe
            pandas dataframe with all requested rows and columns
        """
        # getting the fields is duplicate to the code in query_tables(...)
        # but the dataframe needs the column names as well and query_tables
        # should not return those
        if is_base_table:
            table_path = self.folders.get_base_table(workspace, table_name)
        else:
            table_path = self.folders.get_table(table_name, workspace=workspace,
                                                project=project)
        if not columns and arcpy.Exists(table_path):
            columns = [f.name for f in arcpy.ListFields(table_path)]

        rows = self.query_table(table_name, columns=columns,
                                workspace=workspace, where=where, pkey=pkey,
                                project=project, is_base_table=is_base_table)

        dataframe = pd.DataFrame.from_records(rows, columns=columns)
        # there is some strange issue with naming the geometry column
        # sometimes ArcGIS decides to name it Shape instead of SHAPE
        if 'Shape' in dataframe.columns:
            dataframe.rename(columns={"Shape": "SHAPE"}, inplace=True)
        return dataframe


    def dataframe_to_table(self, table_name, dataframe, pkeys, workspace='',
                           upsert=False, is_base_table=False):
        """
        Update a table in a Workspace in the Project Folder with values inside a
        pandas dataframe, all columns inside the dataframe will be written to
        the table (for this purpose all columns in the dataframe have to have a
        matching column in the table).
        Supports optional upserting (insert if not exists)

        Parameters
        ----------
        table_name : str
            name of the table
        dataframe: DataFrame,
            the dataframe to upload
        pkeys: list of str
            the names of the primary keys
        workspace : str, optional
            the database name
        upsert : bool, optional, default = False
            if True insert rows that do not exist yet, else ignored

        Examples
        --------
        dataframe = pd.DataFrame([[1, 1.4], [2, 2.0]],
                                 columns=['OBJECTID', 'Korrekturfaktor_EW'])
        dataframe_to_table('Wohnen_WE_in_Gebaeudetypen',
                           dataframe, ['OBJECTID'], upsert=False)
        """
        table_name = os.path.basename(table_name)
        if is_base_table:
            table_path = self.folders.get_base_table(workspace, table_name)
        else:
            table_path = self._get_table_path(table_name, workspace=workspace)
        columns_incl_pkeys = dataframe.columns.values
        desc = arcpy.Describe(table_path)
        fields = [field.name for field in desc.fields]

        # intersection of fields between dataframe and available fields
        # (prevent writing columns of df that don't exist in db)
        columns_incl_pkeys = np.intersect1d(columns_incl_pkeys, fields)

        # columns without the pkeys
        columns = np.setdiff1d(columns_incl_pkeys, pkeys)

        for row in dataframe.iterrows():
            # row is a tuple with index at 0 and the columns at 1
            pkey_values = dict(zip(pkeys, row[1][pkeys].values))
            values = row[1][columns].values
            column_values = dict(zip(columns, values))
            where = self.get_where_clause(pkey_values)
            updated = self._update_table(
                table_path, column_values, pkey=pkey_values)
            # row does not exist yet
            if upsert and updated == 0:
                # Todo: insert row with values including the primary keys?
                #column_values.update(pkey_values)
                self._insert_rows_in_table(
                    table_path,
                    list(columns) + pkey_values.keys(),
                    [list(values) + pkey_values.values()])

    def insert_dataframe_in_table(self, table_name, dataframe, workspace='',
                                  create=False):
        """
        Insert all rows of a pandas dataframe into a table in a Workspace in the
        Project Folder (column names have to match)

        Parameters
        ----------
        table_name : str
            name of the table
        column_values: dict,
            the columns and the values to update them with as key/value-pairs
        workspace : str, optional
            the database name
        create : bool, optional, default = False
            creates the table, drops if already existing

        """
        table_name = os.path.basename(table_name)
        table_path = self._get_table_path(table_name, workspace=workspace)
        df = dataframe
        if create:
            arcpy.Delete_management(table_path)
            arcpy.CreateTable_management(os.path.split(table_path)[0],
                                         table_name)
            columns = df.columns.tolist()
            for i, (column, dtype) in enumerate(zip(columns, df.dtypes)):
                dtype = str(dtype)
                if dtype.startswith('int'):
                    field_type = 'LONG'
                elif dtype.startswith('float'):
                    field_type = 'FLOAT'
                else:
                    field_type = 'TEXT'
                # can't use numbers as column names
                if type(column) != str:
                    column = columns[i] = '_{}'.format(column)
                arcpy.AddField_management(table_path, column, field_type)
        else:
            desc = arcpy.Describe(table_path)
            fields = [field.name for field in desc.fields]

            # intersection of fields between dataframe and available fields
            # (prevent writing columns of df that don't exist in db)
            columns = np.intersect1d(dataframe.columns.values, fields)
            #values = [row[1][columns].values for row in dataframe.iterrows()]
            # faster way
            df = dataframe[columns]
        cursor = arcpy.da.InsertCursor(table_path, columns)
        for index, row in df.iterrows():
            cursor.insertRow(row.tolist())
        del cursor

    def query_table(self, table_name, columns=[], workspace='',
                    where=None, pkey=None, project='', is_base_table=False):
        """
        get rows from a table, defaults to a Workspace in the Project Folder,
        if base table is requested workspace is required


        Parameters
        ----------
        table_name : str
            name of the table
        columns: list, optional
            the requested columns, if not given or empty: return all columns
        where: str, optional
            a where clause to pick single rows
        pkey: dict, optional
        workspace : str, optional
            the database name, required if base table
        project : str, optional
            the project (set project is taken if not given)
        is_base_table : bool, optional, default = False
            if True a base table is queried, else a project table

        Returns
        -------
        rows : list of lists
            the queried rows with values of requested columns in same order as
            in columns argument
        """
        # base table
        if is_base_table:
            if not workspace:
                raise Exception('Querying a base table requires the '
                                'specification of a workspace!')
            table_path = self.folders.get_base_table(workspace, table_name)
            rows = self._query_table(table_path, columns=columns, where=where)
        # project table (with temp. management)
        else:
            table_name = os.path.basename(table_name)
            workspace = os.path.basename(workspace) or self.tool._workspace
            table_path = self._get_table_path(table_name, workspace)
            rows = self._query_table(table_path, columns=columns, where=where,
                                     pkey=pkey)
        return rows

    def _query_table(self, table_path, columns=[], where=None, pkey=None):
        """
        get rows from a FileGeodatabase (full path required)

        Parameters
        ----------
        table_path : str
            full path to the table
        columns: list, optional
            the requested columns, if not given or empty: return all columns
        where: str, optional
            a where clause to pick single rows
        pkey: dict, optional

        Returns
        -------
        rows : list of lists
            the queried rows with values of requested columns in same order as
            in columns argument
        """
        where = where or self.get_where_clause(pkey)
        if not table_path or not arcpy.Exists(table_path):
            raise Exception('Die Tabelle existiert nicht')
        if not columns:
            columns = [f.name for f in arcpy.ListFields(table_path)]
        cursor = arcpy.da.SearchCursor(table_path, columns, where_clause=where)
        rows = [row for row in cursor]
        del cursor
        return rows

    def clear_temporary_dbs(self):
        """remove all temporary gdbs"""
        for project in self.folders.get_temporary_projects():
            path = self.folders.get_temporary_projectpath(project=project)
            #for fgdb in self._temporary_gdbs:
                #path = self.folders.get_temporary_db(fgdb=fgdb, project=project,
                                                     #check=False)
            if arcpy.Exists(path):
                arcpy.Delete_management(path)

    def add_temporary_management(self, workspace):
        """
        add a FileGeoDatabase to be managed temporarly,
        all updates on their tables happen inside the temporary database,
        the changes made are only transferred into the project database after
        pressing OK in the UI

        Parameters
        ----------
        workspace : str
            name of the FileGeoDatabase
        """
        if workspace not in self._temporary_gdbs:
            self._temporary_gdbs.append(workspace)

    def remove_temporary_management(self):
        """
        remove ALL FileGeoDatabases from temporary management
        """
        self._temporary_gdbs = []

    def _create_temporary_copy(self, workspace=''):
        """
        make a copy of a project fgdbs in the given temporary table
        """
        project_db = self.folders.get_db(workspace=workspace)
        temp_db = self.folders.get_temporary_db(workspace=workspace,
                                                check=False)
        if arcpy.Exists(temp_db):
            arcpy.Delete_management(temp_db)
        # deactivate adding of temp. gdbs to table of contents
        with ArcpyEnv(addOutputsToMap=False):
            arcpy.Copy_management(project_db, temp_db)

    def _commit_temporaries(self):
        """transfer all changes made in temporary tables into project tables"""
        gc.collect()

        temp_projects = self.folders.get_temporary_projects()
        if temp_projects:
            arcpy.AddMessage(
                u'Getätigte Änderungen werden in das Projekt übernommen...'
                .encode('latin1'))

        with ArcpyEnv(overwriteOutput=True):
            changes = 0
            for project in temp_projects:
                for fgdb in self._temporary_gdbs:
                    project_db = self.folders.get_db(workspace=fgdb,
                                                     project=project)
                    temp_db = self.folders.get_temporary_db(workspace=fgdb,
                                                            project=project,
                                                            check=False)
                    # temporary dbs only exist,
                    # if changes were made (else nothing to do here)
                    if arcpy.Exists(temp_db):
                        changes += self._replace_with_tempdb(temp_db,
                                                             project_db)
                arcpy.AddMessage(
                    '{} Datenbank(en) wurden erfolgreich geändert'.format(changes))

    def _replace_with_tempdb(self, temp_db, project_db):
        """
        replace project_db with temp_db

        Parameters
        ----------
        temp_db : str
        project_db : str
        """
        self.tool.output.change_layers_workspace(project_db, temp_db)
        res = arcpy.Compact_management(project_db)
        del res
        arcpy.Delete_management(project_db)
        arcpy.Copy_management(temp_db, project_db)
        # repair datasource of layers that reference the project_db
        # which was temporarily deleted
        self.tool.output.change_layers_workspace(temp_db, project_db)
        return 1

    def execute(self, parameters=None, messages=None):
        """
        Run the tool with the parameters and messages from ArcGIS

        Parameters
        ----------
        parameters : list of ArcGIS-Parameters

        messages : the message-object of ArcGIS

        """
        self._is_executing = True
        try:
            self._commit_temporaries()
        except:
            pass
        self.tool.main(self.par, parameters, messages)
        try:
            self.clear_temporary_dbs()
        except:
            pass
        self._is_executing = False
        self.show_outputs()

    def print_test_parameters(self):
        """
        Print the parameters to use in tests

        Examples
        --------
        >> tbx.print_test_parameters()
        ### Category 1 ###
        params.param_1.value = 123
        params.param_2.value = 456
        ### Category 2 ###
        params.param_3.value = 'DefaultString'
        """
        params = self._getParameterInfo()
        self._updateParameters(params)
        category = None
        for k, v in self.par._od.iteritems():
            if v.category and v.category != category:
                category = v.category
                print(u'### {} ###'.format(v.category))
            value = v.value
            if isinstance(value, (str, unicode)):
                value = u"'{}'".format(value)
            print (u'params.{k}.value = {v}'.format(v=value, k=k))

    def print_tool_parameters(self):
        """
        Print the parameters to use in a Tool

        Examples
        --------
        >> tbx.print_tool_parameters()
        ### Category 1 ###
        param_1 = params.param_1.value
        param_2 = params.param_2.value
        ### Category 2 ###
        param_3 = params.param_3.value
        """
        self._getParameterInfo()
        category = None
        for k, v in self.par._od.iteritems():
            if v.category and v.category != category:
                category = v.category
                print(u'### {} ###'.format(v.category))
            print (u'{k} = self.par.{k}.value'.format(k=k))


    def rename_params_in_tool(self):
        """
        rename parameters[n] into params.param_xyz in the Tools's module
        and save under new name tool_OLDNAME.py
        """
        module = sys.modules[self.Tool.__module__]
        path = module.__file__.rstrip('co')
        with open(path, 'r') as original_file:
            src = original_file.read()

        stub = 'parameters[{}].value'
        self._getParameterInfo()
        for i, key in enumerate(self.par._od):
            src = src.replace(stub.format(i), key)

        new_basename = 'tool_{}'.format(os.path.basename(path))
        new_fn = os.path.join(os.path.dirname(path), new_basename)

        with open(new_fn, 'w') as new_file:
            new_file.write(src)


class DummyTool(Tool):

    def add_outputs(self):
        pass

    def run(self):
        pass


class DummyTbx(Tbx):
    """dummy toolbox to be able to access functions of toolboxes outside of
    a 'real' toolbox, not for the purpose to be shown in ArcGIS
    """

    def __init__(self, projectname=''):
        self.projectname = projectname
        super(DummyTbx, self).__init__()
        self._getParameterInfo()

    def _getParameterInfo(self):
        p = self.add_parameter('projectname')
        p.name = 'Projekt'
        p.displayName = 'Projekt'
        p.parameterType = 'Required'
        p.direction = 'Input'
        p.datatype = 'GPString'
        p.filter.list = []
        p.value = self.projectname
        return self.par

    @property
    def Tool(self):
        return DummyTool

    @property
    def label(self):
        return ''

if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=True)
