# -*- coding: utf-8 -*-
import arcpy
import os
import pandas as pd
import json

from rpctools.utils.params import Tbx, Tool
from rpctools.utils.encoding import encode
from rpctools.utils.spatial_lib import get_project_centroid
from rpctools.analyst.standortkonkurrenz.zensus import Zensus
from rpctools.analyst.standortkonkurrenz.routing_distances import DistanceRouting
from rpctools.analyst.standortkonkurrenz.osm_einlesen import Point


class DistMarkets(Tool):
    _param_projectname = 'projectname'
    _workspace = 'FGDB_Standortkonkurrenz_Supermaerkte.gdb'

    def run(self):
        square_size = self.par.square_size.value * 1000
        zensus = Zensus()

        x, y = get_project_centroid(self.projectname)
        centroid = Point(x, y, epsg=self.parent_tbx.config.epsg)

        arcpy.AddMessage('Extrahiere Siedlungszellen aus Zensusdaten...')
        zensus_points, bbox = zensus.cutout_area(centroid, square_size)
        arcpy.AddMessage('Schreibe Siedlungszellen in Datenbank...')
        self.zensus_to_db(zensus_points)
        active_project = self.parent_tbx.config.active_project
        zensus.add_kk(zensus_points, active_project)
        # TODO: Update instead of rewrite
        self.zensus_to_db(zensus_points)
        arcpy.AddMessage(u'Berechne Entfernungen der Märkte '
                         u'zu den Siedlungszellen...')
        markets = self.parent_tbx.table_to_dataframe('Maerkte')
        epsg = self.parent_tbx.config.epsg

        routing = DistanceRouting()
        destinations = self.get_cells()
        dest_ids = [d.id for d in destinations]
        for id, market in markets.iterrows():
            arcpy.AddMessage(' - {}'.format(market['name']))
            market_id = market['id']
            x, y = market['SHAPE']
            origin = Point(x, y, id=market_id, epsg=epsg)
            distances = routing.get_distances(origin, destinations, bbox)
            self.distances_to_db(market_id, destinations, distances)

    def distances_to_db(self, market_id, destinations, distances):
        self.parent_tbx.delete_rows_in_table(
            'Distanzen', where='id_markt={}'.format(market_id))
        column_values = {}
        shapes = []
        ids = []
        for dest in destinations:
            ids.append(dest.id)
            shapes.append(arcpy.Point(dest.x, dest.y))
        column_values['distanz'] = distances
        column_values['id_siedlungszelle'] = ids
        column_values['SHAPE'] = shapes
        column_values['id_markt'] = [market_id] * len(destinations)
        self.parent_tbx.insert_rows_in_table('Distanzen', column_values)

    def get_cells(self):
        cells = []
        epsg = self.parent_tbx.config.epsg
        df = self.parent_tbx.table_to_dataframe('Siedlungszellen')
        for id, cell in df.iterrows():
            x, y = cell['SHAPE']
            dest = Point(x, y, id=cell['id'], epsg=epsg)
            cells.append(dest)
        return cells

    def zensus_to_db(self, zensus_points):
        df = pd.DataFrame()
        epsg = self.parent_tbx.config.epsg
        shapes = []
        ews = []
        kk_indices = []
        kks = []
        cell_ids = []
        self.parent_tbx.delete_rows_in_table('Siedlungszellen')
        for point in zensus_points:
            if point.ew <= 0:
                continue
            t = point.transform(epsg)
            t.create_geom()
            shapes.append(t.geom)
            ews.append(point.ew)
            kk_indices.append(point.kk_index)
            kks.append(point.kk)
            cell_ids.append(point.id)

        df['id'] = cell_ids
        df['SHAPE'] = shapes
        df['ew'] = ews
        df['kk_index'] = kk_indices
        df['kk'] = kks

        self.parent_tbx.insert_dataframe_in_table('Siedlungszellen', df)

        #addLayer = arcpy.mapping.Layer(self.folders.get_table('Siedlungszellen'))
        #mxd = arcpy.mapping.MapDocument("CURRENT")
        #df = arcpy.mapping.ListDataFrames(mxd)[0]
        #arcpy.mapping.AddLayer(df, addLayer)


class TbxDistMarkets(Tbx):

    @property
    def label(self):
        return encode(u'Entfernung zwischen Supermarkt und '
                      u'Rasterzellen berechnen')

    @property
    def Tool(self):
        return DistMarkets

    def _getParameterInfo(self):

        params = self.par
        projekte = self.folders.get_projects()

        # Projekt_auswählen
        p = self.add_parameter('projectname')
        p.name = u'Projekt_auswählen'.encode('cp1252')
        p.displayName = u'Projekt auswählen'.encode('cp1252')
        p.parameterType = 'Required'
        p.direction = 'Input'
        p.datatype = u'GPString'
        p.value = self.config.active_project
        p.enabled = False

        # set square size
        p = self.add_parameter('square_size')
        p.name = u'sqare_size'.encode('cp1252')
        p.displayName = u'Größe des Bereichs wählen (km)'.encode('cp1252')
        p.parameterType = 'Required'
        p.direction = 'Input'
        p.datatype = u'GPLong'
        p.value = 20

        return params

    def _updateParameters(self, params):
        pass

if __name__ == "__main__":
    t = TbxDistMarkets()
    t.getParameterInfo()
    t.par.projectname.value = t.config.active_project
    t.execute()

    print 'done'