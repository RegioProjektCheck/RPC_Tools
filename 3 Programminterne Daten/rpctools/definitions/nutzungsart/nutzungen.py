# -*- coding: utf-8 -*-
import arcpy
import pandas as pd

from rpctools.utils.params import Tool
from rpctools.analyst.standortkonkurrenz.osm_einlesen import Supermarket
from rpctools.analyst.standortkonkurrenz.tbx_osm_markteinlesen import MarktEinlesen


class Nutzungen(Tool):
    _param_projectname = 'projectname'
    _workspace = 'FGDB_Definition_Projekt.gdb'

    def add_outputs(self):
        arcpy.RefreshActiveView()

    def run(self):
        """"""

    def update_wege_flaeche(self, flaechen_id, ways, ways_miv, n_ew=0):
        wege_col = 'Wege_gesamt'
        wege_miv_col = 'Wege_MIV'
        ew_col = 'ew'
        flaechen_table = 'Teilflaechen_Plangebiet'
        flaechen_id_col = 'id_teilflaeche'
        self.parent_tbx.update_table(
            flaechen_table,
            column_values={wege_miv_col: ways_miv.sum(),
                           wege_col: ways.sum(),
                           ew_col: n_ew},
            where='{} = {}'.format(flaechen_id_col, flaechen_id)
        )

    def update_wege_projekt(self):
        '''updates the table "Wege_je_Nutzung" by summing up the calculated
        ways for all areas with Nutzungsart defined for toolbox'''
        flaechen_table = 'Teilflaechen_Plangebiet'
        flaechen_id_col = 'id_teilflaeche'
        wege_table = 'Wege_je_Nutzung'

        nutzungsart = self.parent_tbx._nutzungsart
        flaechen_df = self.parent_tbx.table_to_dataframe(
            flaechen_table, columns=['Wege_gesamt', 'Wege_MIV'],
            where='Nutzungsart={}'.format(nutzungsart))
        ways_sum = flaechen_df['Wege_gesamt'].sum()
        ways_miv_sum = flaechen_df['Wege_MIV'].sum()
        pkw_anteil = (float(ways_miv_sum) / ways_sum) * 100 if ways_sum > 0 else 0
        self.parent_tbx.upsert_row_in_table(
            wege_table,
            {'Wege_gesamt': ways_sum,
             'PKW_Anteil': pkw_anteil},
            {'Nutzungsart': nutzungsart},
            workspace='FGDB_Verkehr.gdb')

    def delete_chronik(self):
        chronik = self.folders.get_table("Chronik_Nutzung", "FGDB_Einnahmen.gdb")
        cursor = arcpy.da.UpdateCursor(chronik, ["Letzte_Nutzung"])
        for row in cursor:
            row[0] = None
            cursor.updateRow(row)
        del cursor


