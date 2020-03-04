# -*- coding: utf-8 -*-

import sys

from os.path import abspath, dirname, join
import numpy as np
import arcpy
import datetime
import pandas as pd

from rpctools.utils.params import Tbx
from rpctools.utils.constants import Nutzungsart
from rpctools.utils.encoding import encode
from rpctools.definitions.projektverwaltung.tbx_teilflaechen_verwalten import \
     TbxFlaechendefinition
from rpctools.definitions.nutzungsart.nutzungen import (
    NutzungenGewerbe, NutzungenWohnen, NutzungenEinzelhandel)
from rpctools.utils.encoding import encode
from rpctools.utils.constants import Branche, Gewerbegebietstyp
from rpctools.utils.spatial_lib import get_gemeindetyp
from rpctools.utils.basetable_definitions import (
    Gebaeudetyp, Gebaeudetypen, Sortiment, Sortimente, Branche, Branchen)
from collections import OrderedDict


class TbxNutzungen(TbxFlaechendefinition):
    _label = u'Detailangaben zur Nutzung "{name}"'
    _nutzungsart = Nutzungsart.UNDEFINIERT
    _duration_heading = None
    _displayname_begin = u'Beginn der Aufsiedlung (Jahreszahl)'
    _max_duration = 20

    @property
    def label(self):
        return self._label

    def _getParameterInfo(self):
        super(TbxNutzungen, self)._getParameterInfo()

        # Beginn der Aufsiedlung (Jahreszahl)
        param = self.add_parameter('bezugsbeginn')
        param.name = u'Beginn_der_Aufsiedlung__Jahreszahl_'
        param.displayName = self._displayname_begin
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.filter.type = 'Range'
        # ToDo: Jahre an die Jahre der Projektdefinition anpassen
        param.filter.list = [2010, 2050]
        param.category = self._duration_heading

        param.value = datetime.datetime.now().year + 1

        # Dauer des Bezugs (Jahre, 1 = Bezug wird noch im Jahr des
        # Bezugsbeginns abgeschlossen)
        param = self.add_parameter('dauer_aufsiedlung')
        param.name = u'dauer_aufsiedlung'
        param.displayName = (u'Dauer des Bezugs (Jahre, 1 = Bezug wird noch '
                             u'im Jahr des Bezugsbeginns abgeschlossen)')
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = 1
        param.filter.type = 'Range'
        param.filter.list = [1, self._max_duration]
        param.category = self._duration_heading

        return self.par

    def set_selected_area(self):
        area, i = self.get_selected_area()
        if 'bezugsbeginn' in self.par:
            self.par.bezugsbeginn.value = int(area['Beginn_Nutzung'])
        if 'dauer_aufsiedlung' in self.par:
            self.par.dauer_aufsiedlung.value = int(area['Aufsiedlungsdauer'])

    def _updateParameters(self, params):
        area, idx = self.get_selected_area()
        if area is None:
            return params

        if self.par.changed('area'):
            self.set_selected_area()

        elif 'bezugsbeginn' in self.par and self.par.changed('bezugsbeginn'):
            self.df_areas.loc[idx, 'Beginn_Nutzung'] = self.par.bezugsbeginn.value
        elif ('dauer_aufsiedlung' in self.par and
            self.par.changed('dauer_aufsiedlung')):
            self.df_areas.loc[idx, 'Aufsiedlungsdauer'] = \
                self.par.dauer_aufsiedlung.value
        return params


