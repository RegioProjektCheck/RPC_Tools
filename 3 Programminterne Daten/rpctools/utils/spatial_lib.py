import arcpy
from rpctools.utils.params import Folders
from rpctools.utils.params import DummyTbx
from rpctools.utils.output import ArcpyEnv
from pyproj import Proj, transform

import requests
import numpy as np
from os.path import join, split
import sys

def remove_duplicates(features, id_field, match_field='', where='', distance=100):
    '''remove point features matched by where clause from the given feature-class
    if other features are within given distance
    match_field - optional, only delete feature, if points within distance have
                  same value in this field
    '''
    add = match_field or id_field
    fields =  [id_field, 'SHAPE', add]
    cursor = arcpy.da.SearchCursor(features, fields)
    all_r = [(id, point, mf) for id, point, mf in cursor]
    if len(all_r) == 0:
        return 0
    ids, points, mfs = zip(*all_r)
    del(cursor)
    ids = np.array(ids)
    points = np.array(points)
    mfs = np.array(mfs)
    cursor = arcpy.da.UpdateCursor(features, fields, where)
    n_duplicates = 0
    for id, point, mf in cursor:
        p_within, indices = points_within(point, points, distance)
        sub_ids = ids[indices]
        sub_mfs = mfs[indices]
        for p, pid, pmf in zip(p_within, sub_ids, sub_mfs):
            if id == pid:
                continue
            if match_field and mf != pmf:
                continue
            cursor.deleteRow()
            n_duplicates += 1
            break
    return n_duplicates

def features_to_raster(feature_class, outfile, field, template=None,
                       transform_method=None,
                       where=''):
    '''convert a feature-class to a raster-file

    template : str, optional
        full path to template raster, outfput file will get same projection and
        raster size
    '''
    with ArcpyEnv(addOutputsToMap=False):
        proj_tmp = join(arcpy.env.scratchGDB, 'proj_tmp')
        where_tmp = join(arcpy.env.scratchGDB, 'where_tmp')
        arcpy.Delete_management(where_tmp)
        arcpy.Delete_management(proj_tmp)
        in_features = arcpy.FeatureClassToFeatureClass_conversion(
            feature_class, *split(where_tmp), where_clause=where)
        if template:
            desc = arcpy.Describe(template)
            sr = desc.spatialReference
            in_features = arcpy.Project_management(
                in_features, proj_tmp, sr, transform_method=transform_method)
        arcpy.FeatureToRaster_conversion(in_features, field, outfile,
                                         cell_size=template)
        arcpy.Delete_management(where_tmp)
        arcpy.Delete_management(proj_tmp)
    return outfile

def get_project_epsg():
    mxd = arcpy.mapping.MapDocument("CURRENT")
    df = arcpy.mapping.ListDataFrames(mxd)[0]
    epsg = df.spatialReference.factoryCode
    return epsg

def from_project_srid(x, y, target_srid):
    project_epsg = get_project_epsg()
    # no project -> keep projection
    if not project_epsg:
        return (x, y)
    point = Point(x, y, epsg=project_epsg)
    return point.transform(target_srid)

def to_project_srid(x, y, srid):
    project_epsg = get_project_epsg()
    # no project -> keep projection
    if not project_epsg:
        return (x, y)
    point = Point(x, y, epsg=srid)
    return point.transform(project_epsg)


class Point(object):
    """A Point object"""
    __slots__ = ['x', 'y', 'id', 'geom', 'epsg', 'proj']
    def __init__(self, x, y, id=None, epsg=4326):
        self.id = id
        self.x = x
        self.y = y
        self.geom = None
        self.epsg = epsg
        self.proj = Proj(init='epsg:{}'.format(epsg))

    def __repr__(self):
        return '{},{}'.format(self.x, self.y)

    def __hash__(self):
        return hash((self.x, self.y))

    def create_geom(self):
        """Create geometry from coordinates"""
        geom = arcpy.Point(self.x, self.y)
        self.geom = geom

    def transform(self, target_srid):
        target_srs = Proj(init='epsg:{}'.format(target_srid))
        x, y = transform(self.proj, target_srs, self.x, self.y)
        self.epsg = target_srid
        self.proj = Proj(init='epsg:{}'.format(self.epsg))
        self.x = x
        self.y = y
        return (x, y)


def extent_to_bbox(self, extent, epsg, boundary_size = 0.00):
    '''return a square bounding box with given centroid in center and dimension
    of size x size, tuple of lower left and upper right Point'''
    xmin, ymin, xmax, ymax = extent
    boundary = boundary_size
    p1 = Point(xmin - boundary, ymin - boundary, epsg=epsg)
    p2 = Point(xmax + boundary, ymax + boundary, epsg=epsg)
    bbox = (p1, p2)

    return bbox