class NutzungenWohnen(Nutzungen):
    BETRACHTUNGSZEITRAUM_JAHRE = 25

    def run(self):
        """"""
        self.update_tables()
        self.delete_chronik()
        self.calculate_we_ways()
        self.update_wege_projekt()

        tfl_table = self.parent_tbx.query_table(
            'Teilflaechen_Plangebiet', columns=['id_teilflaeche', 'Name'],
            where='Nutzungsart = {}'.format(self.parent_tbx._nutzungsart))
        tfl = [t for t in tfl_table]
        arcpy.AddMessage(u'Berechne Entwicklung der Bewohnerzahl '
                         u'der Teilflächen')
        for flaechen_id, name in tfl:
            self.calculate_development(flaechen_id, name)

    def update_tables(self):
        self.parent_tbx.dataframe_to_table(
            'Wohnen_WE_in_Gebaeudetypen',
            self.parent_tbx.df_acc_units,
            ['IDTeilflaeche', 'IDGebaeudetyp'],
            upsert=True)

        self.parent_tbx.dataframe_to_table(
            'Teilflaechen_Plangebiet',
            self.parent_tbx.df_areas, ['id_teilflaeche'],
            upsert=False)


    def calculate_development(self, flaechen_id, name):
        """"""
        tbx = self.parent_tbx

        bewohner_table = 'Bewohner_nach_Altersgruppe_und_Jahr'
        wohnen_struct_table = 'Wohnen_Struktur_und_Alterung_WE'
        ew_base_table = 'Einwohner_pro_WE'
        flaechen_col = 'IDTeilflaeche'
        alter_we_col = 'AlterWE'
        geb_typ_col = 'IDGebaeudetyp'
        id_aclass_col = 'IDAltersklasse'
        aclass_col = 'Altersklasse'
        year_col = 'Jahr'
        ew_col = 'Einwohner'
        wohnungen_col = 'Wohnungen'
        n_bewohner_col = 'Bewohner'

        # empty the bewohner table (results will be stored there)
        tbx.delete_rows_in_table(
            bewohner_table,
            workspace='FGDB_Bewohner_Arbeitsplaetze.gdb',
            where='IDTeilflaeche={}'.format(flaechen_id)
        )

        # get all required tables as dataframes
        bewohner_df = tbx.table_to_dataframe(
            bewohner_table, workspace='FGDB_Bewohner_Arbeitsplaetze.gdb',
            where='IDTeilflaeche={}'.format(flaechen_id)
        )

        ew_base_df = tbx.table_to_dataframe(
            ew_base_table, workspace='FGDB_Bewohner_Arbeitsplaetze_Tool.gdb',
            is_base_table=True)

        # prepare the base table, take duration as age reference for development
        # over years
        ew_base_df['reference'] = 1
        for geb_typ, group in ew_base_df.groupby('IDGebaeudetyp'):
            reference = group[group['AlterWE'] == 3]['Einwohner'].sum()
            ew_base_df.loc[ew_base_df['IDGebaeudetyp'] == geb_typ,
                           'reference'] = reference

        wohnen_struct_df = tbx.table_to_dataframe(
            wohnen_struct_table, pkey={flaechen_col: flaechen_id})

        if len(wohnen_struct_df) == 0:
            arcpy.AddMessage(u'Achtung: Die Wohneinheiten der Fläche "{}" '
                             u'wurden noch nicht definiert. Die Teilfläche '
                             u'wird ignoriert.'.format(name))
            return

        # corresponding SQL: Einwohner_pro_WE INNER JOIN
        # Wohnen_Struktur_und_Alterung_WE ON
        # (Einwohner_pro_WE.AlterWE = Wohnen_Struktur_und_Alterung_WE.AlterWE)
        # AND (Einwohner_pro_WE.IDGebaeudetyp =
        # Wohnen_Struktur_und_Alterung_WE.IDGebaeudetyp)
        joined = wohnen_struct_df.merge(ew_base_df, how='inner',
                                        on=[alter_we_col, geb_typ_col])

        # GROUP BY Wohnen_Struktur_und_Alterung_WE.IDTeilflaeche,
        # Wohnen_Struktur_und_Alterung_WE.Jahr, Einwohner_pro_WE.IDAltersklasse,
        # Einwohner_pro_WE.Altersklasse
        grouped = joined.groupby([year_col, id_aclass_col, aclass_col])

        # make an appendable copy of the (empty) bewohner dataframe
        group_template = bewohner_df.copy()
        # flaechen_id will be the same for all group entries
        group_template[flaechen_col] = [flaechen_id]

        # iterate the groups and set their number of inhabitants etc.
        for g in grouped:
            group = g[1]
            entry = group_template.copy()
            # corresponding SQL:  Sum([Einwohner]*[Wohnungen])
            n_bewohner = (group[ew_col] * group[wohnungen_col]
                          / group['reference']).sum()
            entry[n_bewohner_col] = [n_bewohner]
            entry[id_aclass_col] = group[id_aclass_col].unique()
            entry[aclass_col] = group[aclass_col].unique()
            entry[year_col] = group[year_col].unique()
            bewohner_df = bewohner_df.append(entry)

        tbx.insert_dataframe_in_table(
            bewohner_table, bewohner_df,
            workspace='FGDB_Bewohner_Arbeitsplaetze.gdb')

    def calculate_we_ways(self):
        tbx = self.parent_tbx

        # table and column names
        wohnen_we_table = 'Wohnen_WE_in_Gebaeudetypen'
        geb_typ_table = 'Wohnen_Gebaeudetypen'
        flaechen_table = 'Teilflaechen_Plangebiet'
        wohnen_struct_table = 'Wohnen_Struktur_und_Alterung_WE'
        project_table = 'Projektrahmendaten'
        geb_typ_col = 'IDGebaeudetyp'
        ew_col = 'EW_je_WE'
        reference_col = 'Ew_pro_WE_Referenz'
        cor_factor_col = 'Korrekturfaktor_EW'
        we_col = 'WE'
        wege_je_ew_col = 'Wege_je_Einwohner'
        pkw_perc_col = 'Anteil_Pkw_Fahrer'
        pkey =  'OBJECTID'
        id_flaeche_col = 'IDTeilflaeche'

        # get all required tables as dataframes
        wohnen_we_df = tbx.table_to_dataframe(
            wohnen_we_table, columns=[pkey, ew_col, geb_typ_col,
                                      cor_factor_col, we_col,
                                      id_flaeche_col])

        geb_typ_df = tbx.table_to_dataframe(
            geb_typ_table, workspace='FGDB_Definition_Projekt_Tool.gdb',
                    columns=[geb_typ_col, reference_col, wege_je_ew_col,
                             pkw_perc_col],
                    is_base_table=True)

        ### Korrekturfaktoren ###

        arcpy.AddMessage('Berechne Korrekturfaktoren...')


        joined = pd.merge(wohnen_we_df, geb_typ_df, on=geb_typ_col)
        joined[cor_factor_col] = (joined[ew_col] /
                                  joined[reference_col])

        tbx.dataframe_to_table(wohnen_we_table,
                               joined[[pkey, cor_factor_col]],
                               [pkey])

        ### Calculate ways ###

        arcpy.AddMessage('Berechne Anzahl der Wege...')

        grouped = joined.groupby(id_flaeche_col)
        for g in grouped:
            group = g[1]
            flaechen_id = group[id_flaeche_col].unique()[0]
            n_ew = group[ew_col] * group[we_col]
            n_ways = n_ew * group[wege_je_ew_col]
            n_ways_miv = n_ways * group[pkw_perc_col] / 100
            self.update_wege_flaeche(flaechen_id,
                                     n_ways.sum(), n_ways_miv.sum(),
                                     n_ew.sum())

        ### Structure and age ###

        arcpy.AddMessage('Berechne Wohneinheiten...')
        # empty the table
        tbx.delete_rows_in_table(wohnen_struct_table)
        # empty now, but easier to allocate all fields this way
        wohnen_struct_df = tbx.table_to_dataframe(wohnen_struct_table)
        # calc. structure grouped by flaechen id
        grouped_we = wohnen_we_df.groupby(id_flaeche_col)
        for index, group in grouped_we:
            flaechen_id = group[id_flaeche_col].unique()[0]
            begin, duration = tbx.query_table(
                flaechen_table,
                columns=['Beginn_Nutzung', 'Aufsiedlungsdauer'],
                where='id_teilflaeche={}'.format(flaechen_id))[0]
            end = begin + self.BETRACHTUNGSZEITRAUM_JAHRE - 1
            flaechen_template = pd.DataFrame()
            geb_types = group[geb_typ_col].values
            flaechen_template[geb_typ_col] = geb_types
            flaechen_template[id_flaeche_col] = flaechen_id
            flaechen_template['Wohnungen'] = list(
                group[we_col].values.astype(float) * group[ew_col] / duration)
            for j in range(begin, end + 1):
                for i in range(1, duration + 1):
                    if j - begin + i - duration + 1 > 0:
                        df = flaechen_template.copy()
                        df['Jahr'] = j
                        df['AlterWE'] = j - begin + i - duration + 1
                        wohnen_struct_df = wohnen_struct_df.append(df)
        # is ignored anyway
        #wohnen_struct_df[pkey] = range(1, len(wohnen_struct_df) + 1)
        tbx.insert_dataframe_in_table(wohnen_struct_table, wohnen_struct_df)