class TbxNutzungenWohnen(TbxNutzungen):
    _label = TbxNutzungen._label.format(sub='a', name='Wohnen')
    _nutzungsart = Nutzungsart.WOHNEN
    _duration_heading = "1) Bezugszeitraum"
    _displayname_begin = u'Beginn des Bezugs (Jahreszahl)'

    ew_je_we_range = [r / 10.0 for r in range(10, 50)]

    def __init__(self):
        super(TbxNutzungenWohnen, self).__init__()
        self.gebaeudetypen = Gebaeudetypen(self.folders)

    @property
    def Tool(self):
        return NutzungenWohnen

    def _getParameterInfo(self):
        params = super(TbxNutzungenWohnen, self)._getParameterInfo()

        # specific parameters for "Wohnen"
        heading = encode(u"2) Anzahl Wohneinheiten nach Gebäudetypen")

        # Wohntyp auswaehlen
        param = self.add_parameter('wohntyp')
        param.name = u'Wohntyp'
        param.displayName = encode(u'Anzahl an Wohneinheiten über Gebietstyp schaetzen')
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'GPString'
        param.filter.list = ["Einfamilienhäuser auf großen Grundstücken",
                             "Einfamilienhausgebiet mit wenigen Doppelhäusern" ,
                             "Einzel-, Doppel- und Reihenhäuser",
                             "Doppel-, Reihen- und Mehrfamilienhäuser",
                             "Reihenhäuser und Stadtvillen",
                             "Geschosswohnungsbau",
                             "Benutzerdefiniert"]
        param.value = param.filter.list[6]
        param.category = heading

        # Anzahl WE in Gebäudetypen
        for gt in self.gebaeudetypen.itervalues():
            assert isinstance(gt, Gebaeudetyp)
            param = self.add_parameter(gt.param_we)
            param.name = encode(u'Bewohner {}'.format(gt.display_name))
            param.displayName = encode(u'Anzahl WE in {}'.format(gt.display_name))
            param.parameterType = 'Required'
            param.direction = 'Input'
            param.datatype = u'Long'
            param.value = u'0'
            param.filter.type = 'Range'
            param.filter.list = [0, 1000]
            param.category = heading

        heading = ("3) Mittlere Anzahl Einwohner pro Wohneinheit " +
                   "(3 Jahre nach Bezug)")

        for gt in self.gebaeudetypen.itervalues():
            assert isinstance(gt, Gebaeudetyp)
            # Mittlere Anzahl Einwohner pro WE in Einfamilienhäusern
            # (kurz nach dem Bezug)
            param = self.add_parameter(gt.param_ew_je_we)
            param.name = encode(u'EW_JE_WE {}'.format(gt.display_name))
            param.displayName = encode(u'... in {}'.format(gt.display_name))
            param.parameterType = 'Required'
            param.direction = 'Input'
            param.datatype = u'GPDouble'
            param.value = gt.default_ew_je_we
            param.filter.list = self.ew_je_we_range
            param.category = heading

        heading = encode(u"4) Anteil an unter 18-jährigen nach Gebäudetyp")

        # Anteil u18 nach Gebäudetyp
        for gt in self.gebaeudetypen.itervalues():
            param = self.add_parameter(gt.param_anteil_u18)
            param.name = encode(u'U18 {}'.format(gt.display_name))
            param.displayName = encode(u'Anteil an unter 18-Jährigen in  {}'
                                       .format(gt.display_name))
            param.parameterType = 'Required'
            param.direction = 'Input'
            param.datatype = u'Long'
            param.filter.type = 'Range'
            param.value = gt.default_anteil_u18
            param.filter.list = [0, 60]
            param.category = heading

        return params

    def _open(self, params):
        self.df_acc_units = self.get_accommodation_units()
        super(TbxNutzungenWohnen, self)._open(params)

    def get_accommodation_units(self):
        df_acc_units = self.table_to_dataframe(
            'Wohnen_WE_in_Gebaeudetypen')
        return df_acc_units

    def set_selected_area(self):
        """update all inputs based on currently selected area"""
        super(TbxNutzungenWohnen, self).set_selected_area()
        area, idx = self.get_selected_area()

        acc_idx = self.df_acc_units['IDTeilflaeche'] == area['id_teilflaeche']
        rows = self.df_acc_units[acc_idx]
        # if there are no values defined yet, set to default values
        if len(rows) == 0:
            columns=['IDTeilflaeche', 'IDGebaeudetyp',
                     'WE', 'EW_je_WE', 'Anteil_U18']
            for gt in self.gebaeudetypen.itervalues():
                we = 0
                ew_je_we = gt.default_ew_je_we
                u18 = gt.default_anteil_u18
                self.par[gt.param_we].value = we
                self.par[gt.param_ew_je_we].value = ew_je_we
                self.par[gt.param_anteil_u18].value = u18
                row = pd.DataFrame([[area['id_teilflaeche'], gt.typ_id,
                                     we, ew_je_we, u18]],
                                   columns=columns)
                self.df_acc_units = self.df_acc_units.append(
                    row, ignore_index=True)

        else:
            # update values
            for index, row in rows.iterrows():
                gt = self.gebaeudetypen[row['IDGebaeudetyp']]
                self.par[gt.param_we].value = row['WE']
                self.par[gt.param_ew_je_we].value = row['EW_je_WE']
                self.par[gt.param_anteil_u18].value = row['Anteil_U18']

    def _update_row(self, area, geb_typ, key, value):
        area_id = area['id_teilflaeche']
        row_idx = ((self.df_acc_units['IDTeilflaeche'] == area['id_teilflaeche']).values &
                   (self.df_acc_units['IDGebaeudetyp'] == geb_typ).values)
        self.df_acc_units.loc[row_idx, key] = value

    def _updateParameters(self, params):
        params = super(TbxNutzungenWohnen, self)._updateParameters(params)
        area, area_idx = self.get_selected_area()
        if area is None:
            return params

        we_changed = False

        # Note CF: actually this should be done with relation to existing
        # building types like below
        if params.changed('wohntyp') and params.wohntyp.value != "Benutzerdefiniert":
            fields = ['NAME', 'IDGebietstyp']
            tbl_areas = self.folders.get_table('Teilflaechen_Plangebiet', 'FGDB_Definition_Projekt.gdb')
            cursor_areas = arcpy.da.UpdateCursor(tbl_areas, fields)
            for area in cursor_areas:
                if area[0] == self.par['area'].value:
                    area[1] = self.par['wohntyp'].value
                cursor_areas.updateRow(area)
            
            tbl_teilflaechen = self.folders.get_table("Teilflaechen_Plangebiet", 'FGDB_Definition_Projekt.gdb')
            tbl_teilflaechen = tbl_teilflaechen[ 'NAME' == self.par['area'].value]
            area, i = self.get_selected_area()
            tfl_hektar = area['Flaeche_ha']
            tbl_we_typ = self.table_to_dataframe(
                'WE_nach_Gebietstyp',
                workspace='FGDB_Definition_Projekt_Tool.gdb',
                is_base_table=True
            )
            tbl_we_typ = tbl_we_typ.loc[tbl_we_typ['Gebietstyp'] == params.wohntyp.value]
            anzahl_efh = int(tbl_we_typ.iloc[0].loc["WE_pro_Hektar"] * tfl_hektar)
            anzahl_dh = int(tbl_we_typ.iloc[1].loc["WE_pro_Hektar"] * tfl_hektar)
            anzahl_rh = int(tbl_we_typ.iloc[2].loc["WE_pro_Hektar"] * tfl_hektar)
            anzahl_mfh = int(tbl_we_typ.iloc[3].loc["WE_pro_Hektar"] * tfl_hektar)
            self.par[5].value = anzahl_efh
            self.par[6].value = anzahl_dh
            self.par[7].value = anzahl_rh
            self.par[8].value = anzahl_mfh
            self._update_row(area, 1, 'WE', anzahl_efh)
            self._update_row(area, 2, 'WE', anzahl_dh)
            self._update_row(area, 3, 'WE', anzahl_rh)
            self._update_row(area, 4, 'WE', anzahl_mfh)
            we_changed = True

        for gt in self.gebaeudetypen.itervalues():
            if params.changed(gt.param_we):
                self._update_row(area, gt.typ_id, 'WE',
                                 self.par[gt.param_we].value)
                we_changed = True
            elif params.changed(gt.param_ew_je_we):
                self._update_row(area, gt.typ_id, 'EW_je_WE',
                                 self.par[gt.param_ew_je_we].value)
            elif params.changed(gt.param_anteil_u18):
                self._update_row(area, gt.typ_id, 'Anteil_U18',
                                 self.par[gt.param_anteil_u18].value)

        if we_changed:
            if not params.changed('wohntyp'):
                params.wohntyp.value = "Benutzerdefiniert"
            we_idx = self.df_acc_units['IDTeilflaeche'] == area['id_teilflaeche']
            sums = self.df_acc_units[we_idx]['WE'].sum()
            self.df_areas.loc[area_idx, 'WE_gesamt'] = sums
            self.update_pretty_name()

        return params