def minimal_bounding_poly(in_features, where=''):
    """get a bounding multipart geometry around the given features

    Parameters
    ----------
    in_features : str
        full path to input features
    iout_features : str
        full path to output features
    where : str, optional
        where clause

    Returns
    -------
    polygon : arcpy.Polygon
    """
    ws_tmp = arcpy.env.scratchGDB
    feat_tmp = join(ws_tmp, 'feat_tmp')
    feat_single = join(ws_tmp, 'feat_single')
    feat_minimal = join(ws_tmp, 'feat_minimal')
    out_union = join(ws_tmp, 'out_union')
    out_features = join(ws_tmp, 'out')
    #arcpy.Delete_management(ws_tmp)
    def del_tmp():
        for f in [feat_tmp, feat_single, feat_minimal, out_features, out_union]:
            arcpy.Delete_management(f)
    del_tmp()
    arcpy.FeatureClassToFeatureClass_conversion(
        in_features, ws_tmp, split(feat_tmp)[1],
        where_clause=where)
    arcpy.MultipartToSinglepart_management(feat_tmp, feat_single)
    arcpy.MinimumBoundingGeometry_management(feat_single, feat_minimal,
                                             "RECTANGLE_BY_AREA", "NONE")
    arcpy.Union_analysis(feat_minimal, out_union, gaps="NO_GAPS")
    arcpy.Dissolve_management(out_union, out_features, "", "",
                              "MULTI_PART", "DISSOLVE_LINES")
    #arcpy.FillGaps_production(out_features)
    cursor = arcpy.da.SearchCursor(out_features, ['SHAPE@'])
    polygon = cursor.next()[0]
    del(cursor)

    del_tmp()
    return polygon

def google_geocode(address, api_key=''):
    url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {'sensor': 'false', 'address': address}
    if api_key:
        params['key'] = api_key
    r = requests.get(url, params=params)
    json = r.json()
    results = json['results']
    msg = json['status'] if json.has_key('status') else ''
    if not results:
        if json.has_key('error_message'):
            msg = json['error_message']
        return None, msg
    location = results[0]['geometry']['location']
    return (location['lat'], location['lng']), msg

def closest_point(point, points):
    """get the point out of given points that is closest to the given point,
    points have to be passed as tuples of x, y (z optional) coordinates

    Parameters
    ----------
    point : tuple
        x, y (, z) coordinates of point
    points : list of tuples
        x, y (, z) coordinates of points to pick closest one to point from

    Returns
    -------
    index : int
        index of closest point in points
    point : tuple
        x, y of closest point
    """
    distances = _get_distances(point, points)
    closest_idx = distances.argmin()
    return closest_idx, tuple(points[closest_idx])

def points_within(center_point, points, radius):
    """get the points within a radius around a given center_point,
    points have to be passed as tuples of x, y (z optional) coordinates

    Parameters
    ----------
    center_point : tuple or Point
        x, y (, z) coordinates of center-point of circle
    points : list of tuples or list of Points
        x, y (, z) coordinates of points
    radius : int
        radius of circle,
        metric depends on projection of points (e.g. meter if Gauss-Krueger)

    Returns
    -------
    points : list of tuples
        points within radius
    indices : list of bool
        True if point is wihtin radius
    """
    distances = _get_distances(center_point, points)
    is_within = distances <= radius
    return np.array(points)[is_within], is_within

def _get_distances(point, points):
    points = [np.array(p) for p in points]
    diff = np.array(points) - np.array(point)
    distances = np.apply_along_axis(np.linalg.norm, 1, diff)
    return distances

# cancelled: distance calculation is arcpro only
#def get_points_in_radius(table, center, radius):
    #fc_center = 'in_memory/center'
    #fc_radius = 'in_memory/radius'
    #from rpctools.utils.config import Config
    #x, y = center
    ##c = Point(x, y, epsg=Config().epsg)
    ##c.transform(4326)
    ##arcpy.CopyFeatures_management([arcpy.Point(c.y, c.x)], fc_center)
    #arcpy.CreateFeatureclass_management(
        #"in_memory", "center", "POINT")
    #cursor = arcpy.da.InsertCursor(fc_center, ["SHAPE"])
    #cursor.insertRow([arcpy.Point(x, y)])
    #del(cursor)
    #cursor = arcpy.da.SearchCursor(fc_center, ['*'])
    #for row in cursor:
        #print(row)

    #arcpy.PointDistance_analysis(fc_center, table, search_radius=35)
    #cursor = arcpy.da.SearchCursor(fc_clipped, ['SHAPE@', 'GEN', 'AGS'])

def clip_raster(in_file, out_file, bbox):

    desc = arcpy.Describe(in_file)
    sr = desc.spatialReference
    srid = sr.factoryCode
    p1, p2 = bbox
    p1.transform(srid)
    p2.transform(srid)
    arcpy.Clip_management(
        in_file,
        "{x_min} {y_min} {x_max} {y_max}".format(
            x_min=p1.x, y_min=p1.y,
            x_max=p2.x, y_max=p2.y),
        out_file)
    return srid

def get_project_centroid(projectname):
    """get the centroid of the defined areas of the given project
    (projection is defined by project)"""
    tbx = DummyTbx()
    tbx.set_active_project(projectname)
    flaechen_df = tbx.table_to_dataframe(
        'Teilflaechen_Plangebiet',
        columns=['INSIDE_X', 'INSIDE_Y'],
        workspace='FGDB_Definition_Projekt.gdb')
    x = flaechen_df['INSIDE_X'].mean()
    y = flaechen_df['INSIDE_Y'].mean()
    return x, y

