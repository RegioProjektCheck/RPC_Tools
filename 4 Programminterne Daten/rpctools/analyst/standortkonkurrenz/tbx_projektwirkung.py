# -*- coding: utf-8 -*-
import arcpy
import os
import pandas as pd
import json
import numpy as np
import pandas as pd
import gc

from rpctools.utils.params import Tbx, Tool
from rpctools.utils.encoding import encode
from rpctools.utils.spatial_lib import get_project_centroid
from rpctools.analyst.standortkonkurrenz.zensus import Zensus, ZensusCell
from rpctools.analyst.standortkonkurrenz.routing_distances import DistanceRouting
from rpctools.utils.spatial_lib import Point
from rpctools.utils.config import Folders
from rpctools.analyst.standortkonkurrenz.sales import Sales


class ProjektwirkungMarkets(Tool):
    _param_projectname = 'projectname'
    _workspace = 'FGDB_Standortkonkurrenz_Supermaerkte.gdb'
    # ToDo: set this in toolbox?
    recalculate = False

    def add_outputs(self):
        # Add Layers
        folder = 'Standortkonkurrenz'
        group_layer = ("standortkonkurrenz")
        fc_maerkte = 'Maerkte'
        layer_maerkte = u'Umsatzveränderung Märkte'
        fc_zentren = 'Zentren'
        layer_vb = u'Umsatzveränderung Versorgungsbereiche'
        layer_gem = u'Umsatzveränderung Gemeinden'

        self.output.add_layer(group_layer, layer_maerkte, fc_maerkte,
                              template_folder=folder, zoom=False)

        betriebstyp_col = 'id_betriebstyp_nullfall'
        df_markets = self.parent_tbx.table_to_dataframe('Maerkte')
        id_nullfall = df_markets['id_betriebstyp_nullfall']
        id_planfall = df_markets['id_betriebstyp_planfall']
        planfall_idx = (id_nullfall != id_planfall) & (id_planfall > 0)

        for index, plan_market in df_markets[planfall_idx].iterrows():
            for layer in ['Kaufkraftbindung']:#, 'Erreichbarkeit']:
                layer_name = u'{n} {m} ({i})'.format(n=layer,
                                                     m=plan_market['name'],
                                                     i=plan_market['id'])
                self.output.add_layer(group_layer, layer, fc_maerkte,
                                      query='id_markt={}'.format(
                                          plan_market['id']),
                                      name=layer_name,
                                      template_folder=folder,
                                      zoom=False)

        self.output.add_layer(group_layer, layer_vb, fc_zentren,
                              template_folder=folder, zoom=False)
        self.output.add_layer(group_layer, layer_gem, fc_zentren,
                              template_folder=folder, zoom=False)

    def run(self):
        folders = Folders(self.par)
        self.recalculate = self.par.recalculate.value

        if self.recalculate:
            self.parent_tbx.delete_rows_in_table('Beziehungen_Maerkte_Zellen')
            self.parent_tbx.delete_rows_in_table('Siedlungszellen')

        df_markets = self.parent_tbx.table_to_dataframe('Maerkte')
        bbox = self.calculate_zensus(df_markets)

        arcpy.AddMessage(u'Ermittle angrenzende Gemeinden...')
        self.communities_to_centers(bbox)

        # when cells were not recalculated (including Kaufkraft)
        # do it again (number of inhabitants may have changed by the user
        # since last calc.)
        if not self.recalculate:
            arcpy.AddMessage(u'Aktualisiere Siedlungszellen der Teilflächen...')
            self.update_tfl_points()

        arcpy.AddMessage(u'Berechne Erreichbarkeiten der Märkte...')
        self.calculate_distances(df_markets, bbox)
        del(df_markets)

        arcpy.AddMessage(u'Lade Eingangsdaten für die nachfolgenden '
                         u'Berechnungen...')
        # reload markets
        df_markets = self.parent_tbx.table_to_dataframe(
            'Maerkte', columns=['id', 'id_betriebstyp_nullfall',
                                'id_betriebstyp_planfall', 'AGS', 'id_kette'])
        df_zensus = self.parent_tbx.table_to_dataframe(
            'Siedlungszellen', columns=['id', 'kk', 'id_teilflaeche'])
        
        # workaround for loading distances avoiding 'out of memory' errors
        df_distances = pd.DataFrame()
        values = self.parent_tbx.query_table(
            'Beziehungen_Maerkte_Zellen', columns=['id_markt'])
        df_distances['id_markt'] = np.array(values).reshape(len(values)).astype('int16')
        del(values)
        values = self.parent_tbx.query_table(
            'Beziehungen_Maerkte_Zellen', columns=['id_siedlungszelle'])
        df_distances['id_siedlungszelle'] = np.array(values).reshape(len(values)).astype('int32')
        del(values)
        values = self.parent_tbx.query_table(
            'Beziehungen_Maerkte_Zellen', columns=['distanz'])
        df_distances['distanz'] = np.array(values).reshape(len(values)).astype('int8')
        del(values)
        
        sales = Sales(df_distances, df_markets, df_zensus)
        gc.collect()
        arcpy.AddMessage('Berechne Nullfall...')
        kk_nullfall = sales.calculate_nullfall()
        arcpy.AddMessage('Berechne Planfall...')
        kk_planfall = sales.calculate_planfall()
        arcpy.AddMessage(u'Berechne Kenngrößen...')
        self.sales_to_db(kk_nullfall, kk_planfall)
        arcpy.AddMessage(u'Berechne Umsatzänderungen der Versorgungsbereiche...')
        self.update_centers()

        #arcpy.AddMessage(u"Erstelle Distanzmatrix...")
        #self.create_distance_matrix()


    def calculate_zensus(self, markets):
        '''extract zensus points (incl. points for planned areas)
        and write them to the database'''
        zensus = Zensus()
        x, y = get_project_centroid(self.projectname)
        centroid = Point(x, y, epsg=self.parent_tbx.config.epsg)
        square_size = self.par.square_size.value * 1000

        if (len(self.parent_tbx.query_table('Siedlungszellen')) == 0):
            arcpy.AddMessage('Extrahiere Siedlungszellen aus Zensusdaten...')
            zensus_points, bbox, max_id = zensus.cutout_area(
                centroid, square_size)
            tfl_points = self.get_tfl_points(max_id + 1)
            # settlements = zensus centroids + teilflaeche centroids
            sz_points = zensus_points + tfl_points
            arcpy.AddMessage('Schreibe Siedlungszellen in Datenbank...')
            self.zensus_to_db(sz_points)
            project = self.parent_tbx.folders.projectname
            zensus.add_kk(sz_points, project)
            # TODO: Update instead of rewrite
            self.zensus_to_db(sz_points)
        else:
            bbox = zensus.get_bbox(centroid, square_size)
            arcpy.AddMessage('Siedlungszellen bereits vorhanden, '
                             'Berechnung wird übersprungen')
        for p in bbox:
            p.transform(self.parent_tbx.config.epsg)
        return bbox

    def communities_to_centers(self, bbox):
        '''get communities intersecting with bbox and write them as centers to
        the database'''
        gemeinden = self.parent_tbx.folders.get_base_table(
            table='bkg_gemeinden', workspace='FGDB_Basisdaten_deutschland.gdb')
        p1, p2 = bbox
        # bbox as polygon
        poly_points = arcpy.Array([
            arcpy.Point(p1.x, p1.y),
            arcpy.Point(p1.x, p2.y),
            arcpy.Point(p2.x, p2.y),
            arcpy.Point(p2.x, p1.y),
            arcpy.Point(p1.x, p1.y)
        ])
        bbox_poly = arcpy.Polygon(poly_points)
        # delete existing community-entries
        self.parent_tbx.delete_rows_in_table('Zentren',
                                             where='nutzerdefiniert=0')
        ids = self.parent_tbx.query_table('Zentren', columns='id')
        max_id = np.array(ids).max() if len(ids) > 0 else 0
        # clip the communities with the bbox
        fc_bbox = 'in_memory/bbox'
        fc_clipped = 'in_memory/clipped'
        if arcpy.Exists(fc_bbox):
            arcpy.Delete_management(fc_bbox)
        if arcpy.Exists(fc_clipped):
            arcpy.Delete_management(fc_clipped)
        arcpy.CopyFeatures_management([bbox_poly], fc_bbox)
        arcpy.Clip_analysis(gemeinden, fc_bbox, fc_clipped)
        cursor = arcpy.da.SearchCursor(fc_clipped, ['SHAPE@', 'GEN', 'AGS'])
        # add clipped communities as centers
        for i, (shape, name, ags) in enumerate(cursor):
            self.parent_tbx.insert_rows_in_table(
                'Zentren',
                column_values={
                    'SHAPE@': shape,
                    'name': name,
                    'nutzerdefiniert': 0,
                    'umsatz_differenz': 0,
                    'umsatz_planfall': 0,
                    'umsatz_nullfall': 0,
                    'id': max_id + i + 1
                })
        del cursor
        arcpy.Delete_management(fc_bbox)
        arcpy.Delete_management(fc_clipped)

    def get_tfl_points(self, start_id):
        '''get the centroids of the planned areas as zensus points, start_id
        is the id the first point gets (further areas ascending)'''
        df_tfl = self.parent_tbx.table_to_dataframe(
            'Teilflaechen_Plangebiet', workspace='FGDB_Definition_Projekt.gdb')
        points = []
        i = 0
        for index, tfl in df_tfl.iterrows():
            point = ZensusCell(tfl['INSIDE_X'], tfl['INSIDE_Y'],
                               epsg=self.parent_tbx.config.epsg, ew=tfl['ew'],
                               id=start_id+i,
                               tfl_id=tfl['id_teilflaeche'])
            points.append(point)
            i += 1
        return points

    def update_tfl_points(self):
        '''update the number of inhabitants for points representing the
        planned areas'''
        df_tfl = self.parent_tbx.table_to_dataframe(
            'Teilflaechen_Plangebiet',
            columns=['id_teilflaeche', 'ew'],
            workspace='FGDB_Definition_Projekt.gdb')
        df_tfl_cells = self.parent_tbx.table_to_dataframe(
            'Siedlungszellen', columns=['SHAPE', 'id', 'kk', 'id_teilflaeche'],
            where='id_teilflaeche >= 0'
        )
        # update number of inhabitants by merging with areas
        joined = df_tfl_cells.merge(df_tfl, on='id_teilflaeche')
        # add_kk only needs the ids and number of inhabitants but
        # not the coord (not nice, but works)
        points = [ZensusCell(0, 0, id=id, ew=ew)
                  for id, ew in zip(joined['id'].values,
                                    joined['ew'].values)]
        zensus = Zensus()
        project = self.parent_tbx.folders.projectname
        zensus.add_kk(points, project)
        kk = [point.kk for point in points]
        joined['kk'] = kk
        self.parent_tbx.dataframe_to_table(
            'Siedlungszellen', joined, ['id'])

    def calculate_distances(self, markets, bbox):
        '''calculate distances between settlement points and markets and
        write them to the database'''
        routing = DistanceRouting()
        destinations = self.get_cells()
        dest_ids = [d.id for d in destinations]
        already_calculated = np.unique(self.parent_tbx.table_to_dataframe(
            'Beziehungen_Maerkte_Zellen', columns=['id_markt'])['id_markt'])
        n_markets = len(markets)
        i = 1
        for index, market in markets.iterrows():
            arcpy.AddMessage(u' - {name} ({i}/{n})'.format(
                name=market['name'], i=i, n=n_markets))
            i += 1
            if market['id'] not in already_calculated:
                arcpy.AddMessage('   wird berechnet')
                market_id = market['id']
                x, y = market['SHAPE']
                origin = Point(x, y, id=market_id,
                               epsg=self.parent_tbx.config.epsg)
                distances = routing.get_distances(origin, destinations, bbox)
                #distances = routing.get_distances(origin, destinations)
                self.distances_to_db(market_id, destinations, distances)
            else:
                arcpy.AddMessage(u'   bereits berechnet, wird übersprungen')
            gc.collect()

    def sales_to_db(self, kk_nullfall, kk_planfall):
        '''store the sales matrices in database'''
        # sum up sales join them on index to dataframe, replace missing entries
        # (e.g. no entries for planned markets in nullfall -> sales = 0)
        sales_nullfall = kk_nullfall.sum(axis=1)
        sales_planfall = kk_planfall.sum(axis=1)
        df_sales_null = pd.DataFrame(sales_nullfall, columns=['umsatz_nullfall'])
        df_sales_plan = pd.DataFrame(sales_planfall, columns=['umsatz_planfall'])
        df_sales = df_sales_null.join(df_sales_plan, how='outer')
        df_sales.fillna(0, inplace=True)
        df_sales['id'] = df_sales.index
        df_sales['umsatz_differenz'] = ((df_sales['umsatz_planfall'] /
                                         df_sales['umsatz_nullfall']) * 100 - 100)

        self.parent_tbx.dataframe_to_table('Maerkte', df_sales, pkeys=['id'])

        # invert the pivoted tables
        kk_nullfall['id_markt'] = kk_nullfall.index
        kk_planfall['id_markt'] = kk_planfall.index
        df_nullfall = pd.melt(kk_nullfall,
                              value_name='kk_strom_nullfall',
                              id_vars='id_markt')
        df_planfall = pd.melt(kk_planfall,
                              value_name='kk_strom_planfall',
                              id_vars='id_markt')

        # join the results to the cell table
        cells = self.parent_tbx.table_to_dataframe('Beziehungen_Maerkte_Zellen')
        del cells['kk_strom_nullfall']
        del cells['kk_strom_planfall']
        cells = cells.merge(df_nullfall,
                            on=['id_siedlungszelle', 'id_markt'], how='left')
        cells = cells.merge(df_planfall,
                            on=['id_siedlungszelle', 'id_markt'], how='left')
        cells.fillna(0, inplace=True)
        cells.sort(['id_markt', 'id_siedlungszelle'], inplace=True)


        # should be identical, but take both anyway
        sum_null = cells.groupby('id_siedlungszelle',
                                 as_index=False)['kk_strom_nullfall'].sum()
        sum_plan = cells.groupby('id_siedlungszelle',
                                 as_index=False)['kk_strom_planfall'].sum()
        cells = cells.merge(sum_null, on=['id_siedlungszelle'],
                            suffixes=('', '_sum'))
        cells = cells.merge(sum_plan, on=['id_siedlungszelle'],
                            suffixes=('', '_sum'))
        cells['kk_bindung_nullfall'] = cells['kk_strom_nullfall'] * 100 / cells['kk_strom_nullfall_sum']
        cells['kk_bindung_planfall'] = cells['kk_strom_planfall'] * 100 / cells['kk_strom_planfall_sum']

        # deletion of old entries and inserting is faster than updating
        self.parent_tbx.delete_rows_in_table('Beziehungen_Maerkte_Zellen')
        #column_values = {}
        #for col in cells.columns:
            #column_values[col] = cells[col].values
        arcpy.AddMessage(u'Schreibe Kenngrößen in Datenbank...')
        self.parent_tbx.insert_dataframe_in_table(
            'Beziehungen_Maerkte_Zellen', cells)

    def update_centers(self):
        '''calculate the sales of the defined centers'''
        tmp_join = os.path.join(arcpy.env.scratchGDB, 'tmp_join')
        tmp_markets = os.path.join(arcpy.env.scratchGDB, 'tmp_markets')
        if arcpy.Exists(tmp_join):
            arcpy.Delete_management(tmp_join)
        if arcpy.Exists(tmp_markets):
            arcpy.Delete_management(tmp_markets)

        umsatz_fields = ['umsatz_nullfall', 'umsatz_planfall']

        markets_table = self.parent_tbx.folders.get_table('Maerkte')
        centers_table = self.parent_tbx.folders.get_table('Zentren')

        arcpy.CopyFeatures_management(markets_table, tmp_markets)
        # you have to remove the id column to join because both tables have
        # column of same name
        arcpy.DeleteField_management(tmp_markets, 'id')
        # remove the planned markets, that did not exist in nullfall
        self.parent_tbx._delete_rows_in_table(tmp_markets,
                                              where='id_betriebstyp_nullfall=0')

        fieldmappings = arcpy.FieldMappings()
        for field in umsatz_fields:
            fm = arcpy.FieldMap()
            fm.addInputField(tmp_markets, field)
            fieldmappings.addFieldMap(fm)
        fm_c = arcpy.FieldMap()
        # the table assigned to the fieldmapping is ignored by dumbass arcpy,
        # arcpy always takes markets_table anyway (so the need to delete before)
        fm_c.addInputField(centers_table, 'id')
        fieldmappings.addFieldMap(fm_c)

        arcpy.SpatialJoin_analysis(tmp_markets,centers_table, tmp_join,
                                   join_type='KEEP_COMMON',
                                   join_operation='JOIN_ONE_TO_MANY',
                                   field_mapping=fieldmappings,
                                   match_option='WITHIN')
        columns = ['id'] + umsatz_fields
        rows = self.parent_tbx._query_table(tmp_join,
                                            columns=columns)
        df_join = pd.DataFrame.from_records(rows, columns=columns)
        summed = df_join.groupby('id').sum()
        summed['umsatz_differenz'] = 100 * (summed['umsatz_planfall'] /
                                            summed['umsatz_nullfall']) - 100
        summed['id'] = summed.index
        self.parent_tbx.dataframe_to_table('Zentren', summed, pkeys=['id'])


    def distances_to_db(self, market_id, destinations, distances):
        self.parent_tbx.delete_rows_in_table(
            'Beziehungen_Maerkte_Zellen', where='id_markt={}'.format(market_id))
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
        self.parent_tbx.insert_rows_in_table('Beziehungen_Maerkte_Zellen',
                                             column_values)
        for p in shapes:
            del(p)

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
        tfl_ids = []
        self.parent_tbx.delete_rows_in_table('Siedlungszellen')
        for point in zensus_points:
            # ignore zensus points with no inhabitants
            # (but keep the planned ones)
            if point.ew <= 0 and point.tfl_id < 0:
                continue
            point.transform(epsg)
            point.create_geom()
            shapes.append(point.geom)
            ews.append(point.ew)
            kk_indices.append(point.kk_index)
            kks.append(point.kk)
            cell_ids.append(point.id)
            tfl_ids.append(point.tfl_id)

        df['id'] = cell_ids
        df['SHAPE'] = shapes
        df['ew'] = ews
        df['kk_index'] = kk_indices
        df['kk'] = kks
        df['id_teilflaeche'] = tfl_ids

        self.parent_tbx.insert_dataframe_in_table('Siedlungszellen', df)

    def create_distance_matrix(self):
        distance_path = self.folders.get_table("Beziehungen_Maerkte_Zellen", "FGDB_Standortkonkurrenz_Supermaerkte.gdb")
        modul_path = self.folders.get_db("FGDB_Standortkonkurrenz_Supermaerkte.gdb")
        markets_path = self.folders.get_table("Maerkte", "FGDB_Standortkonkurrenz_Supermaerkte.gdb")
        matrix_path = os.path.join(modul_path, "Distanzmatrix")
        arcpy.AddMessage("...Anzahl Maerkte ermitteln...")
        cursor = arcpy.da.SearchCursor(markets_path, ["id"])
        number_markets = 0
        for row in cursor:
            number_markets = row[0]
        arcpy.AddMessage("...Distanzmatrix initialisieren...")
        if arcpy.Exists(matrix_path):
            arcpy.Delete_management(matrix_path)
        arcpy.CreateTable_management(modul_path, "Distanzmatrix")
        arcpy.AddField_management(matrix_path, "ID_Siedlungszelle", "LONG")

        fields_insert = ["ID_Siedlungszelle"]
        for number in range(1, number_markets + 1):
            arcpy.AddField_management(matrix_path, "Markt_" + str(number), "LONG")
            fields_insert.append("Markt_" + str(number))


        cursor_distance = arcpy.da.SearchCursor(distance_path, ["id_markt","id_siedlungszelle","distanz"])
        arcpy.AddMessage("...Distanzmatrix befuellen...")
        used_cell = -1
        new_cell = [-1] * (number_markets +1)
        for cell in cursor_distance:
            if cell[1] == used_cell or used_cell == -1:
                #arcpy.AddMessage("Update: " + str(cell[1]))
                new_cell[cell[0]] = cell[2]
            else:
                new_cell[0] = used_cell
                cursor_matrix = arcpy.da.InsertCursor(matrix_path, fields_insert)
                arcpy.AddMessage("Insert: " + str(new_cell[0]))
                cursor_matrix.insertRow(new_cell)
                new_cell = [-1] * (number_markets +1)
                new_cell[cell[0]] = cell[2]
            used_cell = cell[1]

class TbxProjektwirkungMarkets(Tbx):

    @property
    def label(self):
        return encode(u'Projektwirkung schätzen')

    @property
    def Tool(self):
        return ProjektwirkungMarkets

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

        # set square size
        p = self.add_parameter('square_size')
        p.name = u'sqare_size'
        p.displayName = encode(u'Größe des betrachteten Siedlungs-Bereichs '
                               u'wählen (km)')
        p.parameterType = 'Required'
        p.direction = 'Input'
        p.datatype = u'GPLong'
        p.enabled = False
        p.value = 40

        param = self.add_parameter('recalculate')
        param.name = encode(u'Neuberechnung')
        param.displayName = encode(u'Neuberechnung der Distanzen und '
                                   u'Siedlungszellen erzwingen')
        param.parameterType = 'Optional'
        param.direction = 'Input'
        param.datatype = u'GPBoolean'

        return params

    def _updateParameters(self, params):
        pass

if __name__ == "__main__":
    t = TbxProjektwirkungMarkets()
    t.getParameterInfo()
    t.set_active_project()
    t.par.recalculate.value = False
    #t.show_outputs()
    t.execute()

    print 'done'