# -*- coding: utf-8 -*-
from collections import OrderedDict
import arcpy
import numpy as np
import subprocess
import os
import sys
from rpctools.utils.config import Config, Folders
from rpctools.utils import image as image_exec
import requests
import shutil


class ArcpyEnv(object):
    """
    Context Manager to backup arcpy-environment values, set new one
    and restore the backuped files later
    """

    def __init__(self, object_to_backup=arcpy.env, **kwargs):
        """
        Params
        ------
        object_to_backup : object, optional(Default=arcpy.env)
        *kwargs : one or more key=value
            the arcpy.env.attributes to backup

        Examples
        --------
        >>> my_object = OrderedDict()
        >>> my_object.aaa = 11
        >>> my_object.bbb = 22
        >>> with ArcpyEnv(bbb=99, aaa=22, object_to_backup=my_object):
        ...     print(my_object.aaa)
        ...     print(my_object.bbb)
        ...     my_object.aaa = 77
        ...     print(my_object.aaa)
        22
        99
        77
        >>> my_object.aaa
        11
        >>> my_object.bbb
        22
        >>> with ArcpyEnv(bbb=99, aaa=22, object_to_backup=my_object):
        ...     my_object.aaa = 77
        ...     raise ValueError('Error')
        Traceback (most recent call last):
            ...
        ValueError: Error
        >>> my_object.aaa
        11
        >>> my_object.bbb
        22
        """
        self._object_to_backup = object_to_backup
        self._kwargs = kwargs
        self._backups = dict()

    def __enter__(self):
        for attr, value in self._kwargs.iteritems():
            self._backups[attr] = getattr(self._object_to_backup, attr)
            setattr(self._object_to_backup, attr, value)

    def __exit__(self, exc_type, exc_value, traceback):
        for attr, value in self._backups.iteritems():
            setattr(self._object_to_backup, attr, value)


class LayerGroup(OrderedDict):
    """"""
    def __init__(self, label='root'):
        """
        Parameters
        ----------
        label : str, optional(defaul='root')
            the label of the layer group

        Examples
        --------
        >>> lg = LayerGroup()
        >>> lg.label
        'root'
        """
        super(LayerGroup, self).__init__()
        self.label = label

    def __repr__(self, _repr_running={}):
        return self.label

    def __getitem__(self, key):
        value = self.get_value(key)
        if value is None:
            raise KeyError('{} not found'.format(key))
        return value

    def get_label(self, key):
        """
        return the label of the given key in self or a subgroup

        Parameters
        ----------
        key : str

        Returns
        -------
        label : str
        """
        return self[key].label

    def get_labels(self):
        """
        return all labels in order of adding

        Returns
        -------
        labels : list of str
        """
        labels = [self[key].label for key in self.keys()]
        return labels

    def get_value(self, key):
        value = self.get(key)
        it = self.itervalues()
        while value is None:
            try:
                group = it.next()
                value = group.get_value(key)
            except StopIteration:
                break
        return value

    def add(self, key, label):
        """
        Parameters
        ----------
        key : str
            the key of the layer group
        label : str
            the label of the layer group

        Examples
        --------
        >>> lg = LayerGroup()
        >>> analysen = lg.add('analyse', 'Analysen')
        >>> definition = lg.add('definition', 'Definition')
        >>> einnahmen = analysen.add('einnahmen', 'Einnahmen')
        >>> steuern = einnahmen.add('steuern', 'Steuern')
        >>> ausgaben = analysen.add('ausgaben', 'Ausgaben')
        >>> nutzung = definition.add('nutzung', 'Nutzungsart')
        >>> analysen.label
        'Analysen'
        >>> nutzung.label
        'Nutzungsart'
        >>> lg['nutzung']
        Nutzungsart
        >>> lg['analyse']
        Analysen
        >>> len(lg['analyse'])
        2
        >>> len(lg['definition'])
        1
        >>> len(lg['ausgaben'])
        0
        >>> len(lg['einnahmen'])
        1
        >>> lg['steuern']
        Steuern
        >>> analysen['steuern']
        Steuern
        >>> einnahmen['steuern']
        Steuern
        >>> definition['steuern']
        Traceback (most recent call last):
            ...
        KeyError: 'steuern not found'
        """
        lg = LayerGroup(label)
        self[key] = lg
        return lg