class NutzungenGewerbe(Nutzungen):
    BETRACHTUNGSZEITRAUM_JAHRE = 15

    def run(self):
        self.update_tables()
        self.delete_chronik()
        self.calculate_ways()
        self.update_wege_projekt()
        tfl_table = self.parent_tbx.query_table(
            'Teilflaechen_Plangebiet', columns='id_teilflaeche',
            where='Nutzungsart = {}'.format(self.parent_tbx._nutzungsart))
        ids = [i[0] for i in tfl_table]
        arcpy.AddMessage(u'Berechne die Arbeitsplatzentwicklung '
                         u'für die Gewerbeflächen...')
        for flaechen_id in ids:
            self.calculate_growth(flaechen_id)
        arcpy.AddMessage(u'Berechne die Branchenanteile...')
        for flaechen_id in ids:
            self.calculate_percentages(flaechen_id)

    def update_tables(self):
        self.parent_tbx.dataframe_to_table(
            'Gewerbe_Anteile',
            self.parent_tbx.df_shares, ['IDTeilflaeche', 'IDBranche'],
            upsert=True)

        self.parent_tbx.dataframe_to_table(
            'Gewerbe_Arbeitsplaetze',
            self.parent_tbx.df_jobs, ['IDTeilflaeche'],
            upsert=True)

        self.parent_tbx.dataframe_to_table(
            'Teilflaechen_Plangebiet',
            self.parent_tbx.df_areas, ['id_teilflaeche'],
            upsert=False)

    def calculate_growth(self, flaechen_id): ### Structure and age ###
        flaechen_table = 'Teilflaechen_Plangebiet'
        project_table = 'Projektrahmendaten'
        jobs_year_table = 'AP_nach_Jahr'
        results_workspace = 'FGDB_Bewohner_Arbeitsplaetze.gdb'

        tbx = self.parent_tbx

        n_jobs = self.parent_tbx.query_table(
                'Gewerbe_Arbeitsplaetze', columns=['Arbeitsplaetze'])[0][0]

        begin, duration = tbx.query_table(
                flaechen_table,
                columns=['Beginn_Nutzung', 'Aufsiedlungsdauer'],
                where='id_teilflaeche={}'.format(flaechen_id))[0]

        end = begin + self.BETRACHTUNGSZEITRAUM_JAHRE - 1

        # empty the bewohner table (results will be stored there)
        tbx.delete_rows_in_table(jobs_year_table,
                                 where='IDTeilflaeche={}'.format(flaechen_id),
                                 workspace=results_workspace)

        for progress in range(0, end - begin + 1):
            proc_factor = (float(progress + 1) / duration
                           if progress + 1 <= duration
                           else 1)
            year = begin + progress

            tbx.insert_rows_in_table(
                jobs_year_table,
                column_values={
                    'Jahr': year,
                    'AP': n_jobs * proc_factor,
                    'IDTeilflaeche': flaechen_id
                },
                workspace=results_workspace
            )

    def calculate_percentages(self, flaechen_id):
        perc_table = 'Gewerbe_Anteile'
        perc_res_table = 'Branchenanteile'
        results_workspace = 'FGDB_Bewohner_Arbeitsplaetze.gdb'

        tbx = self.parent_tbx
        tbx.delete_rows_in_table(perc_res_table, workspace=results_workspace,
                                 where='IDTeilflaeche={}'.format(flaechen_id))

        perc_table_df = tbx.table_to_dataframe(
            perc_table, where='IDTeilflaeche={}'.format(flaechen_id))
        if len(perc_table_df) == 0:
            return

        perc_res_df = pd.DataFrame()
        perc_res_df['IDBranche'] = perc_table_df['IDBranche']
        perc_res_df['Anteil'] = (
            perc_table_df['dichtekennwert_ap_pro_ha_brutto'] *
            perc_table_df['anteil'])

        perc_res_df['Anteil'] /= perc_res_df['Anteil'].sum()
        perc_res_df['IDTeilflaeche'] = flaechen_id

        tbx.dataframe_to_table(perc_res_table, perc_res_df,
                               ['IDTeilflaeche', 'IDBranche'],
                               workspace=results_workspace, upsert=True)

    def calculate_ways(self):
        pkw_perc_col = 'Anteil_Pkw_Fahrer'
        id_branche_col = 'ID_Branche_ProjektCheck'
        wege_je_besch_col = u'Wege_je_Beschäftigten'
        flaechen_table = 'Teilflaechen_Plangebiet'
        branchen_table = 'Gewerbe_Branchen'
        arbeitsplaetze_table = 'Gewerbe_Arbeitsplaetze'
        id_flaeche_col = 'IDTeilflaeche'
        n_jobs_col = 'anzahl_jobs_schaetzung'
        gew_tablename = 'Gewerbe_Anteile'

        arcpy.AddMessage('Berechne Anzahl der Wege...')


        gew_table_df = self.parent_tbx.table_to_dataframe(gew_tablename)
        gew_table_df.rename(columns={'IDBranche': id_branche_col}, inplace=True)

        branchen_table_df = self.parent_tbx.table_to_dataframe(
            branchen_table, workspace='FGDB_Definition_Projekt_Tool.gdb',
            is_base_table=True)

        arbeitsplaetze_table_df = self.parent_tbx.table_to_dataframe(
            arbeitsplaetze_table)

        joined = gew_table_df.merge(branchen_table_df, on=id_branche_col,
                                    how='inner')

        grouped = joined.groupby(by=id_flaeche_col)
        for flaechen_id, group_data in grouped:
            group_data.fillna(0, inplace=True)
            # the number of jobs as calculated resp. manually input in toolbox
            idx = arbeitsplaetze_table_df[id_flaeche_col] == flaechen_id
            preset = arbeitsplaetze_table_df.loc[idx]['Arbeitsplaetze'].values[0]
            # the calculated number of jobs
            estimated = group_data[n_jobs_col]
            estimated_sum = estimated.sum()
            # difference between calculated and preset values
            cor_factor = preset / estimated_sum if estimated_sum > 0 else 0
            n_ways = estimated * cor_factor * group_data[wege_je_besch_col]
            n_ways_miv = n_ways * group_data[pkw_perc_col] / 100
            self.update_wege_flaeche(flaechen_id, n_ways.sum(), n_ways_miv.sum())


