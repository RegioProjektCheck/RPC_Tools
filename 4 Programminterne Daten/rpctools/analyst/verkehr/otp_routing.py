# -*- coding: utf-8 -*-
#

import requests
import polyline
import arcpy
import os
import numpy as np
from collections import OrderedDict
from scipy.sparse import csc_matrix
from pyproj import Proj, transform
from  scipy.sparse.csgraph import dijkstra



class Route(object):
    """Route to a destination"""

    def __init__(self, route_id, source_id):
        """
        Parameters
        ----------
        route_id : int
        """
        self.route_id = route_id
        self.source_id = source_id
        self.node_ids = np.array([], dtype='i4')

    @property
    def source_node(self):
        if not len(self.node_ids):
            return None
        return self.node_ids[0]


class Routes(OrderedDict):
    """Routes-object"""

    def get_route(self, route_id, source_id):
        """
        (add and) get route with given route_id

        Parameters
        ----------
        route_id : int

        source_id : int

        Returns
        -------
        route
        """
        route = self.get(route_id)
        if route is None:
            route = Route(route_id, source_id)
            self[route_id] = route
        return route

    @property
    def source_nodes(self):
        """
        Return the source nodes of the routes

        Returns
        -------
        np.array()
        """
        return np.unique(np.array([n.source_node
                         for n in self.itervalues()], dtype='i4'))


class TransferNodes(OrderedDict):
    """TransferNodes-object"""

    def get_node(self, node, route):
        """
        (add and) get transfer_node with given node_id

        Parameters
        ----------
        node

        route

        Returns
        -------
        transfer_node
        """
        transfer_node = self.get(node.node_id)
        if transfer_node is None:
            transfer_node = TransferNode(node)
            self[node.node_id] = transfer_node
        transfer_node.routes[route.route_id] = route
        return transfer_node

    @property
    def total_weights(self):
        """Total weights of all transfer nodes"""
        return float(sum((tn.weight for tn in self.itervalues())))

    def calc_initial_weight(self):
        """calculate the initial weight based upon the number of routes"""
        for tn in self.itervalues():
            tn.calc_initial_weight()
        total_weights = self.total_weights
        for tn in self.itervalues():
            tn.weight /= total_weights
            route_weight = tn.weight / tn.n_routes
            for route in tn.routes.itervalues():
                route.weight = route_weight


class Nodes(object):
    """Nodes"""
    def __init__(self, epsg=31467):
        self.dtype = np.dtype(dict(names=['node_id', 'lat', 'lon', 'x', 'y'],
                                   formats=['i4', 'd', 'd', 'd', 'd']))
        self.epsg = epsg
        self.p1 = Proj(init='epsg:4326')
        self.p2 = Proj(init='epsg:{}'.format(self.epsg))
        self.coords2nodes = OrderedDict()
        self.id2nodes = OrderedDict()
        self.serial = 0
        self.links = Links()

    def add_points(self, coord_list, route):
        """
        Add Nodes, create link and add route_id to link

        Parameters
        ----------
        coord_list : list of tuple of floats

        route : int

        """
        last_node = None
        node_ids = []
        for coords in coord_list:
            node = self.get_or_set_node_from_coord(coords)
            if last_node:
                link = self.links.add_vertex(last_node, node)
                link.add_route(route.route_id)
            last_node = node
            node_ids.append(node.node_id)
        route.node_ids = np.array(node_ids, dtype='i4')

    def get_or_set_node_from_coord(self, coords):
        """
        get an existing node or add a new node from given coordinates

        Parameters
        ----------
        coords : tuple(float, float)
            (lat, lon)

        Returns
        -------
        node : Point-instance
        """
        node = self.coords2nodes.get(coords)
        if node is None:
            node = Point(*coords)
            node.node_id = self.serial
            self.coords2nodes[coords] = node
            self.id2nodes[node.node_id] = node
            self.serial += 1
        return node

    def get_id(self, point):
        """"""
        node_id = self.coords2nodes[(point.lat, point.lon)]
        return self.get_node(node_id)

    def get_node(self, node_id):
        """"""
        return self.id2nodes[node_id]

    @property
    def node_ids(self):
        return self.id2nodes.keys()

    @property
    def nodes(self):
        points = self.id2nodes.values()
        if points:
            ret = np.rec.fromrecords([(p.node_id, p.lat, p.lon, p.x, p.y)
                                      for p in points],
                                     dtype=self.dtype)
        else:
            ret = np.rec.array(np.empty((0, ), dtype=self.dtype))
        return ret

    def transform(self):
        """Transform"""
        x, y = transform(self.p1, self.p2, self.nodes.lon, self.nodes.lat)
        for i, node in enumerate(self):
            node.x = x[i]
            node.y = y[i]

    def __iter__(self):
        """Iterator"""
        return iter(self.id2nodes.itervalues())

    def __len__(self):
        return len(self.id2nodes)


