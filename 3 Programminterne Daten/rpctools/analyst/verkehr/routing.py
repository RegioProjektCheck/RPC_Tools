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
                              symbology_classes=(15, 'weight'))
        self.output.add_layer('verkehr', 'Zielpunkte',
                              featureclass='Zielpunkte',
                              template_folder='Verkehr',
                              name='Herkunfts-/Zielpunkte',
                              zoom=True, zoom_extent=self._extent)

    def run(self):
        # self.calculate_transfer_nodes()
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
                u"Suche Routen ausgehend von Teilfläche {}...".format(source_id))
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
                u'Suche Routen zwischen Teilfläche {}'
                u'und den Herkunfts- und Zielpunkten...'.format(source_id))
            x_coord, y_coord = shape
            connector = Point.from_xy(y=y_coord, x=x_coord,
                                      srid_proj=otp_router.p2,
                                      srid_geogr=otp_router.p1)

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
                        toolbox.insert_rows_in_table(
                            'RouteLinks',
                            {'from_node_id': from_id,
                             'to_node_id': to_id,
                             'transfer_node_id': from_id,
                             'id_teilflaeche': source_id,
                             'SHAPE': lg}
                        )


        #for i, area in enumerate(self.areas):
            #self.log(f'Suche Routen zwischen Teilfläche {area.name} und den '
                     #'Herkunfts- und Zielpunkten...')
            #connector = self.connectors.get(id_teilflaeche=area.id)
            #qpoint = connector.geom.asPoint()
            #pcon = Point(id=area.id, x=qpoint.x(), y=qpoint.y(),
                         #epsg=project_epsg)
            #pcon.transform(OTPRouter.router_epsg)
            #for transfer_node in self.transfer_nodes:
                #qpoint = transfer_node.geom.asPoint()
                #pnode = Point(id=transfer_node.id, x=qpoint.x(), y=qpoint.y(),
                              #epsg=project_epsg)
                #pnode.transform(otp_router.router_epsg)
                #out_route = otp_router.route(pcon, pnode)
                #in_route = otp_router.route(pnode, pcon)
                #for route in out_route, in_route:
                    #if not route:
                        #continue
                    #for link in route.links:
                        #geom = QgsGeometry()
                        #from_id = link.from_node.node_id
                        #to_id = link.to_node.node_id
                        #lg = link.get_geom()
                        #if from_id == to_id or not lg:
                            #continue
                        #geom.fromWkb(lg.ExportToWkb())
                        #geom.transform(transform)
                        #self.links.add(from_node_id=from_id, to_node_id=to_id,
                                       #transfer_node_id=transfer_node.id,
                                       #area_id=area.id, geom=geom)

    def calculate_traffic_load(self):
        pass

        #toolbox = self.parent_tbx
        ## tbx settings
        #inner_circle = toolbox.par.inner.value
        #mid_circle = inner_circle + 500
        #outer_circle = inner_circle + self._outer_circle
        ##arcpy.Delete_management(tmp_table)
        ## get data from Wege_je_nutzung table
        #data_wjn = toolbox.query_table('Wege_je_nutzung',
                                       #columns=['Nutzungsart', 'Wege_gesamt',
                                                #'PKW_Anteil'])
        #data_tfl = self.get_areas_data()
        #data_tfl = self.calc_trips(data_tfl, data_wjn)

        ## calculate routes
        #workspace = self.folders.get_db()
        #o = OTPRouter(workspace)
        #o.dist = inner_circle
        #r_id = 0
        #for single_tfl in data_tfl:
            #source_id, trips, tfl_use, shape = single_tfl
            #arcpy.AddMessage(
                #u"Suche Routen ausgehend von Teilfläche {}...".format(source_id))
            #x_coord, y_coord = shape
            ##if not trips:
                ##continue
            #o.areas.add_area(source_id, trips=trips)
            #source = Point.from_xy(y=y_coord, x=x_coord,
                                   #srid_proj=o.p2, srid_geogr=o.p1)

            ## calculate segments around centroid
            #inner_dest = o.create_circle(source, dist=mid_circle,
                                         #n_segments=self._n_segments)
            #outer_dest = o.create_circle(source, dist=outer_circle,
                                         #n_segments=self._n_segments)
            #destinations = np.concatenate([inner_dest, outer_dest])

            ## calculate the routes to the segments
            #for (lon, lat) in destinations:
                #destination = Point(lat, lon)
                #json = o.get_routing_request(source, destination)
                #o.decode_coords(json, route_id=r_id, source_id=source_id)
                #r_id += 1

        #o.nodes.transform()
        #o.nodes_to_graph(meters=inner_circle)
        #o.remove_redundant_routes()
        #arcpy.AddMessage("berechne Zielknoten...")
        #o.transfer_nodes.calc_initial_weight()
        #arcpy.AddMessage("berechne Gewichte...")
        #o.calc_vertex_weights()
        #o.create_polyline_features()
        #o.create_node_features()
        #o.create_transfer_node_features()
        #o.set_layer_extent()

        #self._extent = o.extent
        #o.dump(self.folders.get_otp_pickle_filename(check=False))

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