class NutzungenEinzelhandel(Nutzungen):

    def run(self):
        self.update_tables()
        self.delete_chronik()
        self.calculate_ways()
        self.update_wege_projekt()

    def update_tables(self):
        self.parent_tbx.dataframe_to_table(
            'Einzelhandel_Verkaufsflaechen',
            self.parent_tbx.df_sqm,
            ['IDTeilflaeche', 'IDSortiment'],
            upsert=True)

        grouped = self.parent_tbx.df_sqm.groupby(by='IDTeilflaeche')

        arcpy.AddMessage(u'Füge die Lebensmittel-Verkaufsflächen '
                         u'repräsentierende Märkte hinzu...')
        market_tool = MarktEinlesen(projectname=self.projectname)
        do_update_ags = False
        for id, group in grouped:
            idx = self.parent_tbx.df_areas['id_teilflaeche'] == id
            area = self.parent_tbx.df_areas[idx].iloc[0]

            # add a market that corresponds to the area
            # 'Lebensmittel' only
            id_lm = 1
            vkfl_lebensmittel = group[
                group['IDSortiment'] == id_lm]['Verkaufsflaeche_qm'].values[0]
            market_tool.delete_area_market(id)

            if vkfl_lebensmittel > 0:
                name = u'Neuer Lebensmittelmarkt auf Fläche "{}"'.format(
                    area['Name'])
                arcpy.AddMessage(u'  - {} mit {} m² Verkaufsfläche'.format(
                    name, vkfl_lebensmittel))
                x, y = area['SHAPE']
                market = Supermarket(id,
                                     x, y,
                                     name=name,
                                     kette='unbekannt',
                                     vkfl=vkfl_lebensmittel,
                                     id_teilflaeche=id,
                                     epsg=self.parent_tbx.config.epsg)
                market = market_tool.vkfl_to_betriebstyp([market])[0]
                market_tool.markets_to_db([market], planfall=True)
                # market added -> update ags for all markets (no function for
                # single update implemented yet)
                do_update_ags = True

        self.parent_tbx.dataframe_to_table(
            'Teilflaechen_Plangebiet',
            self.parent_tbx.df_areas, ['id_teilflaeche'],
            upsert=False)

        if do_update_ags:
            arcpy.AddMessage(u'Aktualisiere die AGS der Märkte...')
            market_tool.set_ags()

    def calculate_ways(self):
        besucher_sqm_col = 'Besucher_je_qm_Vfl'
        pkw_perc_col = 'Anteil_Pkw_Fahrer'
        id_sort_col = 'IDSortiment'
        vfl_col = 'Verkaufsflaeche_qm'
        wege_je_besucher_col = 'Wege_je_Besucher'
        id_flaeche_col = 'IDTeilflaeche'
        vfl_tablename = 'Einzelhandel_Verkaufsflaechen'
        sortimente_tablename = 'Einzelhandel_Sortimente'

        arcpy.AddMessage('Berechne Anzahl der Wege...')

        vfl_table_df = self.parent_tbx.table_to_dataframe(vfl_tablename)
        sortimente_df = self.parent_tbx.table_to_dataframe(
            sortimente_tablename, workspace='FGDB_Definition_Projekt_Tool.gdb',
            is_base_table=True)
        # column names of the ids differ -> rename one of them
        sortimente_df.rename(
            columns={'ID_Sortiment_ProjektCheck': id_sort_col}, inplace=True)
        joined = vfl_table_df.merge(sortimente_df, on=id_sort_col,
                                    how='inner')

        grouped = joined.groupby(by=id_flaeche_col)
        for g in grouped:
            group = g[1]
            flaechen_id = group[id_flaeche_col].unique()[0]
            n_ways = (group[vfl_col] *
                      group[besucher_sqm_col] *
                      group[wege_je_besucher_col])
            n_ways_miv = n_ways * group[pkw_perc_col] / 100
            self.update_wege_flaeche(flaechen_id, n_ways.sum(), n_ways_miv.sum())