class Point(object):
    """A Point object"""
    __slots__ = ['lat', 'lon', 'x', 'y', 'node_id', 'geom']
    def __init__(self, lat, lon, node_id=None, x=None, y=None):
        self.lat = lat
        self.lon = lon
        self.node_id = node_id
        self.x = x
        self.y = y
        self.geom = None

    def __repr__(self):
        return '{},{}'.format(self.lat, self.lon)

    def __hash__(self):
        return hash((self.lat, self.lon))

    def create_geom(self):
        """Create geometry from coordinates"""
        geom = arcpy.Point(self.x, self.y)
        self.geom = geom



class TransferNode(Point):
    """"""
    def __init__(self, node):
        self.lat = node.lat
        self.lon = node.lon
        self.node_id = node.node_id
        self.x = node.x
        self.y = node.y
        self.routes = Routes()
        self.weight = 0.0
        self.geom = None

    @property
    def n_routes(self):
        return len(self.routes)

    def calc_initial_weight(self):
        """calculate the initial weight based upon the number of routes"""
        self.weight = float(self.n_routes)


class Links(object):
    """all links"""
    def __init__(self):
        self.node_ids2link = OrderedDict()
        self.id2link = OrderedDict()
        self.serial = 0

    def __iter__(self):
        return iter(self.node_ids2link.itervalues())

    def add_vertex(self, node1, node2):
        """"""
        node_ids = (node1.node_id, node2.node_id)
        link = self.node_ids2link.get(node_ids)
        if link is None:
            link = Link(node1, node2, self.serial)
            self.node_ids2link[node_ids] = link
            self.id2link[link.link_id] = link
            self.serial += 1
        return link

    def get_id(self, node_ids):
        """"""
        return self.node_ids2link[node_ids]

    def get_node(self, vertex_id):
        """"""
        return self.id2link[vertex_id]

    @property
    def vertex_ids(self):
        return self.id2link.keys()

    @property
    def node_ids(self):
        return np.rec.fromrecords([l.node_ids
                                   for l in self],
                                  names=['from_node', 'to_node'])

    def __len__(self):
        return len(self.id2link)

    @property
    def link_length(self):
        return np.array([l.length for l in self])


class Link(object):
    """A Vertex"""
    def __init__(self, node1, node2, vertex_id):
        self.node1 = node1
        self.node2 = node2
        self.link_id = vertex_id
        self.routes = set()
        self.weight = 0.0
        self.geom = None
        self.distance_from_source = 9999999

    def __repr__(self):
        return '->'.join([repr(self.node1), repr(self.node2)])

    def __hash__(self):
        return hash(((self.node1.x, self.node1.y),
                     (self.node2.x, self.node2.y)))

    @property
    def length(self):
        meter = np.sqrt((self.node2.x - self.node1.x) ** 2 +
                         (self.node2.y - self.node1.y) **2)
        return meter

    @property
    def node_ids(self):
        return (self.node1.node_id, self.node2.node_id)

    def add_route(self, route_id):
        """add route_id to route"""
        self.routes.add(route_id)

    def create_geom(self):
        """Create polyline from geometry"""
        if self.length:
            n1 = self.node1
            n2 = self.node2
            coord_list = [(n1.y, n1.x), (n2.y, n2.x)]
            geom = arcpy.Polyline(
                arcpy.Array([arcpy.Point(coords[1], coords[0])
                             for coords in coord_list]))
            self.geom = geom


