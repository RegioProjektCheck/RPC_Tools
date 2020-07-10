# -*- coding: utf-8 -*-
#
import arcpy
import os

from rpctools.utils.params import Tbx, Tool
from rpctools.addins.common import config
from rpctools.utils.spatial_lib import to_project_srid
from rpctools.utils.encoding import encode
from rpctools.definitions.projektverwaltung.tbx_teilflaechen_verwalten \
     import TbxFlaechendefinition
from rpctools.utils.constants import Nutzungsart


class SetSource(Tool):
    _workspace = 'FGDB_Verkehr.gdb'

    def add_outputs(self):
        # get extent
        toolbox = self.parent_tbx
        points = toolbox.table_to_dataframe('Anbindungspunkte',
                                            columns=['SHAPE'],
                                            workspace='FGDB_Verkehr.gdb').as_matrix()
        self.set_layer_extent(points)
        # update the names of the areas the points belong to
        df_areas = self.parent_tbx.table_to_dataframe(
            'Teilflaechen_Plangebiet',
            workspace='FGDB_Definition_Projekt.gdb',
            columns=['id_teilflaeche', 'Name']
        )
        df_points = self.parent_tbx.table_to_dataframe(
            'Anbindungspunkte', columns=['id_teilflaeche'])
        df_points = df_points.merge(df_areas, on='id_teilflaeche')
        df_points.rename(columns={'Name': 'name_teilflaeche'}, inplace=True)
        self.parent_tbx.dataframe_to_table('Anbindungspunkte', df_points,
                                           ['id_teilflaeche'])

        self.output.add_layer('projektdefinition', 'Anbindungspunkte',
                              featureclass='Anbindungspunkte',
                              template_folder='Verkehr',
                              zoom=True, zoom_extent=self._extent)
        self.output.hide_layer('projektdefinition')

    def run(self):
        area, i = self.parent_tbx.get_selected_area()
        toolbox = self.parent_tbx
        source_x = toolbox.x
        source_y = toolbox.y
        shape = arcpy.Point(source_x, source_y)
        id = area['id_teilflaeche']
        toolbox.update_table('Anbindungspunkte',
                             {'Shape': shape},
                             where='id_teilflaeche={}'.format(id),
                             workspace='FGDB_Verkehr.gdb')
        arcpy.AddMessage(u"initialisiertes Verkehrsaufkommen wird gelöscht")
        self.remove_output()
        # delete pickle file
        pickle_path = self.folders.get_otp_pickle_filename(check=False)
        if os.path.exists(pickle_path):
            os.remove(pickle_path)
            # empty gdb tables
            tn_path = toolbox.folders.get_table('Zielpunkte',
                                                workspace=self._workspace)
            links_path = toolbox.folders.get_table('links',
                                                   workspace=self._workspace)
            nodes_path = toolbox.folders.get_table('nodes',
                                                   workspace=self._workspace)
            routes_path = toolbox.folders.get_table('Routes',
                                                    workspace=self._workspace)
            tables_to_clear = [tn_path, links_path, nodes_path, routes_path]
            for path in tables_to_clear:
                arcpy.DeleteRows_management(path)

    def remove_output(self):
        mxd = arcpy.mapping.MapDocument("CURRENT")
        df = arcpy.mapping.ListDataFrames(mxd, "*")[0]
        layers1 = arcpy.mapping.ListLayers(mxd, "*Zielpunkte*", df)
        layers2 = arcpy.mapping.ListLayers(mxd, "*Fahrten*", df)
        layers = sum([layers1, layers2], [])
        for layer in layers:
            arcpy.mapping.RemoveLayer(df, layer)
        del(mxd)

    def set_layer_extent(self, points, zoom_border=0.2):
        """
        get the layer extent from points.

        Parameters
        ----------
        points : np.array of points shape = (n, 1)
        zoom_border : float, optional
            expands the extend by a factor
        """
        transformed = [to_project_srid(point[0][0], point[0][1], config.epsg)
                       for point in points]
        x_coords = [point[0] for point in transformed]
        y_coords = [point[1] for point in transformed]
        x_max = max(x_coords)
        x_min = min(x_coords)
        y_max = max(y_coords)
        y_min = min(y_coords)
        x_area = x_max - x_min
        y_area = y_max - y_min

        self._extent = (x_min - zoom_border * x_area,
                        y_min - zoom_border * y_area,
                        x_max + zoom_border * x_area,
                        y_max + zoom_border * y_area)


class TbxSetSource(TbxFlaechendefinition):

    @property
    def label(self):
        return encode(u'Anbindung einer Teilfläche an das Straßennetz')

    @property
    def Tool(self):
        return SetSource

    def _open(self, params):
        super(TbxSetSource, self)._open(params)
        self.x, self.y = self.config.active_coord

    def _getParameterInfo(self):
        params = super(TbxSetSource, self)._getParameterInfo()
        params.area.displayName = encode(u'Teilfläche, die über den eben in '
                                         u'der Karte gesetzten Anbindungspunkt'
                                         u' an das Straßennetz angeschlossen'
                                         u'werden soll')
        return self.par

    def set_selected_area(self):
        pass

if __name__ == '__main__':
    tbx = TbxSetSource()
    tbx._getParameterInfo()
    tbx.set_active_project()
    tbx.execute()
    print