class TbxNutzungenGewerbe(TbxNutzungen):
    _label = TbxNutzungen._label.format(sub='b', name='Gewerbe')
    _nutzungsart = Nutzungsart.GEWERBE
    _duration_heading = "1) Bezugszeitraum"
    _displayname_begin = u'Beginn des Bezugs (Jahreszahl)'
    _max_duration = 15

    # Default Gewerbegebietstyp
    _default_typ_id = 2

    def __init__(self):
        super(TbxNutzungenGewerbe, self).__init__()
        self.branchen = Branchen(self.folders)

    @property
    def Tool(self):
        return NutzungenGewerbe

    def _getParameterInfo(self):
        params = super(TbxNutzungenGewerbe, self)._getParameterInfo()

        self.df_comm_types = self.table_to_dataframe(
            'Gewerbegebietstypen',
            workspace='FGDB_Definition_Projekt_Tool.gdb',
            is_base_table=True
        )

        # extend the commercial types
        default_idx = self.df_comm_types['IDGewerbegebietstyp'] == self._default_typ_id
        self.df_comm_types.loc[default_idx, 'Name_Gewerbegebietstyp'] += ' (default)'
        custom_row = pd.DataFrame(columns=self.df_comm_types.columns)
        custom_row['IDGewerbegebietstyp'] = [Gewerbegebietstyp.BENUTZERDEFINIERT]
        custom_row['Name_Gewerbegebietstyp'] = ['Benutzerdefiniert']
        self.df_comm_types = self.df_comm_types.append(
            custom_row, ignore_index=True).sort('IDGewerbegebietstyp')

        self.df_presets = self.table_to_dataframe(
            'Vorschlagswerte_Branchenstruktur',
            workspace='FGDB_Definition_Projekt_Tool.gdb',
            is_base_table=True
        )

        self.df_density = self.table_to_dataframe(
            'Dichtekennwerte_Gewerbe',
            workspace='FGDB_Definition_Projekt_Tool.gdb',
            is_base_table=True
        )

        heading = u"2) Voraussichtlicher Anteil der Branchen an der Nettofläche"

        # Gebietstyp auswählen
        param = self.add_parameter('gebietstyp')
        param.name = u'Gebietstyp'
        param.displayName = encode(u'Gebietstyp auswählen')
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'GPString'

        param.filter.list = self.df_comm_types['Name_Gewerbegebietstyp'].values.tolist()
        param.value = param.filter.list[0]
        param.category = heading

        # remember params
        sum_params = []

        for branche in self.branchen.itervalues():
            assert isinstance(branche, Branche)
            param = self.add_parameter(branche.param_gewerbenutzung)
            param.name = encode(encode(branche.name))
            param.displayName = encode(
                u'{} (in % der Nettofläche)'.format(branche.name))
            param.parameterType = 'Required'
            param.direction = 'Input'
            param.datatype = u'Long'
            param.value = branche.default_gewerbenutzung
            param.filter.type = 'Range'
            param.filter.list = [0, 100]
            param.category = heading
            sum_params.append(branche.param_gewerbenutzung)

        self.add_dependency(sum_params, 100)

        heading = u'3) Voraussichtliche Anzahl an Arbeitsplätzen'

        # Arbeitsplatzzahl schätzen
        param = self.add_parameter('auto')
        param.name = u'Arbeitsplatzzahl schätzen'
        param.displayName = encode(u'Vorgehen zur Schätzung der Zahl der '
                                   u'Arbeitsplätze nach Vollbezug')
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'GPString'
        param.filter.list = [u'Eigenen Wert eingeben',
                             u'Arbeitsplatzzahl automatisch schätzen']
        param.value = param.filter.list[0]
        param.category = heading

        # Arbeitsplätze insgesamt
        param = self.add_parameter('arbeitsplaetze_insgesamt')
        param.name = u'Arbeitsplätze insgesamt'
        param.displayName = encode(u'Schätzung der Zahl der Arbeitsplätze '
                                   u'nach Vollbezug (Summe über alle '
                                   u'Branchen)')
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'GPLong'
        param.category = heading
        param.enabled = False
        param.filter.type = 'Range'
        param.filter.list = [0, 10000]

        return params

    def _open(self, params):
        self.df_shares = self.get_shares()
        self.df_jobs = self.table_to_dataframe('Gewerbe_Arbeitsplaetze')
        super(TbxNutzungenGewerbe, self)._open(params)

    def add_community_types(self):
        for index, area in self.df_areas.iterrows():
            g_typ = get_gemeindetyp(area['ags_bkg'])
            self.df_areas.loc[index, 'gemeindetyp'] = g_typ

    def get_shares(self):
        df_shares = self.table_to_dataframe(
            'Gewerbe_Anteile')
        return df_shares

    def set_gewerbe_presets(self, id_gewerbe):
        """set all branche values to db-presets of given gewerbe-id"""
        idx = self.df_presets['IDGewerbegebietstyp'] == id_gewerbe
        presets = self.df_presets[idx]
        for branche in self.branchen.itervalues():
            param = self.par[branche.param_gewerbenutzung]
            p_idx = presets['ID_Branche_ProjektCheck'] == branche.id
            param.value = int(presets[p_idx]['Vorschlagswert_in_Prozent'].values[0])

    def _update_shares(self, area):
        area_id = area['id_teilflaeche']
        a_idx = self.df_shares['IDTeilflaeche'] == area['id_teilflaeche']
        for branche in self.branchen.itervalues():
            row_idx = a_idx & (self.df_shares['IDBranche'] == branche.id)
            share = self.par[branche.param_gewerbenutzung].value
            data = {
                'IDTeilflaeche': area_id,
                'IDBranche': branche.id,
                'anteil': share,
                'dichtekennwert_ap_pro_ha_brutto': branche.jobs_per_ha,
                'anzahl_jobs_schaetzung': branche.estimated_jobs
            }
            # row doesn't exist -> create new one and append it
            if row_idx.sum() == 0:
                row = pd.DataFrame(data, index=[0])
                self.df_shares = self.df_shares.append(row, ignore_index=True)
            else:
                for k, v in data.iteritems():
                    self.df_shares.loc[row_idx, k] = v

    def _updateParameters(self, params):
        params = super(TbxNutzungenGewerbe, self)._updateParameters(params)
        area, area_idx = self.get_selected_area()
        if area is None:
            return params
        altered = False

        # set presets
        if self.par.changed('gebietstyp'):
            comm_idx = (self.df_comm_types['Name_Gewerbegebietstyp'] ==
                        params.gebietstyp.value)
            id_gewerbe = self.df_comm_types[comm_idx][
                'IDGewerbegebietstyp'].values[0]
            if id_gewerbe != Gewerbegebietstyp.BENUTZERDEFINIERT:
                self.set_gewerbe_presets(id_gewerbe)
                altered = True
                self.df_areas.loc[area_idx, 'IDGebietstyp'] = self.df_comm_types[comm_idx]['Name_Gewerbegebietstyp'].values[0]    
        # check if one of the branchenanteile changed
        elif self.par.changed(*[branche.param_gewerbenutzung
                      for branche in self.branchen.values()]):
            # set selection to "benutzerdefiniert" and recalc. jobs
            self.par.gebietstyp.value = self.par.gebietstyp.filter.list[0]
            altered = True

        auto_idx = self.par.auto.filter.list.index(
            self.par.auto.value)

        if self.par.changed('auto'):
            # auto calc. entry
            if auto_idx:
                altered = True
                params.arbeitsplaetze_insgesamt.enabled = False
            # manual entry
            else:
                params.arbeitsplaetze_insgesamt.enabled = True

        if altered and auto_idx:
            n_jobs = self.estimate_jobs()
            params.arbeitsplaetze_insgesamt.value = n_jobs

        if self.par.changed('arbeitsplaetze_insgesamt') or altered:
            idx = self.df_jobs['IDTeilflaeche'] == area['id_teilflaeche']
            n_jobs = params.arbeitsplaetze_insgesamt.value
            self.df_jobs.loc[idx, 'Arbeitsplaetze'] = n_jobs
            self.df_jobs.loc[idx, 'ist_geschaetzt'] = auto_idx
            self.df_areas.loc[area_idx, 'AP_gesamt'] = n_jobs
            self._update_shares(area)
            self.update_pretty_name()

        return params

    def estimate_jobs(self):
        """calculate estimation of number of jobs
        sets estimated jobs to branchen"""
        area, idx = self.get_selected_area()
        jobs_sum = 0

        if 'gemeindetyp' not in self.df_areas.columns:
            self.add_community_types()
            area, idx = self.get_selected_area()
        gemeindetyp = area['gemeindetyp']

        df_kennwerte = self.df_density[
            self.df_density['Gemeindetyp_ProjektCheck'] == gemeindetyp]
        for branche in self.branchen.itervalues():
            param = self.par[branche.param_gewerbenutzung]
            idx = df_kennwerte['ID_Branche_ProjektCheck'] == branche.id
            branche.jobs_per_ha = df_kennwerte[idx]['AP_pro_ha_brutto'].values[0]
            jobs_branche = (area['Flaeche_ha'] *
                            (param.value / 100.) *
                            branche.jobs_per_ha)
            branche.estimated_jobs = jobs_branche
            jobs_sum += jobs_branche

        return jobs_sum

    def set_selected_area(self):
        """update all inputs based on currently selected area"""
        super(TbxNutzungenGewerbe, self).set_selected_area()
        area, idx = self.get_selected_area()
        share_idx = self.df_shares['IDTeilflaeche'] == area['id_teilflaeche']
        rows = self.df_shares[share_idx]
        # if there are no values defined yet, set to default values
        if len(rows) == 0:
            self.set_gewerbe_presets(self._default_typ_id)
            self._update_shares(area)
        # update values
        else:
            for index, row in rows.iterrows():
                branche = self.branchen[row['IDBranche']]
                self.par[branche.param_gewerbenutzung].value = int(row['anteil'])

        # get number of jobs
        job_idx = self.df_jobs['IDTeilflaeche'] == area['id_teilflaeche']
        rows = self.df_jobs[job_idx]
        if len(rows) == 0:
            columns=['IDTeilflaeche', 'Arbeitsplaetze']
            n_jobs = self.estimate_jobs()
            row = pd.DataFrame([[area['id_teilflaeche'], n_jobs]],
                               columns=columns)
            self.df_jobs = self.df_jobs.append(row, ignore_index=True)
            self.par.auto.value = self.par.auto.filter.list[1]
        else:
            self.par.auto.value = self.par.auto.filter.list[1] \
                if rows['ist_geschaetzt'].values[0] \
                else self.par.auto.filter.list[0]
            n_jobs = int(rows['Arbeitsplaetze'].values[0])

        auto_idx = self.par.auto.filter.list.index(
            self.par.auto.value)
        # not custom settings -> estimate
        if auto_idx:
            n_jobs = self.estimate_jobs()
            self.par.arbeitsplaetze_insgesamt.enabled = False
        else:
            self.par.arbeitsplaetze_insgesamt.enabled = True

        self.par.arbeitsplaetze_insgesamt.value = n_jobs
        self.df_areas.loc[idx, 'AP_gesamt'] = n_jobs
        self.update_pretty_name()
        self.par.gebietstyp.value = self.par.gebietstyp.filter.list[0]