class OTPRouter(object):
    def __init__(self, epsg=31467):
        self.url = r'https://rpcrouting.ggr-planung.de/otp/routers/hvv_car/plan'
        self.ws = r'C:\Dev\RPC_Tools\4 Programminterne Daten\templates\Template\FGDB_Verkehr.gdb'
        self.router = 'hvv_car'
        self.epsg = epsg
        self.p1 = Proj(init='epsg:4326')
        self.p2 = Proj(init='epsg:{}'.format(self.epsg))
        self.nodes = Nodes(epsg)
        self.polylines = []
        self.routes = Routes()
        self.transfer_nodes = TransferNodes()

    def get_routing_request(self, source, destination, mode='CAR'):
        """
        get a routing requset for route from source to destination

        Parameters
        ----------
        source : Point
        destination : Point
        mode : str, optional (default='CAR')

        Returns
        -------
        json
        """
        params = dict(routerId=self.router,
                      fromPlace=source,
                      toPlace=destination,
                      mode=mode)
        r = requests.get(self.url, params=params)
        return r.json()

    def decode_coords(self, json, route_id, source_id=0):
        """
        Parse the geometry from a json

        Parameters
        ----------
        json : json-instance

        route_id : int

        source_id : int, optional(default=0)
        """
        try:
            itinerary = json['plan']['itineraries'][0]
        except KeyError:
            return
        leg = itinerary['legs'][0]
        points = leg['legGeometry']['points']
        coord_list = polyline.decode(points)
        route = self.routes.get_route(route_id, source_id)
        self.nodes.add_points(coord_list, route)

    def coord_list2polyline(self, coord_list):
        """
        create arcpy.Polyline from list of coordinates
        and append to polylines list

        Parameters
        ----------
        coord_list : list of tuples of coordinates


        """
        if not len(coord_list):
            return None
        geom = arcpy.Polyline(
            arcpy.Array([arcpy.Point(coords[1], coords[0])
                         for coords in coord_list]))
        self.polylines.append(geom)

    def insert_polyline(self, fc):
        """
        Insert polylines to fc

        Parameters
        ----------
        fc : str
            the path of the feature-class

        """
        sr = arcpy.SpatialReference(4326)
        fields = ['source', 'destination', 'SHAPE@']
        with arcpy.da.InsertCursor(fc, fields) as rows:
            for dest, geom in enumerate(self.polylines):
                if geom:
                    rows.insertRow((1, dest, geom))

    def create_circle(self, source, dist=1000, n_segments=20):
        """
        Create a circle around source in a given distance
        and with the given number of segments

        Parameters
        ----------
        source : Point-instance

        dist : float
            the distance around the point

        n_segments : int
            the number of segments of the (nearly) circle

        """
        source_x, source_y = transform(self.p1, self.p2,
                                       source.lon, source.lat)
        angel = np.linspace(0, np.pi*2, n_segments)
        x = source_x + dist * np.cos(angel)
        y = source_y + dist * np.sin(angel)
        lon, lat = transform(self.p2, self.p1, x, y)
        destinations = np.vstack([lon, lat]).T

        return destinations

    def get_max_node_for_route(self, dist_vector, route_id):
        """
        get the max distant node for a given route_id

        Parameters
        ----------
        dist_vector
        route_id : int

        Returns
        -------
        transfer_node : Node
        """
        route = self.routes[route_id]
        route_nodes = route.node_ids
        route_dist_vector = dist_vector[route_nodes]

        idx = np.argmax(route_dist_vector)
        node_id = route_nodes[idx]
        node = self.nodes.get_node(node_id)
        transfer_node = self.transfer_nodes.get_node(node, route)
        transfer_node.dist = route_dist_vector[idx]
        print('Route {}: node {} {} {} at {} meters'.format(route_id,
                                                      transfer_node.node_id,
                                                      transfer_node.lat,
                                                      transfer_node.lon,
                                                      transfer_node.dist))
        return transfer_node

    def get_max_nodes(self, dist_vector):
        """
        """
        # for several Teilflächen: use the maximum to one of the origins
        for route in self.routes.itervalues():
            transfer_node = self.get_max_node_for_route(dist_vector,
                                                        route.route_id)

    def nodes_to_graph(self, meters=600):
        """Convert nodes and links to graph"""
        data = self.nodes.links.link_length
        node_ids = self.nodes.links.node_ids
        row = node_ids.from_node
        col = node_ids.to_node
        N = len(self.nodes)
        mat = csc_matrix((data, (row, col)), shape=(N, N))
        source_nodes = self.routes.source_nodes
        dist_matrix = dijkstra(mat,
                                    directed=True,
                                    return_predecessors=False,
                                    indices=self.routes.source_nodes,
                                    #limit=meters,
                                    )
        dist_vector = dist_matrix.min(axis=0)
        self.set_link_distance(dist_vector)
        dist_vector[dist_vector > meters] = np.NINF
        self.get_max_nodes(dist_vector)

    def set_link_distance(self, dist_vector):
        """set distance to plangebiet for each link"""
        for link in self.nodes.links:
            node_id = link.node2.node_id
            dist = dist_vector[node_id]
            link.distance_from_source = dist


    def calc_vertex_weights(self):
        """calc weight of link"""
        for link in self.nodes.links:
            link.weight = 0.
            for route_id in link.routes:
                route = self.routes[route_id]
                route_weight = route.weight
                link.weight += route_weight

    def create_polyline_features(self):
        """Create the polyline-features from the links"""
        sr = arcpy.SpatialReference(self.epsg)
        fields = ['link_id', 'weight', 'distance_from_source', 'SHAPE@']

        fc = os.path.join(self.ws, 'links')
        self.truncate(fc)
        with arcpy.da.InsertCursor(fc, fields) as rows:
            for link in self.nodes.links:
                link.create_geom()
                if link.geom:
                    rows.insertRow((link.link_id, link.weight,
                                    link.distance_from_source, link.geom))

    def create_transfer_node_features(self):
        """Create the point-features from the transfer nodes"""
        sr = arcpy.SpatialReference(self.epsg)
        fields = ['node_id', 'Gewicht_Bewohnerverkehr',
                  'Gewicht_Beschäftigte', 'Gewicht_Kunden',
                  'SHAPE@']
        fc = os.path.join(self.ws, 'Zielpunkte')
        self.truncate(fc)

        with arcpy.da.InsertCursor(fc, fields) as rows:
            for node in self.transfer_nodes.itervalues():
                node.create_geom()
                if node.geom:
                    rows.insertRow((node.node_id,
                                    node.weight,
                                    node.weight,
                                    node.weight,
                                    node.geom))

    def truncate(self, fc):
        """
        Truncate the table

        Parameters
        ----------
        fc : str
            the table to truncate
        """
        arcpy.TruncateTable_management(in_table=fc)
        #with arcpy.da.UpdateCursor(fc, "OID@") as rows:
            #for row in rows:
                #row.deleteRow()


    def create_node_features(self):
        """Create the point-features from all nodes"""
        sr = arcpy.SpatialReference(self.epsg)
        fields = ['node_id',
                  'SHAPE@']
        fc = os.path.join(self.ws, 'nodes')
        self.truncate(fc)
        with arcpy.da.InsertCursor(fc, fields) as rows:
            for node in self.nodes:
                node.create_geom()
                if node.geom:
                    rows.insertRow((node.node_id,
                                    node.geom))



if __name__ == '__main__':
    o = OTPRouter()
    source = Point(lat=53.5, lon=9.589)
    source_id = 0
    destinations = o.create_circle(source, dist=1000, n_segments=36)
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

