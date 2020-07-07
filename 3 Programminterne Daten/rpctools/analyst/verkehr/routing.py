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
        self.output.add_layer('verkehr', 'Anbindungspunkte',
                              featureclass='Anbindungspunkte',
                              template_folder='Verkehr', zoom=False)
        self.output.add_layer('verkehr', 'links',
                              featureclass='links',
                              template_folder='Verkehr',
                              name='Zusätzliche PKW-Fahrten', zoom=False,
                              symbology_classes=(15, 'weight'))
        self.output.add_layer('verkehr', 'Zielpunkte',
                              featureclass='Zielpunkte',
                              template_folder='Verkehr',
                              name='Herkunfts-/Zielpunkte',
                              zoom=True, zoom_extent=self._extent)

    def run(self):
        toolbox = self.parent_tbx
        # tbx settings
        inner_circle = toolbox.par.inner.value
        mid_circle = inner_circle + 500
        outer_circle = inner_circle + self._outer_circle
        #arcpy.Delete_management(tmp_table)
        # get data from Wege_je_nutzung table
        data_wjn = toolbox.query_table('Wege_je_nutzung',
                                       columns=['Nutzungsart', 'Wege_gesamt',
                                                'PKW_Anteil'])
        data_tfl = self.get_areas_data()
        data_tfl = self.calc_trips(data_tfl, data_wjn)

        # calculate routes
        workspace = self.folders.get_db()
        o = OTPRouter(workspace)
        o.dist = inner_circle
        r_id = 0
        for single_tfl in data_tfl:
            source_id, trips, tfl_use, shape = single_tfl
            arcpy.AddMessage(
                u"Suche Routen ausgehend von Teilfläche {}...".format(source_id))
            x_coord, y_coord = shape
            #if not trips:
                #continue
            o.areas.add_area(source_id, trips=trips)
            # ? lat = y lon = x
            source = Point.from_xy(y=y_coord, x=x_coord,
                                   srid_proj=o.p2, srid_geogr=o.p1)  # centroid

            # calculate segments around centroid
            inner_dest = o.create_circle(source, dist=mid_circle,
                                         n_segments=self._n_segments)
            outer_dest = o.create_circle(source, dist=outer_circle,
                                         n_segments=self._n_segments)
            destinations = np.concatenate([inner_dest, outer_dest])

            # calculate the routes to the segments
            for (lon, lat) in destinations:
                destination = Point(lat, lon)
                json = o.get_routing_request(source, destination)
                o.decode_coords(json, route_id=r_id, source_id=source_id)
                r_id += 1

        o.nodes.transform()
        o.nodes_to_graph(meters=inner_circle)
        o.remove_redundant_routes()
        arcpy.AddMessage("berechne Zielknoten...")
        o.transfer_nodes.calc_initial_weight()
        arcpy.AddMessage("berechne Gewichte...")
        o.calc_vertex_weights()
        o.create_polyline_features()
        o.create_node_features()
        o.create_transfer_node_features()
        o.set_layer_extent()

        self._extent = o.extent
        o.dump(self.folders.get_otp_pickle_filename(check=False))

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

if __name__ == '__main__':
    o = OTPRouter(r'C:\Users\ggr\Desktop\RPC Projekte\neu\FGDB_Verkehr.gdb')
    source = Point(lat=53.32, lon=9.83)
    source_id = 0
    destinations = o.create_circle(source, dist=1000, n_segments=12)
    o.dist = 1000
    for d, (lon, lat) in enumerate(destinations):
        destination = Point(lat, lon)
        print d,
        json = o.get_routing_request(source, destination)
        o.decode_coords(json, route_id=d, source_id=source_id)

    max_d = d
    source = Point(lat=53.502, lon=9.587)
    source_id = 1
    for d, (lon, lat) in enumerate(destinations):
        destination = Point(lat, lon)
        json = o.get_routing_request(source, destination)
        o.decode_coords(json, route_id=d+max_d, source_id=source_id)

    o.nodes.transform()
    o.nodes_to_graph()
    o.transfer_nodes.calc_initial_weight()
    o.calc_vertex_weights()
    o.create_polyline_features()
    o.create_node_features()
    o.create_transfer_node_features()
    o.set_layer_extent()
    print(o.extent)