class Image(object):
    def __init__(self,
                 image_path,
                 window_title,
                 width=7.0,
                 height=5.0,
                 interpolation = "lanczos",
                 show_white_space = False,
                 show_toolbar=False):
        self.image_path = image_path
        self.window_title = window_title
        self.width = width
        self.height = height
        self.interpolation = interpolation
        self.show_white_space = show_white_space
        self.show_toolbar = show_toolbar


class Layer(object):
    def __init__(self,
                 groupname,
                 template_layer,
                 name='',
                 featureclass='',
                 workspace='',
                 template_folder='',
                 disable_other=False,
                 visible=True,
                 subgroup="",
                 in_project=True,
                 query="",
                 symbology={},
                 label_replace={},
                 zoom=True,
                 zoom_extent=None,
                 symbology_classes=None,
                 show_wms_legends=False):
        self.groupname = groupname
        self.template_layer = template_layer
        self.featureclass = featureclass
        self.disable_other = disable_other
        self.visible = visible
        self.subgroup = subgroup
        self.in_project = in_project
        self.zoom = zoom
        self.zoom_extent = zoom_extent
        self.template_folder = template_folder
        self.query = query
        self.name = name
        self.symbology = symbology
        self.label_replace = label_replace
        self.workspace = workspace
        self.symbology_classes = symbology_classes
        self.show_wms_legends = show_wms_legends


