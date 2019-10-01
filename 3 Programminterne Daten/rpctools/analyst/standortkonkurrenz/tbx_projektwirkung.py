# -*- coding: utf-8 -*-
import arcpy
import os
import pandas as pd
import json
import numpy as np
import pandas as pd
import gc
from collections import Counter

from rpctools.utils.params import Tbx, Tool
from rpctools.utils.encoding import encode
from rpctools.analyst.standortkonkurrenz.zensus import Zensus, ZensusCell
from rpctools.analyst.standortkonkurrenz.routing_distances import DistanceRouting
from rpctools.utils.spatial_lib import (get_project_centroid, Point,
                                        features_to_raster)
from rpctools.utils.config import Folders
from rpctools.analyst.standortkonkurrenz.sales import Sales

DEBUG = True


class ProjektwirkungMarkets(Tool):
    _param_projectname = 'projectname'
    _settlement_buffer = 3000
    _markets_buffer = 6000
    _workspace = 'FGDB_Standortkonkurrenz_Supermaerkte.gdb'
    recalculate = False

    def add_outputs(self):
        # Add Layers
        folder = 'Standortkonkurrenz'
        group_layer = ("standortkonkurrenz")
        fc_maerkte = 'Maerkte'
        layer_maerkte = u'Umsatzveränderung Märkte'
        fc_zentren = 'Zentren'
        layer_auswahl = ''
        layer_vb = u'Umsatzveränderung Bestand Zentren'
        layer_gem = u'Umsatzveränderung Bestand Verwaltungsgemeinschaften'
        layer_zen_n = u'Zentralität Nullfall'
        layer_zen_p = u'Zentralität Planfall'
        layer_zen_e = u'Entwicklung Zentralität'
        layer_vkfl_n = u'Verkaufsflächendichte Nullfall'
        layer_vkfl_p = u'Verkaufsflächendichte Planfall'
        layer_vkfl_e = u'Entwicklung Verkaufsflächendichte'

        #self.output.add_layer(group_layer, layer_maerkte, fc_maerkte,
                              #template_folder=folder, zoom=False)

        betriebstyp_col = 'id_betriebstyp_nullfall'
        df_markets = self.parent_tbx.table_to_dataframe('Maerkte')
        id_nullfall = df_markets['id_betriebstyp_nullfall']
        id_planfall = df_markets['id_betriebstyp_planfall']
        planfall_idx = np.logical_and((id_nullfall != id_planfall), (id_planfall > 0))
    
        for index, plan_market in df_markets[planfall_idx].iterrows():
            layer_name = u'Kaufkraftbindung {m} ({i})'.format(
                m=plan_market['name'], i=plan_market['id'])
            self.output.remove_layer(layer_name)
            fn = u'Kaufkraftbindung_Raster_{i}'.format(i=plan_market['id'])

            fp = self.folders.get_table(fn, check=False)
            arcpy.AddMessage('Erzeuge Raster {}'.format(fn))
            table = self.folders.get_table('Beziehungen_Maerkte_Zellen')
            where = ('id_markt={} and distanz>=0 and in_auswahl=1'
                     .format(plan_market['id']))
            arcpy.Delete_management(fp)
            template = self.folders.ZENSUS_RASTER_500_FILE
            arcpy.Delete_management(fp)
            try:
                raster_file = features_to_raster(
                    table, fp, 'kk_bindung_planfall', template=template,
                    where=where)
            except arcpy.ExecuteError:
                arcpy.AddMessage(
                    u'Keine Ergebnisse der Kaufkraftbindung im '
                    u'Planfall für den Markt "{}" -> scheinbar nicht erreichbar'
                    .format(plan_market['name']))
                continue
            self.output.add_layer(group_layer, 'Kaufkraftbindung_Raster',
                                  fn,
                                  name=layer_name,
                                  template_folder=folder,
                                  zoom=False)
        self.output.hide_layer(u'Ausgewählte Gemeinden im Betrachtungsraum')
        self.output.hide_layer(u'Nicht ausgewählte Gemeinden')
        self.output.add_layer(group_layer, layer_vb, fc_zentren, visible=False,
                              template_folder=folder, zoom=False)
        self.output.add_layer(group_layer, layer_gem, fc_zentren,
                              template_folder=folder, zoom=False)
        self.output.add_layer(group_layer, layer_zen_n, fc_zentren,
                              visible=False, template_folder=folder, zoom=False)
        self.output.add_layer(group_layer, layer_zen_p, fc_zentren,
                              visible=False, template_folder=folder, zoom=False)
        self.output.add_layer(group_layer, layer_zen_e, fc_zentren,
                              visible=False, template_folder=folder, zoom=False)
        self.output.add_layer(group_layer, layer_vkfl_n, fc_zentren,
                              visible=False, template_folder=folder, zoom=False)
        self.output.add_layer(group_layer, layer_vkfl_p, fc_zentren,
                              visible=False, template_folder=folder, zoom=False)
        self.output.add_layer(group_layer, layer_vkfl_e, fc_zentren,
                              visible=False, template_folder=folder, zoom=False)

    def run(self):
        folders = Folders(self.par)
        self.recalculate = self.par.recalculate.value

        # set "Gemeinden" as selected based on selection of "Verwaltungsgemeinschaften"
        selected_rs = self.parent_tbx.query_table(
            'Zentren', columns=['RS'],
            where='"Auswahl" <> 0 and nutzerdefiniert = -1')
        self.parent_tbx.update_table('Zentren', {'Auswahl': 0},
                                     where='nutzerdefiniert = 0')

        selected_rs = ["'{}'".format(r[0]) for r in selected_rs]
        self.parent_tbx.update_table(
            'Zentren', {'Auswahl': 1},
            where='"RS" in ({})'.format(','.join(selected_rs)))

        # check the settings of last calculation
        set_table = 'Settings'
        cur_ags = self.parent_tbx.query_table(
            'Zentren', columns=['AGS'],
            where='"Auswahl" <> 0 and nutzerdefiniert = 0')
        cur_ags = zip(*cur_ags)[0]
        cur_settings = {
            'sz_puffer': self.par.radius_sz.value,
            'betrachtungsraum': ','.join(cur_ags),
        }
        prev_settings = self.parent_tbx.query_table(set_table,
                                                    columns=cur_settings.keys())
        if len(prev_settings) == 0:
            self.parent_tbx.insert_rows_in_table(set_table, cur_settings)
            self.recalculate = True  # will be done anyway, cause all result tables are empty
        else:
            prev_settings = prev_settings[0]
            equal = True
            for i, (col, cur_set) in enumerate(cur_settings.iteritems()):
                    # ags changed
                if ((col == 'betrachtungsraum' and
                     Counter(cur_set.split(',')) !=
                     Counter(prev_settings[i].split(','))) or
                    # something else changed
                    cur_set != prev_settings[i]):
                    equal = False
                    break
            if not equal:
                arcpy.AddMessage(
                    u'Der gepufferte Betrachtungsraum hat sich seit der letzten '
                    u'Berechnung geändert. Neuberechnung der Siedlungszellen und '
                    u'Distanzen wird ausgeführt.')
                self.recalculate = True
                self.parent_tbx.update_table(set_table, cur_settings)

        # empty result tables (empty indicates need of recalculation later on)
        if self.recalculate:
            self.parent_tbx.delete_rows_in_table('Beziehungen_Maerkte_Zellen')
            self.parent_tbx.delete_rows_in_table('Siedlungszellen')

        # buggy? counts rows that are not there
        #sz_count = int(arcpy.GetCount_management(
            #self.folders.get_table('Siedlungszellen')).getOutput(0))
        sz_count = len(self.parent_tbx.query_table('Siedlungszellen',
                                                   columns=['id']))
        if sz_count == 0:
            # calculate cells with inhabitants (incl. 'teilflaechen')
            ags_res = self.calculate_zensus(cur_ags)

            for ags, (ew, kk) in ags_res.iteritems():
                self.parent_tbx.update_table('Zentren',
                                             column_values={'ew': ew, 'kk': kk},
                                             where="ags='{}'".format(ags))
        else:
            arcpy.AddMessage('Siedlungszellen bereits vorhanden, '
                             'Berechnung wird übersprungen')
            # at least update the cells of the user defined 'teilflaechen'
            # (number of inhabitants may have changed by the user since last calc.)
            arcpy.AddMessage(u'Aktualisiere Siedlungszellen der Teilflächen...')
            self.update_tfl_points()

        arcpy.AddMessage(u'Berechne Erreichbarkeiten der Märkte...')
        self.calculate_distances()

        arcpy.AddMessage(u'Lade Eingangsdaten für die nachfolgenden '
                         u'Berechnungen...')
        # reload markets
        df_markets = self.parent_tbx.table_to_dataframe(
            'Maerkte', columns=['id', 'id_betriebstyp_nullfall',
                                'id_betriebstyp_planfall', 'AGS', 'id_kette'])
        df_zensus = self.parent_tbx.table_to_dataframe(
            'Siedlungszellen', columns=['id', 'kk', 'id_teilflaeche'])

        df_distances = pd.DataFrame()

        # workaround for loading distances avoiding 'out of memory' errors
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
        df_distances['distanz'] = np.array(values).reshape(len(values)).astype('int32')
        del(values)
        values = self.parent_tbx.query_table(
            'Beziehungen_Maerkte_Zellen', columns=['luftlinie'])
        df_distances['luftlinie'] = np.array(values).reshape(len(values)).astype('int32')
        del(values)

        sales = Sales(df_distances, df_markets, df_zensus, debug=DEBUG,
                      projectname=self.projectname)
        gc.collect()
        arcpy.AddMessage('Berechne Nullfall...')
        kk_nullfall = sales.calculate_nullfall()
        arcpy.AddMessage('Berechne Planfall...')
        kk_planfall = sales.calculate_planfall()
        arcpy.AddMessage(u'Berechne Kenngrößen...')
        self.sales_to_db(kk_nullfall, kk_planfall)
        arcpy.AddMessage(u'Werte Ergebnisse auf Verwaltungsgemeinschaftsebene aus...')
        self.update_centers()

    def calculate_zensus(self, ags_auswahl):
        '''extract zensus points (incl. points for planned areas)
        and write them to the database'''
        buffered = self.folders.get_table('Siedlungszellen_Puffer', check=False)
        arcpy.Delete_management(buffered)
        bbox = self.buffer_area(self.par.radius_sz.value, buffered)

        zensus = Zensus()
        arcpy.AddMessage('Extrahiere Siedlungszellen aus Zensusdaten...')
        zensus_points, max_id = zensus.cutout_area(
            bbox, epsg=self.parent_tbx.config.epsg, cutout_shape=buffered)
        tfl_points = self.get_tfl_points(max_id + 1)
        # settlements = zensus centroids + teilflaeche centroids
        sz_points = zensus_points + tfl_points
        arcpy.AddMessage('Schreibe Siedlungszellen in Datenbank...')
        self.zensus_to_db(sz_points)
        project = self.parent_tbx.folders.projectname
        ags_res = zensus.add_kk_ags(sz_points, project, ags_auswahl)
        # TODO: Update instead of rewrite
        self.zensus_to_db(sz_points)

        return ags_res

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
                               tfl_id=tfl['id_teilflaeche'], in_auswahl=True)
            points.append(point)
            i += 1
        return points

    def zensus_to_db(self, zensus_points):
        df = pd.DataFrame()
        shapes = []
        ews = []
        kk_indices = []
        kks = []
        cell_ids = []
        tfl_ids = []
        in_auswahl = []
        ags = []
        self.parent_tbx.delete_rows_in_table('Siedlungszellen')
        for point in zensus_points:
            # ignore zensus points with no inhabitants
            # (but keep the planned ones)
            if point.ew <= 0 and point.tfl_id < 0:
                continue
            point.create_geom()
            shapes.append(point.geom)
            ews.append(point.ew)
            kk_indices.append(point.kk_index)
            kks.append(point.kk)
            cell_ids.append(point.id)
            tfl_ids.append(point.tfl_id)
            in_auswahl.append(int(point.in_auswahl))
            ags.append(point.ags)

        df['id'] = cell_ids
        df['SHAPE'] = shapes
        df['ew'] = ews
        df['kk_index'] = kk_indices
        df['kk'] = kks
        df['id_teilflaeche'] = tfl_ids
        df['in_auswahl'] = in_auswahl
        df['ags'] = ags

        self.parent_tbx.insert_dataframe_in_table('Siedlungszellen', df)

    def buffer_area(self, radius, output):
        communities = self.folders.get_table('Zentren')
        ws_tmp = arcpy.env.scratchGDB
        sel_comm = os.path.join(ws_tmp, 'sel_comm')

        arcpy.Delete_management(sel_comm)

        arcpy.FeatureClassToFeatureClass_conversion(
            communities, ws_tmp, os.path.split(sel_comm)[1],
            where_clause='Auswahl<>0')

        arcpy.AddMessage('Analysiere Pufferbereich...')
        if radius > 0:
            # create buffer area
            arcpy.Buffer_analysis(sel_comm, output,
                                  radius,
                                  dissolve_option='ALL')
        else:
            arcpy.CopyFeatures_management(sel_comm, output)

        bbox = self.get_bbox(output)
        arcpy.Delete_management(sel_comm)
        return bbox

    def get_bbox(self, table_path):
        desc = arcpy.Describe(table_path)
        epsg = self.parent_tbx.config.epsg
        ex = desc.extent
        bbox = (Point(ex.XMin, ex.YMin, epsg=epsg),
                Point(ex.XMax, ex.YMax, epsg=epsg))
        return bbox

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
        zensus.add_kk_ags(points, project)
        kk = [point.kk for point in points]
        joined['kk'] = kk
        self.parent_tbx.dataframe_to_table(
            'Siedlungszellen', joined, ['id'])

    def calculate_distances(self):
        '''calculate distances between settlement points and markets and
        write them to the database'''

        # calculate bounding box
        bbox = self.get_bbox(self.folders.get_table('Siedlungszellen'))
        markets = self.parent_tbx.table_to_dataframe('Maerkte')
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
                distances, beelines = routing.get_distances(
                    origin, destinations, bbox)
                arcpy.AddMessage('   wird gespeichert')
                self.distances_to_db(market_id, destinations, distances,
                                     beelines)
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
        df_sales.fillna(0, inplace=True)

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
        cells.sort_values(by = ['id_markt', 'id_siedlungszelle'], inplace=True)


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

    def get_markets_in_user_centers(self):
        ''' find markets in user defined centers by spatial joining '''
        tmp_table = os.path.join(arcpy.env.scratchGDB, 'tmp_join')
        if arcpy.Exists(tmp_table):
            arcpy.Delete_management(tmp_table)
        arcpy.SpatialJoin_analysis(self.folders.get_table('Zentren'), self.folders.get_table('Maerkte'), tmp_table,
                                   join_operation='JOIN_ONE_TO_MANY', match_option='CONTAINS')
        where = 'nutzerdefiniert = 1'
        columns = ['id', 'id_1']
        cursor = arcpy.da.SearchCursor(tmp_table, columns, where_clause=where)
        mapping = {}
        for row in cursor:
            center_id, market_id = row
            if center_id not in mapping:
                mapping[center_id] = []
            mapping[center_id].append(market_id)
        return mapping

    def update_centers(self):
        '''calculate the sales of the defined centers'''

        df_markets = self.parent_tbx.table_to_dataframe(
            'Maerkte',
            columns=['id', 'AGS', 'umsatz_planfall', 'umsatz_nullfall', 'vkfl',
                     'vkfl_planfall', 'id_betriebstyp_nullfall',
                     'id_betriebstyp_planfall'])

        # Zentralität needs turnovers including new and changed markets
        # copy column for use in Zentralität, as it will be changed in the next step
        df_markets['umsatz_planfall_full'] = df_markets['umsatz_planfall']

        # exclude new markets by setting their turnovers to zero
        new_market_idx = df_markets['id_betriebstyp_nullfall'] == 0
        df_markets.loc[new_market_idx, 'umsatz_planfall'] = 0

        df_centers = self.parent_tbx.table_to_dataframe(
            'Zentren', columns=['id', 'AGS', 'RS', 'ew', 'kk', 'nutzerdefiniert'])

        # ignore turnover changes for existing markets that have been changed
        changed_market_idx = np.logical_and(
            (df_markets['id_betriebstyp_nullfall']
             != df_markets['id_betriebstyp_planfall']),
            df_markets['id_betriebstyp_nullfall'] != 0)
        df_markets.loc[changed_market_idx, 'umsatz_planfall'] = \
            df_markets.loc[changed_market_idx, 'umsatz_nullfall']
        summed = df_markets.groupby('AGS').sum().reset_index()
        df_centers_res = df_centers.merge(summed, how='left', on='AGS')
        # pandas gives left table suffix '_x' by default after joining
        df_centers_res.rename(columns={'id_x': 'id'}, inplace=True)

        # sum up ags based results to rs
        df_ags_res = df_centers_res[df_centers_res['nutzerdefiniert'] == 0]
        df_ags_agg = df_ags_res.groupby('RS')['ew', 'kk', 'umsatz_planfall',
                                              'umsatz_nullfall',
                                              'umsatz_planfall_full', 'vkfl',
                                              'vkfl_planfall'].sum()
        # -1 indicate the "Verwaltungsgemeinschaften"
        rs_idx = df_centers_res['nutzerdefiniert'] == -1
        for index, row in df_ags_agg.iterrows():
            r_idx = np.logical_and(rs_idx, (df_centers_res['RS'] == index))
            for col in row.keys():
                df_centers_res.loc[r_idx, col] = row[col]

        # get markets in user centers and sum up their values.
        # this spatial joining could be done for ALL centers instead of joining
        # by ags (actually it once was before ags centers were selectable), but
        # for having it done fast, it is only applied for user defined centers
        # now
        user_center_markets = self.get_markets_in_user_centers()
        sum_cols = ['umsatz_planfall', 'umsatz_nullfall',
                    'umsatz_planfall_full', 'vkfl', 'vkfl_planfall']
        for center_id, market_ids in user_center_markets.iteritems():
            mic_idx = df_markets['id'].isin(market_ids)
            markets_in_center = df_markets.loc[mic_idx, sum_cols].sum()
            center_idx = df_centers_res['id'] == center_id
            summed = df_markets.loc[mic_idx, sum_cols].sum().values
            df_centers_res.loc[center_idx, sum_cols] = summed

        df_centers_res['umsatz_differenz'] = (
            100 * (df_centers_res['umsatz_planfall'] /
                   df_centers_res['umsatz_nullfall']) - 100)

        df_centers_res['vkfl_dichte_nullfall'] = (
            df_centers_res['vkfl'] / df_centers_res['ew'])
        df_centers_res['vkfl_dichte_planfall'] = (
            df_centers_res['vkfl_planfall'] / df_centers_res['ew'])
        df_centers_res['vkfl_dichte_differenz'] = (
            df_centers_res['vkfl_dichte_planfall']
            - df_centers_res['vkfl_dichte_nullfall'])

        df_centers_res['zentralitaet_planfall'] = (
            100 * df_centers_res['umsatz_planfall_full'] / df_centers_res['kk'])
        df_centers_res['zentralitaet_nullfall'] = (
            100 * df_centers_res['umsatz_nullfall'] / df_centers_res['kk'])
        df_centers_res['zentralitaet_differenz'] = (
            df_centers_res['zentralitaet_planfall']
            - df_centers_res['zentralitaet_nullfall'])

        df_centers_res.replace([np.inf, -np.inf], np.nan, inplace=True)
        df_centers_res.fillna(0, inplace=True)
        self.parent_tbx.dataframe_to_table('Zentren', df_centers_res,
                                           pkeys=['id'])

    def distances_to_db(self, market_id, destinations, distances, beelines):
        # no need to delete, should be dropped at this point anyway
        #self.parent_tbx.delete_rows_in_table(
            #'Beziehungen_Maerkte_Zellen', where='id_markt={}'.format(market_id))
        column_values = {}
        shapes = []
        ids = []
        in_auswahl = []
        for dest in destinations:
            ids.append(dest.id)
            shapes.append(arcpy.Point(dest.x, dest.y))
            in_auswahl.append(dest.in_auswahl)
        column_values['distanz'] = distances
        column_values['luftlinie'] = beelines
        column_values['id_siedlungszelle'] = ids
        column_values['in_auswahl'] = in_auswahl
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
            dest = ZensusCell(x, y, id=cell['id'], in_auswahl=cell['in_auswahl'],
                              epsg=epsg)
            cells.append(dest)
        return cells


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
        p.displayName = u'Projekt'.encode('cp1252')
        p.parameterType = 'Required'
        p.direction = 'Input'
        p.datatype = u'GPString'
        p.value = self.config.active_project
        p.enabled = False

        # markets radius
        p = self.add_parameter('radius_sz')
        p.name = u'radius_sz'
        p.displayName = encode(u'Pufferzone für Siedlungszellen um gewählte '
                               u'Gemeinden festlegen (in m)')
        p.parameterType = 'Required'
        p.direction = 'Input'
        p.datatype = u'GPLong'
        p.filter.type = 'Range'
        p.filter.list = [0, 5000]
        p.value = 2000

        param = self.add_parameter('recalculate')
        param.name = encode(u'Neuberechnung')
        param.displayName = encode(u'Neuberechnung der Distanzen und '
                                   u'Siedlungszellen erzwingen')
        param.parameterType = 'Optional'
        param.direction = 'Input'
        param.datatype = u'GPBoolean'

        return params

    def open(self):
        set_table = 'Settings'
        prev_settings = self.query_table(set_table,
                                         columns='sz_puffer')
        self.par.radius_sz.value = (2000 if len(prev_settings) == 0
                                    else prev_settings[0][0])

    def validate_inputs(self):
        df_markets = self.table_to_dataframe('Maerkte')
        id_nullfall = df_markets['id_betriebstyp_nullfall']
        id_planfall = df_markets['id_betriebstyp_planfall']
        planfall_idx = np.logical_and((id_nullfall != id_planfall),
                                      (id_planfall > 0))
        planfall_markets = df_markets[planfall_idx]
        unset_markets = planfall_markets[planfall_markets['id_kette'] == 0]
        if len(unset_markets) > 0:
            m_str = ''
            for idx, market in unset_markets.iterrows():
                m_str += u'  - "{}"\n'.format(market['name'])
            msg = (u'Bei folgenden geplanten Märkten ist der Anbieter zur Zeit '
                   u'noch unbekannt:\n' + m_str + '\n'
                   u'Bitte setzen sie vor der Berechnung die Anbieter für alle '
                   u'geplanten Märkte (unter Analysieren -> '
                   u'Standortkonkurrenz Supermärkte -> Veränderungen durch '
                   u'Planung -> Geplanten Markt bearbeiten)\n\n')
            return False, msg
        return True, ''

    def _updateParameters(self, params):
        pass

if __name__ == "__main__":
    #from rpctools.utils.spatial_lib import assign_groessenklassen
    #assign_groessenklassen()
    t = TbxProjektwirkungMarkets()
    t.getParameterInfo()
    t.set_active_project()
    t.par.recalculate.value = False
    t.par.radius_sz.value = 0
    t.validate_inputs()
    #t.show_outputs()
    t.execute()

    print 'done'
