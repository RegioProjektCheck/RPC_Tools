from rpctools.utils.config import Folders, Config
from rpctools.utils.spatial_lib import clip_raster, Point, points_within

import os
import shutil
import sys
import arcpy
import numpy as np


class ZensusCell(Point):
    def __init__(self, x, y, epsg=4326, ew=0, id=None, kk_index=None,
                 kk=None, tfl_id=-1):
        super(ZensusCell, self).__init__(x, y, id=id, epsg=epsg)
        self.ew = ew
        self.kk_index = kk_index
        self.kk = kk
        # -1 if point is not correlated to a planned area
        self.tfl_id = tfl_id


class Zensus(object):
    def __init__(self):
        self.folders = Folders()
        self.epsg = 4326
        self.tmp_folder = os.path.join(self.folders.TEMPORARY_GDB_PATH,
                                       'Zensus')
        if os.path.exists(self.tmp_folder):
            arcpy.Delete_management(self.tmp_folder)
        try:
            os.mkdir(self.tmp_folder)
        except:
            pass

    def cutout_area(self, centroid, radius, bbox, epsg=None):
        """return the centroids of the zensus cells as points in a square area
        with the dimensions of distance x distance with the given centroid in
        the middle
        """
        size = 2 * radius
        zensus_points = []
        zensus_raster = self.folders.ZENSUS_RASTER_FILE

        out_raster = os.path.join(self.tmp_folder, 'zensus_cutout.tif')

        # clipping circles is pro-version only
        # clip square instead and filter by distances
        srid = clip_raster(zensus_raster, out_raster, bbox)

        out_shp = os.path.join(self.tmp_folder,
                               'zensus_cutout.shp')
        #cellsize = float(arcpy.GetRasterProperties_management(
            #zensus_file, 'CELLSIZEX').getOutput(0).replace(',', '.'))

        arcpy.RasterToPoint_conversion(out_raster, out_shp)
        
        desc = arcpy.Describe(out_shp)
        rows = arcpy.da.SearchCursor(out_shp, ['SHAPE@XY', 'GRID_CODE'])
        coords = []
        for i, ((x, y), value) in enumerate(rows):
            p = ZensusCell(x, y, id=i, epsg=srid, ew=value)
            p.transform(epsg)
            zensus_points.append(p)
            coords.append((p.x, p.y))
        
        coords_within, within_idx = points_within(
            (centroid.x, centroid.y), coords, radius)

        return np.array(zensus_points)[within_idx].tolist(), i

    def add_kk(self, zensus_points, project):
        folders = Folders()
        default_table = folders.get_base_table(
            table='Grundeinstellungen',
            workspace='FGDB_Standortkonkurrenz_Supermaerkte_Tool.gdb'
        )
        cursor = arcpy.da.SearchCursor(
            default_table, ['Wert'],
            where_clause="Info = 'KK je Einwohner default'")
        default_kk_index = cursor.next()[0]
        del(cursor)
        base_kk = 2280
        tmp_table = os.path.join(arcpy.env.scratchGDB, 'tmp_kk_join')
        kk_table = folders.get_base_table(
            workspace='FGDB_Basisdaten_deutschland.gdb',
            table='KK2015')
        zensus_table = folders.get_table(
            'Siedlungszellen',
            workspace='FGDB_Standortkonkurrenz_Supermaerkte.gdb',
            project=project)

        if arcpy.Exists(tmp_table):
            arcpy.Delete_management(tmp_table)
        arcpy.SpatialJoin_analysis(zensus_table, kk_table, tmp_table,
                                   match_option='WITHIN')

        cursor = arcpy.da.SearchCursor(tmp_table, ['id', 'kk_ew_index'])
        kk_indices = {}
        for id_cell, kk_index in cursor:
            kk_indices[id_cell] = kk_index
        for zensus_cell in zensus_points:
            if not kk_indices.has_key(zensus_cell.id):
                continue
            kk_index = kk_indices[zensus_cell.id]
            if kk_index is None:
                kk_index = default_kk_index
            zensus_cell.kk_index = kk_index
            zensus_cell.kk = zensus_cell.ew * base_kk * kk_index / 100

        arcpy.Delete_management(tmp_table)