# -*- coding: utf-8 -*-
#

import arcpy
import os
from rpctools.utils.params import Tool
from rpctools.analyst.verkehr.otp_router import Point, OTPRouter
import pandas as pd
import numpy as np


class Routing(Tool):
    _workspace = 'FGDB_Verkehr.gdb'
    _param_projectname = 'project'
    _outer_circle = 2000
    _n_segments = 24
    _extent = (0.0, 0.0, 0.0, 0.0)

    def add_outputs(self):
        # Add Layers
        self.output.add_layer('projektdefinition', 'Anbindungspunkte',
                              featureclass='Anbindungspunkte',
                              template_folder='Verkehr', zoom=False)
        self.output.add_layer('verkehr', 'links',
                              featureclass='Verkehrsbelastung',
                              template_folder='Verkehr',
                              name='Zusätzliche PKW-Fahrten', zoom=False,
                              symbology_classes=(15, 'trips'))
        self.output.add_layer('verkehr', 'Zielpunkte',
                              featureclass='Zielpunkte',
                              template_folder='Verkehr',
                              name='Herkunfts-/Zielpunkte',
                              zoom=True, zoom_extent=self._extent)

    def run(self):
        self.calculate_transfer_nodes()
        self.route_transfer_nodes()
        self.calculate_traffic_load()

    def calculate_transfer_nodes(self):
        '''
        calculate the position and weights of the initial transfer nodes
        '''
        toolbox = self.parent_tbx
        # tbx settings
        inner_circle = toolbox.par.inner.value
        mid_circle = inner_circle + 500
        outer_circle = inner_circle + self._outer_circle

        data_tfl = self.get_areas_data()

        # calculate routes
        otp_router = OTPRouter(distance=inner_circle)

        for source_id, trips, tfl_use, shape in data_tfl:
            arcpy.AddMessage(
                u'Suche Routen ausgehend von Teilfläche {}...'
                .format(source_id))
            x_coord, y_coord = shape
            source = Point.from_xy(y=y_coord, x=x_coord,
                                   srid_proj=otp_router.p2,
                                   srid_geogr=otp_router.p1)

            # calculate segments around centroid
            inner_dest = otp_router.create_circle(source, dist=mid_circle,
                                                  n_segments=self._n_segments)
            outer_dest = otp_router.create_circle(source, dist=outer_circle,
                                                  n_segments=self._n_segments)
            destinations = np.concatenate([inner_dest, outer_dest])

            # calculate the routes to the segments
            for (lon, lat) in destinations:
                destination = Point.from_xy(y=lat, x=lon,
                                            srid_proj=otp_router.p2,
                                            srid_geogr=otp_router.p1)
                otp_router.route(source, destination)

        otp_router.build_graph(distance=inner_circle)
        otp_router.remove_redundancies()

        arcpy.AddMessage('Berechne Herkunfts- und Zielpunkte aus den Routen...')
        otp_router.transfer_nodes.calc_initial_weight()
        df_transfer_nodes = otp_router.get_transfer_node_features()
        table = 'Zielpunkte'
        toolbox.delete_rows_in_table(table)
        toolbox.insert_dataframe_in_table(table, df_transfer_nodes)

    def route_transfer_nodes(self):
        '''
        routing between transfer nodes and area connectors
        '''

        toolbox = self.parent_tbx
        toolbox.delete_rows_in_table('RouteLinks')
        data_tfl = self.get_areas_data()
        otp_router = OTPRouter()
        transfer_nodes = toolbox.query_table(
            'Zielpunkte', columns=['node_id', 'SHAPE'])

        for source_id, trips, tfl_use, shape in data_tfl:
            arcpy.AddMessage(
                u'Suche Routen zwischen Teilfläche {} '
                u'und den Herkunfts- und Zielpunkten...'.format(source_id))
            x_coord, y_coord = shape
            connector = Point.from_xy(y=y_coord, x=x_coord,
                                      srid_proj=otp_router.p2,
                                      srid_geogr=otp_router.p1)
            from_ids = []
            to_ids = []
            tn_ids = []
            shapes = []
            for tn_id, shape in transfer_nodes:
                x_coord, y_coord = shape
                destination = Point.from_xy(y=y_coord, x=x_coord,
                                            srid_proj=otp_router.p2,
                                            srid_geogr=otp_router.p1)
                out_route = otp_router.route(connector, destination)
                in_route = otp_router.route(destination, connector)
                otp_router.nodes.transform()
                for route in out_route, in_route:
                    if not route:
                        continue
                    for link in route.links:
                        from_id = link.from_node.node_id
                        to_id = link.to_node.node_id
                        lg = link.get_geom()
                        if from_id == to_id or not lg:
                            continue
                        from_ids.append(from_id)
                        to_ids.append(to_id)
                        tn_ids.append(tn_id)
                        shapes.append(lg)

            toolbox.insert_rows_in_table(
                'RouteLinks',
                {'from_node_id': from_ids,
                 'to_node_id': to_ids,
                 'transfer_node_id': tn_ids,
                 'id_teilflaeche': [source_id] * len(from_ids),
                 'SHAPE@': shapes}
            )

    def calculate_traffic_load(self):

        toolbox = self.parent_tbx
        toolbox.delete_rows_in_table('Verkehrsbelastung')

        arcpy.AddMessage('Verteile das Verkehrsaufkommen...')

        data_wjn = toolbox.query_table('Wege_je_nutzung',
                                       columns=['Nutzungsart', 'Wege_gesamt',
                                                'PKW_Anteil'])
        df_links = toolbox.table_to_dataframe(
            'RouteLinks', columns=['from_node_id', 'to_node_id',
                                   'transfer_node_id', 'id_teilflaeche',
                                   'SHAPE@'])
        df_links['wege_miv'] = 0

        data_tfl = self.calc_trips(self.get_areas_data(), data_wjn)
        for source_id, trips, tfl_use, shape in data_tfl:
            idx = df_links['id_teilflaeche'] == source_id
            df_links.loc[idx, 'wege_miv'] = trips

        df_transfer = toolbox.table_to_dataframe(
            'Zielpunkte', columns=['node_id', 'weight'])
        df_weighted = df_links.merge(
                df_transfer, how='left', left_on='transfer_node_id',
                right_on='node_id')
        # ways include back and forth
        df_weighted['wege_miv'] /= 2
        df_weighted['weight'] /= 100
        df_weighted['trips'] = df_weighted['wege_miv'] * df_weighted['weight']
        # linked nodes without direction
        df_weighted['dirless'] = ['{}-{}'.format(*sorted(t))
                                      for t in zip(df_weighted['from_node_id'],
                                                   df_weighted['to_node_id'])]
        df_grouped = df_weighted.groupby('dirless')
        trips = []
        shapes = []
        for i, group in df_grouped:
            trips.append(group['trips'].sum())
            shapes.append(group['SHAPE@'].values[0])

        toolbox.insert_rows_in_table('Verkehrsbelastung',
                                     {'trips': trips, 'SHAPE@': shapes})

    def get_areas_data(self):
        """
        Get data from areas and merge with table for attachement points
        """
        toolbox = self.parent_tbx
        # create tmp_table for transforming from gauss-krüger to 4326
        tfl_table = 'Teilflaechen_Plangebiet'
        tfl_ws = 'FGDB_Definition_Projekt.gdb'
        tfl_df = toolbox.table_to_dataframe(tfl_table,
                                            columns=['id_teilflaeche',
                                                     'Wege_gesamt',
                                                     'Nutzungsart'],
                                            workspace=tfl_ws)
        source_table = 'Anbindungspunkte'
        source_ws = 'FGDB_Verkehr.gdb'
        source_df = toolbox.table_to_dataframe(source_table,
                                               columns=['id_teilflaeche',
                                                        'Shape'],
                                               workspace=source_ws)
        areas_data = tfl_df.merge(source_df, left_on='id_teilflaeche',
                                  right_on='id_teilflaeche', how='left')

        return areas_data.as_matrix()

    def calc_trips(self, data_tfl, data_wjn):
        """
        Calculate the trips from an area and update to data_tfl
        """
        for i in range(len(data_wjn)):
            tou = data_wjn[i][0]  # type of use
            # trips * %cars
            trips_by_car = data_wjn[i][1] * data_wjn[i][2] / 100
            tfl_id_with_tou = []
            total_trips_for_tou = 0
            for j in range(len(data_tfl)):
                source_id, trips, tfl_use, shape = data_tfl[j]
                if tou == tfl_use:
                    tfl_id_with_tou.append(j)
                    total_trips_for_tou += trips
            for tfl_id in tfl_id_with_tou:
                source_id, trips, tfl_use, shape= data_tfl[tfl_id]
                trips = trips_by_car * trips / total_trips_for_tou \
                    if total_trips_for_tou else 0
                data_tfl[tfl_id] = (source_id, trips, tfl_use, shape)
        return data_tfl
