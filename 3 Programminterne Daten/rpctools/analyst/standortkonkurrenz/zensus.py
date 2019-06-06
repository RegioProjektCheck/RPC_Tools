from rpctools.utils.config import Folders, Config
from rpctools.utils.params import DummyTbx
from rpctools.utils.spatial_lib import clip_raster, Point, points_within, \
     get_extent

import os
import shutil
import sys
import arcpy
import numpy as np
import time
from collections import defaultdict


class ZensusCell(Point):
    def __init__(self, x, y, epsg=4326, ew=0, id=None, kk_index=None,
                 kk=None, tfl_id=-1, ags='', in_auswahl=False):
        super(ZensusCell, self).__init__(x, y, id=id, epsg=epsg)
        self.ew = ew
        self.kk_index = kk_index
        self.kk = kk
        # -1 if point is not correlated to a planned area
        self.tfl_id = tfl_id
        self.ags = ags
        self.in_auswahl = in_auswahl


class Zensus(object):
    _workspace = "FGDB_Standortkonkurrenz_Supermaerkte.gdb"
    _table = "Zentren"

    def __init__(self):
        self.folders = Folders()
        self.epsg = 3035
        self.tmp_folder = arcpy.env.scratchGDB
        try:
            arcpy.Delete_management(self.tmp_folder)
            arcpy.CreateFileGDB_management(*os.path.split(self.tmp_folder))
        except:
            pass

    def cutout_area(self, bbox, epsg, cutout_shape=None):
        """
        return the centroids of the zensus cells as points inside the
        selected communities
        """
        zensus_points = []
        zensus_raster = self.folders.ZENSUS_RASTER_500_FILE
        # temporary paths
        out_raster = os.path.join(self.tmp_folder, 'zensus_cutout')
        raster_points = os.path.join(self.tmp_folder,
                                     'raster_points')
        raster_points_projected = os.path.join(self.tmp_folder,
                                         'raster_points_projected')
        raster_points_clipped = os.path.join(self.tmp_folder,
                                             'raster_points_clipped')
        def del_tmp():
            for fn in [raster_points, raster_points_projected, out_raster,
                       raster_points_clipped]:
                arcpy.Delete_management(fn)
        del_tmp()
        out_raster = os.path.join(self.tmp_folder, 'zensus_cutout')
        # clip minimum to rectangle shape that still contains all communities
        srid = clip_raster(zensus_raster, out_raster, bbox)
        # get raster points
        arcpy.RasterToPoint_conversion(out_raster, raster_points)
        start = time.time()
        with arcpy.da.UpdateCursor(raster_points, "GRID_CODE") as cursor:
            for row in cursor:
                if row[0] <= 0:
                    cursor.deleteRow()
        print(time.time() - start)
        # project raster points to gauss krueger
        out_cs = arcpy.SpatialReference(epsg)
        arcpy.Project_management(raster_points, raster_points_projected,
                                 out_cs)

        if cutout_shape:
            # clip raster points to selected communities
            arcpy.Clip_analysis(raster_points_projected,
                                cutout_shape,
                                raster_points_clipped)
        else:
            raster_points_clipped = raster_points
        # create list with zensus points for return
        rows = arcpy.da.SearchCursor(raster_points_clipped,
                                     ['SHAPE@XY', 'GRID_CODE'])
        zensus_points = []
        index = 0
        for ((x, y), value) in rows:
            if value <= 0:
                continue
            p = ZensusCell(x, y, id=index, epsg=srid, ew=value)
            zensus_points.append(p)
            index += 1
        # delete temporary files
        del_tmp()
        return zensus_points, len(zensus_points)

    def add_kk_ags(self, zensus_points, project, ags_auswahl=[]):
        """
        add kaufkraft and ags by joining to base tables
        return dictionary with ags_auswahl as keys values and
        [inhabitants, kk] as values
        """
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
        cursor = arcpy.da.SearchCursor(
            default_table, ['Wert'],
            where_clause="Info = 'Kaufkraft pro Person'")
        base_kk = cursor.next()[0]
        del(cursor)
        tmp_table = os.path.join(arcpy.env.scratchGDB, 'tmp_table')
        tmp_ags_join = os.path.join(arcpy.env.scratchGDB, 'tmp_ags_join')
        kk_table = folders.get_base_table(
            workspace='FGDB_Basisdaten_deutschland.gdb',
            table='KK2015')
        ags_table = folders.get_base_table(
            workspace='FGDB_Basisdaten_deutschland.gdb',
            table='bkg_gemeinden')
        sz_table = folders.get_table(
            'Siedlungszellen',
            workspace='FGDB_Standortkonkurrenz_Supermaerkte.gdb',
            project=project)

        arcpy.Delete_management(tmp_table)
        arcpy.Delete_management(tmp_ags_join)
        arcpy.SpatialJoin_analysis(sz_table, ags_table, tmp_ags_join,
                                   match_option='WITHIN')
        arcpy.SpatialJoin_analysis(sz_table, kk_table, tmp_table,
                                   match_option='WITHIN')

        kk_indices = {}
        ags_indices = {}
        cursor = arcpy.da.SearchCursor(tmp_table, ['id', 'kk_ew_index'])
        for id_cell, kk_index in cursor:
            kk_indices[id_cell] = kk_index
        del(cursor)
        ags_indices = {}
        results = defaultdict(list)
        cursor = arcpy.da.SearchCursor(tmp_ags_join, ['id', 'AGS_1'])
        for id_cell, ags in cursor:
            ags_indices[id_cell] = ags
        del(cursor)

        results = dict([(a, [0, 0]) for a in ags_auswahl])
        for zensus_cell in zensus_points:
            kk_index = default_kk_index
            # take default kk_index only atm
            #if kk_indices.has_key(zensus_cell.id):
                #kk_index = kk_indices[zensus_cell.id]
                #if kk_index is None:
                    #kk_index = default_kk_index
            zensus_cell.kk_index = kk_index
            zensus_cell.kk = zensus_cell.ew * base_kk * kk_index / 100
            if ags_indices.has_key(zensus_cell.id):
                zensus_cell.ags = ags_indices[zensus_cell.id] or ''
                if zensus_cell.ags in ags_auswahl:
                    zensus_cell.in_auswahl = True
                    res = results[zensus_cell.ags]
                    res[0] += zensus_cell.ew
                    res[1] += zensus_cell.kk

        arcpy.Delete_management(tmp_table)
        arcpy.Delete_management(tmp_ags_join)
        return results