class TbxNutzungenEinzelhandel(TbxNutzungen):
    _label = TbxNutzungen._label.format(sub='c', name='Einzelhandel')
    _nutzungsart = Nutzungsart.EINZELHANDEL
    _duration_heading = '1) Voraussichtliche Eröffnung'
    _displayname_begin = u'Eröffnung'

    @property
    def Tool(self):
        return NutzungenEinzelhandel

    def __init__(self):
        super(TbxNutzungenEinzelhandel, self).__init__()
        self.sortimente = Sortimente(self.folders)

    def _getParameterInfo(self):
        params = super(TbxNutzungenEinzelhandel, self)._getParameterInfo()
        # no duration needed as the shops are assumed to be finished instantly
        self.remove_parameter('dauer_aufsiedlung')
        self.remove_parameter('bezugsbeginn')

        for srt in self.sortimente.itervalues():
            assert isinstance(srt, Sortiment)
            # Verkaufsfläche nach Sortiment
            param = self.add_parameter(srt.param_vfl)
            param.name = encode(srt.kurzname)
            param.displayName = encode(u'{} (Verkaufsfläche in qm)'.format(srt.name))
            param.parameterType = 'Required'
            param.direction = 'Input'
            param.datatype = u'Long'
            param.value = u'0'
            param.filter.type = 'Range'
            param.filter.list = [0, 20000]

        return params

    def _open(self, params):
        self.df_sqm = self.get_sqm()
        super(TbxNutzungenEinzelhandel, self)._open(params)

    def get_sqm(self):
        df_sales_areas = self.table_to_dataframe(
            'Einzelhandel_Verkaufsflaechen')
        return df_sales_areas

    def set_selected_area(self):
        """update all inputs based on currently selected area"""
        super(TbxNutzungenEinzelhandel, self).set_selected_area()
        area, idx = self.get_selected_area()

        sales_idx = self.df_sqm['IDTeilflaeche'] == area['id_teilflaeche']
        rows = self.df_sqm[sales_idx]
        # if there are no values defined yet, set to default values
        if len(rows) == 0:
            columns=['IDTeilflaeche', 'IDSortiment', 'Verkaufsflaeche_qm']
            for srt in self.sortimente.itervalues():
                self.par[srt.param_vfl].value = 0
                row = pd.DataFrame([[area['id_teilflaeche'], srt.typ_id, 0]],
                                   columns=columns)
                self.df_sqm = self.df_sqm.append(
                    row, ignore_index=True)

        else:
            # update values
            for index, row in rows.iterrows():
                srt = self.sortimente[row['IDSortiment']]
                self.par[srt.param_vfl].value = row['Verkaufsflaeche_qm']

    def _update_row(self, area, srt_typ, sqm):
        area_id = area['id_teilflaeche']
        row_idx = ((self.df_sqm['IDTeilflaeche'] == area['id_teilflaeche']).values &
                   (self.df_sqm['IDSortiment'] == srt_typ).values)
        self.df_sqm.loc[row_idx, 'Verkaufsflaeche_qm'] = sqm

    def _updateParameters(self, params):
        params = super(TbxNutzungenEinzelhandel, self)._updateParameters(params)
        area, area_idx = self.get_selected_area()
        if area is None:
            return params

        altered = False
        for srt in self.sortimente.itervalues():
            if params.changed(srt.param_vfl):
                sqm = self.par[srt.param_vfl].value
                self._update_row(area, srt.typ_id, sqm)
                altered = True

        if altered:
            sqm_idx = self.df_sqm['IDTeilflaeche'] == area['id_teilflaeche']
            sums = self.df_sqm[sqm_idx]['Verkaufsflaeche_qm'].sum()
            self.df_areas.loc[area_idx, 'VF_gesamt'] = sums
            self.update_pretty_name()
        return params

if __name__ == '__main__':
    t = TbxNutzungenWohnen()
    t.getParameterInfo()
    t.set_active_project()
    t.validate_inputs()
    t.open()
    t._updateParameters(t.par)
    t.execute()
    #t = TbxNutzungenGewerbe()
    #t.getParameterInfo()
    #t.set_active_project()
    #t.validate_inputs()
    #t.open()
    #t._updateParameters(t.par)
    #t.execute()
    #t.commit_tfl_changes()
    #t.tool.calculate_ways()
    #t.tool.update_wege_projekt()
    #t.tool.main(t.par, None)
    #df = t.table_to_dataframe('Teilflaechen_Plangebiet',
                              #workspace='FGDB_Definition_Projekt.gdb')
    #t.table_to_dataframe('Wohnen_WE_in_Gebaeudetypen', columns=None)
    #t.print_test_parameters()
    #t.print_tool_parameters()
    #t.updateParameters(params)
    #t.updateMessages(params)
    #t.print_test_parameters()