def get_ags(features, id_column, match_option='HAVE_THEIR_CENTER_IN', join_operation='JOIN_ONE_TO_ONE', where=None):
    """
    get the ags and names of the areas the centroids of all polygons in given
    feature table or layer lie in, the bkg_gemeinden table is taken as a source
    for ags and names

    Parameters
    ----------
    features : str
        a feature table
    id_column : str
        the name of the column containing the unique ids of the features

    Returns
    -------
    ags_res : dict
        keys are the ids of the features with tuples of (ags, gen) as values
    """
    with ArcpyEnv(addOutputsToMap=False):
        folders = Folders()
        gemeinden = folders.get_base_table('FGDB_Basisdaten_deutschland.gdb',
                                           'bkg_gemeinden')
        tmp_table = join(arcpy.env.scratchGDB, 'tmp_join')
        if arcpy.Exists(tmp_table):
            arcpy.Delete_management(tmp_table)

        arcpy.SpatialJoin_analysis(features, gemeinden, tmp_table,
                                   join_operation=join_operation,
                                   match_option=match_option)

        cursor = arcpy.da.SearchCursor(tmp_table, [id_column, 'AGS_0', 'GEN'], where_clause=where)
        ags_res = {}
        for row in cursor:
            if join_operation == 'JOIN_ONE_TO_MANY':
                if not ags_res.has_key(row[0]):
                    ags_res[row[0]] = []
                ags_res[row[0]].append((row[1], row[2]))
            else:
                ags_res[row[0]] = row[1], row[2]

        arcpy.Delete_management(tmp_table)
    return ags_res

def get_gemeindetyp(ags):
    """get the gemeindetyp referenced by ags"""
    folders = Folders()
    table = folders.get_base_table('FGDB_Basisdaten_deutschland.gdb',
                                   'bkg_gemeinden')
    columns = ['Gemeindetyp', 'AGS']
    cursor = arcpy.da.SearchCursor(table, columns,
                                   where_clause="AGS='{}'".format(ags))
    return cursor.next()[0]

def assign_groessenklassen():
    '''assign the groessenklassen to the gemeinde table based on their
    number of inhabitants'''
    tbx = DummyTbx()
    workspace = 'FGDB_Basisdaten_deutschland.gdb'
    gr_df = tbx.table_to_dataframe('Gemeindegroessenklassen',
                                   workspace=workspace,
                                   is_base_table=True)
    # set nan values to max integer (for highest groessenklasse)
    gr_df.loc[np.isnan(gr_df['bis']), 'bis'] = sys.maxint
    gem_columns = ['RS', 'Einwohner', 'groessenklasse',
                   'vwg_rs', 'vwg_groessenklasse']
    gem_table = tbx.table_to_dataframe('bkg_gemeinden', columns=gem_columns,
                                       workspace=workspace,
                                       is_base_table=True)
    summed = gem_table.groupby('vwg_rs').sum()['Einwohner'].reset_index()
    summed.rename(columns={'Einwohner': 'vwg_Einwohner'}, inplace=True)
    gem_table = gem_table.merge(summed, on='vwg_rs')

    for index, gem in gem_table.iterrows():
        for gr_col, ew_col in [('groessenklasse', 'Einwohner'),
                               ('vwg_groessenklasse', 'vwg_Einwohner')]:
            ew = gem[ew_col]
            higher = ew >= gr_df['von']
            lower = ew < gr_df['bis']
            # take the id where both borders match
            match = gr_df['groessenklasse'][np.logical_and(higher, lower)].values
            assert len(match) == 1
            gr_klasse = match[0]
            gem_table.loc[index, gr_col] = gr_klasse
    tbx.dataframe_to_table('bkg_gemeinden', gem_table, ['RS'],
                           workspace=workspace, is_base_table=True,
                           upsert=False)

def get_extent(tablename, workspace, where=''):
    """
    get the extent of a table with optional where clause for the shapes
    """
    tbx = DummyTbx()
    tbx.set_active_project()
    xmin, xmax, ymin, ymax = [np.inf, -np.inf, np.inf, -np.inf]
    cursor = tbx.query_table(tablename, columns=['SHAPE@'],
                             workspace=workspace,
                             where=where)
    for row in cursor:
        shape = row[0]
        xmin = min(xmin, shape.extent.XMin)
        xmax = max(xmax, shape.extent.XMax)
        ymin = min(ymin, shape.extent.YMin)
        ymax = max(ymax, shape.extent.YMax)
    del(cursor)
    return xmin, ymin, xmax, ymax

if __name__ == '__main__':
    tablename = "Zentren"
    workspace = 'FGDB_Standortkonkurrenz_Supermaerkte.gdb'
    import time
    start = time.time()
    print(get_extent(tablename, workspace, where='Auswahl<>{}'.format(0)))
    print(time.time() - start)