class Output(object):
    """
    Add and update layers to the current ArcMap file.
    """
    _workspace = None

    def __init__(self, params=None):
        self.config = Config()
        self.params = params
        # no params object given -> take a fixed project name (the currently
        # active one)
        projectname = None if params is not None else self.config.active_project
        self.folders = Folders(params=params, workspace=self._workspace,
                               projectname=projectname)
        self.module = LayerGroup()
        self.layers = []
        self.diagrams = []
        self.images = []
        self.add_layer_groups()
        self.define_outputs()

    def add_layer_groups(self):
        root = self.module
        background = root.add('hintergrundkarten',
                              'Hintergrundkarten Projekt-Check')

        # project specific layers
        # order of adding will represent order in TOC! (first added -> on top)
        root.add("projektdefinition", u"Projektdefinition")
        root.add("bevoelkerung",
                 u"Wirkungsbereich 1 - Bewohner und Arbeitsplaetze")
        root.add("erreichbarkeit",
                 u"Wirkungsbereich 2 - Erreichbarkeit")
        root.add("verkehr", u"Wirkungsbereich 3 - Verkehr im Umfeld")
        root.add("oekologie", u"Wirkungsbereich 4 - Flaeche und Oekologie")
        root.add("infrastruktur",
                 u"Wirkungsbereich 5 - Infrastrukturfolgekosten")
        root.add("einnahmen",
                 u"Wirkungsbereich 6 - Kommunale Steuereinnahmen")
        root.add("standortkonkurrenz",
                 u"Wirkungsbereich 7 - Standortkonkurrenz "
                 u"Lebensmitteleinzelhandel")
        root.add("hintergrund", u"Hintergrund")

    def define_outputs(self):
        '''define the output layers here, has to be implemented in subclasses'''

    @property
    def projectname(self):
        projectname = self.params.get_projectname() if self.params else \
            self.config.active_project
        return projectname

    def set_projectlayer(self, projektname=None):
        """
        Check and add project layer
        """
        projektname = projektname or self.projectname
        current_mxd = arcpy.mapping.MapDocument("CURRENT")
        current_dataframe = current_mxd.activeDataFrame

        layer_exists = arcpy.mapping.ListLayers(
            current_mxd,
            projektname,
            current_dataframe)
        if layer_exists:
            is_grouplayer = layer_exists[0].isGroupLayer
        else:
            is_grouplayer = False
        if not layer_exists or not is_grouplayer:
            group_layer_template = self.folders.get_layer(
                layername="__Projektname__", folder='toc', enhance=True)
            addLayer = arcpy.mapping.Layer(group_layer_template)
            addLayer.name = projektname
            arcpy.mapping.AddLayer(current_dataframe, addLayer, "TOP")
            del(addLayer)
        del(current_dataframe)
        del(current_mxd)

    def get_projectlayer(self, projectname=None):
        """
        Returns project layer in table of contents

        Parameters
        ----------
        projectname : str, optional
        """
        projectname = projectname or self.projectname
        current_mxd = arcpy.mapping.MapDocument("CURRENT")
        current_dataframe = current_mxd.activeDataFrame
        layers = arcpy.mapping.ListLayers(current_mxd, projectname,
                                          current_dataframe)
        projectlayer = []
        for layer in layers:
            if layer.isGroupLayer:
                projectlayer = layer
        del(current_dataframe)
        del(current_mxd)
        return projectlayer

    def remove_layer(self, layername):
        '''remove layers with given name from project
        (removes all appearances)'''
        layers = self.get_layers(layername)
        current_mxd = arcpy.mapping.MapDocument("CURRENT")
        current_dataframe = current_mxd.activeDataFrame
        for layer in layers:
            arcpy.mapping.RemoveLayer(current_dataframe, layer)

    @staticmethod
    def change_layers_workspace(source_ws, target_ws):
        """
        change the workspace in the current map that reference source_ws
        to target_ws

        Parameters
        ----------
        source_ws : str
        target_ws : str
        """
        mxd = arcpy.mapping.MapDocument('CURRENT')
        mxd.findAndReplaceWorkspacePaths(source_ws, target_ws)
        arcpy.RefreshActiveView()

    def get_layers(self, layername, projectname=None):
        """
        Return all layers with given name that are grouped in given project
        (respectively in currently set project)

        Parameters
        ----------
        layername : str
        projectname : str, optional

        Returns
        ----------
        layers : list
              all layers found in project
        """

        # Neuen Layer hinzufuegen
        project_layer = self.get_projectlayer(projectname=projectname)
        if not project_layer:
            return []
        layers = arcpy.mapping.ListLayers(project_layer, layername)
        return layers

    def set_backgroundgrouplayer(self, dataframe=None):
        """
        Check and add Background layer group
        """
        current_mxd = arcpy.mapping.MapDocument("CURRENT")
        dataframe = dataframe or current_mxd.activeDataFrame
        hintergrund = self.module.get_label("hintergrundkarten")
        if not arcpy.mapping.ListLayers(current_mxd,
                                        hintergrund,
                                        dataframe):
            group_layer_template = self.folders.get_layer(
                layername=hintergrund, folder='toc', enhance=True)
            addLayer = arcpy.mapping.Layer(group_layer_template)
            arcpy.mapping.AddLayer(dataframe, addLayer, "BOTTOM")
            del(addLayer)
        del(current_mxd)

    def add_osm_layer(self):
        # add OpenStreetmap
        layer = "OpenStreetMap"
        self.add_layer("hintergrundkarten", layer,
                       zoom=False, in_project=False)

    def add_project_contour(self):
        # add contours
        fc = "Teilflaechen_Plangebiet"
        layer = "Umriss des Plangebiets"
        self.add_layer("hintergrund", layer, fc,
                       workspace='FGDB_Definition_Projekt.gdb',
                       zoom=False)

    def hide_layer(self, layername):
        '''hide layer(s) in TOC matching given name,
        layername may also be the placeholder group-name (e.g. bevoelkerung)'''
        if not self.layer_exists(layername):
            try:
                layername = self.module.get_label(layername)
            except:
                return
        for l in self.get_layers(layername):
            l.visible = False
        arcpy.RefreshActiveView()
        arcpy.RefreshTOC()

    def enable_layer(self, layername):
        '''enable layer(s) in TOC matching given name,
        layername may also be the placeholder group-name (e.g. bevoelkerung)'''
        if not self.layer_exists(layername):
            try:
                layername = self.module.get_label(layername)
            except:
                return
        for l in self.get_layers(layername):
            l.visible = True
        arcpy.RefreshActiveView()
        arcpy.RefreshTOC()

    def set_grouplayer(self, group,
                       project_layer=None,
                       dataframe=None):
        """
        Check and add subgroup layer
        """
        project_layer = project_layer or self.get_projectlayer()
        current_mxd = arcpy.mapping.MapDocument("CURRENT")
        dataframe = dataframe or current_mxd.activeDataFrame

        if not arcpy.mapping.ListLayers(project_layer, group, dataframe):
            group_layer_template = self.folders.get_layer(layername=group,
                                                          folder='toc', enhance=True)
            addLayer = arcpy.mapping.Layer(group_layer_template)
            arcpy.mapping.AddLayerToGroup(
                dataframe, project_layer, addLayer, "BOTTOM")
            del(addLayer)
        del(current_mxd)

    def set_subgrouplayer(self,
                          group,
                          subgroup,
                          project_layer=None,
                          dataframe=None):
        """
        Check and add subgroup layer
        """
        project_layer = project_layer or self.get_projectlayer()
        current_mxd = arcpy.mapping.MapDocument("CURRENT")
        dataframe = dataframe or current_mxd.activeDataFrame

        group_layer = arcpy.mapping.ListLayers(
            project_layer, group, dataframe)[0]
        if not arcpy.mapping.ListLayers(group_layer, subgroup, dataframe):
            subgroup_layer_template = self.folders.get_layer(
                layername=subgroup,
                folder='toc',
                enhance=True)
            addLayer = arcpy.mapping.Layer(subgroup_layer_template)
            target_grouplayer = arcpy.mapping.ListLayers(
                project_layer, group, dataframe)[0]
            arcpy.mapping.AddLayerToGroup(
                dataframe, target_grouplayer, addLayer, "BOTTOM")
            del(addLayer)
            del(target_grouplayer)
        del(current_dataframe)
        del(current_mxd)

    def add_layer(self,
                  groupname,
                  template_layer,
                  featureclass='',
                  workspace='',
                  template_folder='',
                  name='',
                  disable_other=False,
                  visible=True,
                  subgroup="",
                  in_project=True,
                  query="",
                  symbology={},
                  label_replace={},
                  zoom=True,
                  zoom_extent = None,
                  symbology_classes=None,
                  show_wms_legends=False):
        """
        Add output layer

        Parameters
        ----------
        groupname : str
            the layer group

        template_layer : str
            name of the template layer

        featureclass : str, optional
            the name of the feature class table,
            which should be linked to the layer

        workspace : str, optional (Default = workspace of Tool)
            the workspace the featureclass is in

        name: str, optional
            name of the layer in TOC (defaults to name of template layer)

        query: str, optional
            query definition, defines which features are shown (e.g. id=10)
            (shows all features by default)

        template_folder : str, optional
            a subfolder of the template_layer

        disable_other : boolean, optional(Default=False)
            if true, then all other layers will be turned off

        subgroup : str, optional
            the subgroup of the layergroup

        in_project : bool, optional(Default = True)
            if False, layer will be created outside the project layers

        zoom : bool, optional(Default = True)
            if True, zoom to layer extent

        symbology : dictionary, optional
            sets symbology of layer on show, keys are the symbology-field and
            values the values to be set
        label_replace : dictionary, optional
            replaces columns in label expressions, keys are the old values and
            the values the new ones to replace them with
        symbology_classes : tuple of int and string, optional
            Set a number of symbology classes for the layer between min and
            max value.
        """
        if not name:
            name = template_layer
        layer = Layer(groupname, template_layer, name=name,
                      featureclass=featureclass, workspace=workspace,
                      disable_other=disable_other, visible=visible,
                      subgroup=subgroup,
                      in_project=in_project, zoom=zoom,
                      zoom_extent=zoom_extent, query=query,
                      template_folder=template_folder, symbology=symbology,
                      label_replace=label_replace,
                      symbology_classes=symbology_classes,
                      show_wms_legends=show_wms_legends)
        self.layers.append(layer)

    def add_diagram(self, *args):
        '''add a diagram (or multiple diagrams), diagram has to be an
        instantiated subclass of Diagram'''
        for arg in args:
            self.diagrams.append(arg)

    def show(self):
        '''show all available outputs (diagrams, layers etc.)'''
        self.show_layers()
        self.show_diagrams()
        self.show_images()
        arcpy.RefreshActiveView()
        arcpy.RefreshTOC()

    def show_diagrams(self):
        '''show available diagrams'''
        for diagram in self.diagrams:
            diagram.show()

    def show_layers(self, redraw=True):
        '''show available layers'''
        if len(self.layers) == 0:
            return
        ## always add an osm layer and the contours of the areas background
        # self.add_osm_layer()
        # self.add_project_contour()
        for layer in self.layers:
            self._show_layer(layer, redraw=redraw)

    def show_images(self):
        for image in self.images:
            self._show_image(image)
        self.images = []

    def _show_image(self, image):
        attrs = ['image_path', 'window_title', 'width', 'height', 'interpolation',
                 'show_white_space', 'show_toolbar']
        #params = []
        #for a in attrs:
            #p = getattr(image, a)
            #if not isinstance(p, str):
                #p = str(p)
            #params.append(p)
        params = [str(getattr(image, a)) for a in attrs]
        print params
        subprocess.Popen(
            [os.path.join(sys.exec_prefix, 'python.exe'),
             '-m' , image_exec.__name__] + params, shell=True)

    def add_image(self,
                  image_path,
                  window_title,
                  width=15.0,
                  height=10.0,
                  interpolation = "lanczos",
                  show_white_space = False,
                  show_toolbar=False):

        if not arcpy.Exists(image_path):
            return
        image = Image(image_path, window_title, width, height, interpolation,
                      show_white_space, show_toolbar)
        self.images.append(image)

        """
        Displays a specified image via matplotlib

        Parameters
        ----------
        image : str
            full path to image file

        window_title : str
            title of the new window

        window_size: int list, optional
            size of the new window in inches [width, height]

        interpolation : str, optional
            type of interpolation

        show_white_space: boolean, optional
            if true, the image is displayed with white margins

        show_toolbar : boolean, optional
            if true, the toolbar within the new window is enabled
        """
    def clear(self):
        '''remove all outputs (diagrams, layers etc.)'''
        self.diagrams = []
        self.layers = []

    def _show_layer(self, layer, redraw=True):
        """show the layer by adding it to the TOC of ArcGIS"""
        current_mxd = arcpy.mapping.MapDocument("CURRENT")
        current_dataframe = current_mxd.activeDataFrame
        self.set_backgroundgrouplayer(current_dataframe)

        if not redraw and self.layer_exists(layer.name):
            arcpy.RefreshActiveView()
            return
        self.remove_layer(layer.name)
        projektname = self.projectname

        group = self.module.get_label(layer.groupname)
        current_dataframe.geographicTransformations = ['DHDN_To_WGS_1984_5x',
                                                       'DHDN_To_ETRS_1989_5']

        # Layer-Gruppen hinuzfuegen, falls nicht vorhanden
        self.set_projectlayer(projektname)
        project_layer = self.get_projectlayer(projektname)

        # Template Layer laden
        template_layer = self.folders.get_layer(layer.template_layer,
                                                layer.template_folder)
        if not os.path.exists(template_layer):
            raise Exception('Layer-file {} does not exist!'.format(template_layer))
        #arcpy.AddMessage(template_layer)
        source_layer = arcpy.mapping.Layer(template_layer)

        # Datasource des Layers auf die gewünschte FeatureClass setzen
        if layer.featureclass:
            featureclass = self.folders.get_table(layer.featureclass,
                                                  workspace=layer.workspace)
            source_ws = source_layer.workspacePath
            target_ws = arcpy.Describe(featureclass).path
            #source_layer.findAndReplaceWorkspacePath(source_ws, target_ws)
            source_layer.replaceDataSource(dataset_name=layer.featureclass,
                                           workspace_path=target_ws)

        # Untergruppen hinzufügen
        if layer.in_project:
            self.set_grouplayer(group, project_layer, current_dataframe)
            #for l in self.get_layers(group)[0]: l.visible = True
            if layer.subgroup != "":
                self.set_subgrouplayer(group, layer.subgroup,
                                       project_layer, current_dataframe)

            # Neuen Layer hinzufuegen
            target_grouplayer = arcpy.mapping.ListLayers(
                project_layer, group, current_dataframe)[0]
        else:
            target_grouplayer = arcpy.mapping.ListLayers(
                current_mxd, group, current_dataframe)[0]

        # Layer zur Group oder Subgroup hinzufügen
        if not layer.subgroup:
            self.add_or_replace_layer(target_grouplayer,
                                      current_dataframe,
                                      source_layer)
        else:
            target_subgrouplayer = arcpy.mapping.ListLayers(
                target_grouplayer, layer.subgroup, current_dataframe)[0]

            self.add_or_replace_layer(target_subgrouplayer,
                                      current_dataframe,
                                      source_layer)

        # neuer Layer
        new_layer = arcpy.mapping.ListLayers(target_grouplayer,
                                             source_layer.name,
                                             current_dataframe)[0]
        # Auf Layer zentrieren
        if layer.zoom:
            if layer.zoom_extent is not None:
                ext = arcpy.Extent(*layer.zoom_extent)
            else:
                ext = new_layer.getExtent()
            current_dataframe.extent = ext

        if layer.disable_other == True:
            for lyr in arcpy.mapping.ListLayers(project_layer):
                lyr.visible = False
        if layer.symbology_classes is not None:
            num_symclasses, column = layer.symbology_classes
            self.update_layersymbology(new_layer, num_symclasses, column)

        new_layer.visible = layer.visible
        for lyr in arcpy.mapping.ListLayers(new_layer):
            lyr.visible = layer.visible
        new_layer.name = layer.name
        if layer.query:
            new_layer.definitionQuery = layer.query
        if layer.subgroup != "":
            target_subgrouplayer.visible = True

        # not all layers support symbology
        try:
            sym = new_layer.symbology
            for f, v in layer.symbology.iteritems():
                setattr(sym, f, v)
        except Exception as e:
            pass
            #print(e)

        # same with labels
        try:
            for label_class in new_layer.labelClasses:
                exp = label_class.expression
                for l, v in layer.label_replace.iteritems():
                    exp = exp.replace(l, v)
                label_class.expression = exp
        except Exception as e:
            pass
            #print(e)

        target_grouplayer.visible = True
        if layer.in_project:
            project_layer.visible = True

        if layer.show_wms_legends:
            url = new_layer.serviceProperties['URL']
            for l in new_layer:
                name = l.serviceProperties['Name']
                legend_url = url + '&layer={}'.format(name)
                legend_url += '&sld_version=1.1.0&request=GetLegendGraphic&service=WMS&version=1.3.0&format=image/png'
                fn = name + '.png'
                fp = os.path.join(os.path.split(template_layer)[0], fn)
                arcpy.Delete_management(fp)
                title = l.serviceProperties['WMSTitle'].encode('utf-8')
                r = requests.get(legend_url, stream=True)
                if r.status_code == 200:
                    with open(fp, 'wb') as f:
                        r.raw.decode_content = True
                        shutil.copyfileobj(r.raw, f)
                    legend = Image(fp, title)
                    self._show_image(legend)

        self.sort_layers()
        del(current_dataframe)
        del(new_layer)
        del(current_mxd)

    def sort_layers(self):
        project_layer = self.get_projectlayer()
        # groups currently in toc for active project
        groups = [l for l in arcpy.mapping.ListLayers(project_layer)
                  if l.isGroupLayer]
        group_names = [g.name for g in groups]
        # labels have already the desired sorting
        labels = np.array(self.module.get_labels())
        toc_unsorted = np.array(group_names)[np.in1d(group_names, labels)]
        # get groups that are also in project labels, retaining order of labels
        names_sorted = np.array(labels)[np.in1d(labels, group_names)]
        # no need to sort if only one group or already sorted
        if (len(names_sorted) == 1 or
            (toc_unsorted != names_sorted).sum() == 0):
            return
        layers_sorted = [groups[group_names.index(n)] for n in names_sorted]

        mxd = arcpy.mapping.MapDocument("CURRENT")
        df = arcpy.mapping.ListDataFrames(mxd)[0]
        # arcpy doesn't know the layers anymore after being moved
        # so take last layer (in label order) as reference and move other
        # layers before it (ascending)
        ref_layer = layers_sorted[-1]
        for layer in layers_sorted[:-1]:
            arcpy.mapping.MoveLayer(df, ref_layer, layer, "BEFORE")

    def layer_exists(self, layername):
        projektname = self.projectname
        current_mxd = arcpy.mapping.MapDocument("CURRENT")
        current_dataframe = current_mxd.activeDataFrame
        project_layer = arcpy.mapping.ListLayers(current_dataframe, projektname)
        if not project_layer or not arcpy.mapping.ListLayers(project_layer[0],
                                                             layername):
            return False
        return True

    def add_or_replace_layer(self,
                             target_grouplayer,
                             current_dataframe,
                             source_layer):
        """
        Add source_layer to target_grouplayer
        in the current_dataframe and remove existing layer
        in the target_grouplayer if exists"""
        existing_layers = arcpy.mapping.ListLayers(
            target_grouplayer,
            source_layer.name,
            current_dataframe)
        if existing_layers:
            for layer in existing_layers:
                arcpy.mapping.RemoveLayer(current_dataframe, layer)

        arcpy.mapping.AddLayerToGroup(current_dataframe,
                                      target_grouplayer,
                                      source_layer, "BOTTOM")

    def delete_output(self, layer):

        projektname = self.projectname
        current_mxd = arcpy.mapping.MapDocument("CURRENT")
        current_dataframe = current_mxd.activeDataFrame
        project_layer = self.get_projectlayer(projektname)

        if project_layer:
            layer_exists = arcpy.mapping.ListLayers(project_layer,
                                                    layer, current_dataframe)
            if layer_exists:
                arcpy.mapping.RemoveLayer(current_dataframe, layer_exists[0])

        del(current_dataframe)
        del(current_mxd)
        arcpy.RefreshActiveView()
        arcpy.RefreshTOC()


    def replace_output(self,
                       groupname,
                       fc,
                       layername,
                       folder = '',
                       subgroup='',
                       disable_other=False):
        """
        delete output layer if exists and create a new layer in groupname

        Parameters
        ----------
        groupname : str
            the groupname where the layer should be created
        fc : str
            the featur-class to show
        layername : str
            the layername
        folder : str
            the folder, where the template layer resides
        subgroup : str, optional
            the subgroup below the group
        disable_other : bool, optional(default=False)
            if true, disable other layers
        """
        self.delete_output(layername)
        template_lyr = self.folders.get_layer(layername=layername,
                                              enhance=True,
                                              folder=folder)
        self.add_layer(groupname=groupname,
                       template_layer=template_lyr,
                        featureclass=fc,
                        disable_other=disable_other,
                        subgroup=subgroup,
                        )

    @staticmethod
    def reclassify_layer(mxd, lyrname):
        """
        Reclassify the first layer in the mxd that matches lyrname

        Parameters
        ----------
        mxd : map-instance
        lyrname : str
            the layername
        """
        matched_layers = arcpy.mapping.ListLayers(mxd, lyrname)
        if matched_layers:
            lyr = matched_layers[0]
            lyr.symbology.reclassify()

    def define_projection(self):
        """Define the projection of the current dataframe from the config"""
        mxd = arcpy.mapping.MapDocument('CURRENT')
        df = mxd.activeDataFrame
        sr = arcpy.SpatialReference(self.config.epsg)
        df.spatialReference = sr
        df.geographicTransformations = [self.config.transformation]
        arcpy.RefreshActiveView()
        del(mxd)
        del(df)

    @staticmethod
    def add_graph(input_template, graph, out_graph_name):
        """
        Add a graph to the output.
        If a graph with the same name already exists,
        replace it with the new one

        Parameters
        ----------
        input_template : a graph template
        graph : arcpy.Graph-instance
        out_graph_name : str
            the name of the graph to create
        """
        with ArcpyEnv(addOutputsToMap=True, overwriteOutput=True):
            arcpy.MakeGraph_management(input_template, graph, out_graph_name)

    def update_layersymbology(self, lyr, num_classes=13, column='weight'):
        """
        update the class break values of layersymbology

        Parameters
        ----------
        num_classes : int
            number of classes of the new layersymbology
        min_val : int or float
            minimum class value
        max_val : int or float
            maximum class value
        """
        from rpctools.utils.params import DummyTbx
        #get layer
        #mxd = arcpy.mapping.MapDocument('CURRENT')
        #lyr = arcpy.mapping.ListLayers(mxd, layername)
        #arcpy.AddMessage(lyr)
        #lyr = lyr[0]
        data_source = lyr.dataSource
        # get new classes
        tbx = DummyTbx()
        data = tbx._query_table(data_source, columns=[column])
        min_val = int(min(data)[0])
        max_val = int(max(data)[0]) + 1
        new_classes = np.linspace(min_val, max_val, num=num_classes + 1)
        new_classes = np.round(new_classes).astype(int)
        labels = ['bis zu {}'.format(c) for c in new_classes[1:]]
        # update layer
        lyr.symbology.classBreakValues = new_classes
        lyr.symbology.classBreakLabels = labels
        lyr.symbology.reclassify()
        arcpy.RefreshTOC()
        arcpy.RefreshActiveView()



if __name__ == '__main__':
    o = Output()
    o.update_layersymbology(u'Zusätzliche PKW-Fahrten')
    import doctest
    doctest.testmod(verbose=True)

