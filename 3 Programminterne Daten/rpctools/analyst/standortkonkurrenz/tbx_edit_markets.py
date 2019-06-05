# -*- coding: utf-8 -*-
import arcpy

from rpctools.utils.params import Tbx, Tool
from rpctools.utils.encoding import encode
from rpctools.utils.spatial_lib import closest_point, get_ags
import numpy as np
import pandas as pd

NULLFALL = 0
PLANFALL = 1
CHANGE = 2


class EditMarkets(Tool):
    _param_projectname = 'projectname'
    _workspace = 'FGDB_Standortkonkurrenz_Supermaerkte.gdb'

    def add_outputs(self):
        pass

    def run(self):
        markets_df = self.parent_tbx.markets_df
        # check which markets should be deleted, the other ones will be updated
        delete_df = markets_df.loc[markets_df['do_delete'] == True]
        update_df = markets_df.loc[markets_df['do_delete'] == False]

        # deletions
        if len(delete_df) > 0:
            arcpy.AddMessage(u'Lösche Märkte')
        for idx, market in delete_df.iterrows():
            arcpy.AddMessage(u' - {}'.format(market['pretty']))
            self.parent_tbx.delete_rows_in_table(
                'Maerkte',
                where='id={}'.format(market['id']))
            self.parent_tbx.delete_rows_in_table(
                'Beziehungen_Maerkte_Zellen',
                where='id_markt={}'.format(market['id']))

        # updates
        arcpy.AddMessage(u'Schreibe Änderungen in Datenbank...')
        self.parent_tbx.dataframe_to_table('Maerkte', update_df,
                                           ['id'], upsert=False)
        arcpy.RefreshActiveView()


class TbxEditMarkets(Tbx):
    setting = None
    _label = ''

    @property
    def label(self):
        return self._label

    @property
    def Tool(self):
        return EditMarkets

    def _getParameterInfo(self):

        # Projekt_auswählen
        param = self.add_parameter('projectname')
        param.name = encode(u'Projekt_auswählen')
        param.displayName = encode(u'Projekt')
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'GPString'
        param.filter.list = []

        param = self.add_parameter('markets')
        param.name = encode(u'Märkte')
        param.displayName = encode(u'Markt auswählen')
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'GPString'
        param.filter.list = []

        self.df_chains = self.table_to_dataframe(
            'Ketten',
            workspace='FGDB_Standortkonkurrenz_Supermaerkte_Tool.gdb',
            is_base_table=True
        )

        if self.setting != CHANGE:
            param = self.add_parameter('name')
            param.name = encode(u'Name')
            param.displayName = encode(u'Name des Marktes')
            param.parameterType = 'Required'
            param.direction = 'Input'
            param.datatype = u'GPString'

            # Handelsketten

            param = self.add_parameter('chain')
            param.name = encode(u'Kette')
            param.displayName = encode(u'Anbieter')
            param.parameterType = 'Required'
            param.direction = 'Input'
            param.datatype = u'GPString'
            param.filter.list = sorted(self.df_chains['name'].values.tolist())

        # Betriebstypen

        self.df_types = self.table_to_dataframe(
            'Betriebstypen',
            workspace='FGDB_Standortkonkurrenz_Supermaerkte_Tool.gdb',
            is_base_table=True
        )

        # list pretty names for Betriebstypen
        pretty_names = []
        for idx, typ in self.df_types.iterrows():
            details = ''
            lower = typ['von_m2']
            upper = typ['bis_m2']
            if not np.isnan(lower):
                details = u'(ab {} m²'.format(lower)
                if not np.isnan(upper):
                    details += u' bis {} m²'.format(upper)
                details += u' Verkaufsfläche)'
                details.replace('.', ',')
            pretty = u'{name} {details}'.format(name=typ['name'],
                                                details=details)
            pretty_names.append(pretty)
        self.df_types['pretty'] = pretty_names

        # add a row for closing markets
        if self.setting == CHANGE:
            # extend the commercial types
            custom_row = pd.DataFrame(columns=self.df_types.columns)
            custom_row['id_betriebstyp'] = [0]
            custom_row['pretty'] = custom_row['name'] = [u'Schließung']
            self.df_types = self.df_types.append(
                custom_row, ignore_index=True).sort_values(by='id_betriebstyp')

        param = self.add_parameter('type_name')
        param.name = encode(u'Betriebstyp')
        param.displayName = encode(u'Betriebstyp')
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'GPString'
        param.filter.list = self.df_types['pretty'].values.tolist()

        if self.setting != CHANGE:
            param = self.add_parameter('do_delete')
            param.name = encode(u'Löschen')
            param.displayName = encode(u'Markt entfernen')
            param.parameterType = 'Optional'
            param.direction = 'Input'
            param.datatype = u'GPBoolean'

            param = self.add_parameter('delete_all')
            param.name = encode(u'Alle Löschen')
            param.displayName = encode(u'Alle Märkte entfernen')
            param.parameterType = 'Optional'
            param.direction = 'Input'
            param.datatype = u'GPBoolean'

        else:
            param = self.add_parameter('do_close')
            param.name = encode(u'close')
            param.displayName = encode(u'Markt schließen')
            param.parameterType = 'Optional'
            param.direction = 'Input'
            param.datatype = u'GPBoolean'

        self.markets_df = []
        return self.par

    def get_markets(self):
        '''return the markets in db as a dataframe, filtered by existance
        in nullfall and planfall (dependent on setting of this toolbox)'''
        df_markets = self.table_to_dataframe('Maerkte')
        if len(df_markets) == 0:
            return df_markets
        id_nullfall = df_markets['id_betriebstyp_nullfall']
        id_planfall = df_markets['id_betriebstyp_planfall']
        nullfall_idx = id_nullfall > 0
        if self.setting in [NULLFALL, CHANGE]:
            return df_markets[nullfall_idx]
        else:
            return df_markets[np.logical_not(nullfall_idx)]

    def add_market_to_db(self, name, coords):
        '''add a market to the database located in given coordinates
        (if market becomes planfall or nullfall depends on setting of toolbox)
        '''
        # take ALL markets (planfall and nullfall) to get correct max id
        df_markets = self.table_to_dataframe('Maerkte')
        if len(df_markets) == 0:
            new_id = 1
        else:
            new_id = df_markets['id'].max() + 1
        columns = df_markets.columns
        new_market = pd.DataFrame(np.zeros((1, len(columns))), columns=columns)
        new_market['id'] = new_id
        new_market['name'] = name
        new_market['SHAPE'] = [coords]
        new_market['id_teilflaeche'] = -1
        default_typ = 1
        vkfl = self.betriebstyp_to_vkfl(default_typ, None)
        new_market['vkfl'] = vkfl if self.setting == NULLFALL else 0
        if self.setting == NULLFALL:
            # market exists in nullfall
            new_market['id_betriebstyp_nullfall'] = default_typ
        # market exists in planfall
        new_market['id_betriebstyp_planfall'] = default_typ
        new_market['vkfl_planfall'] = vkfl

        bt = self.df_types[self.df_types['id_betriebstyp']
                           == default_typ].name.values[0]
        new_market['betriebstyp_planfall'] = bt
        new_market['betriebstyp_nullfall'] = bt

        kette = self.df_chains[self.df_chains['id_kette']
                               == 0].name.values[0]
        new_market['id_kette'] = 0
        new_market['kette'] = kette

        self.insert_dataframe_in_table('Maerkte', new_market)
        ags = get_ags(self.folders.get_table('Maerkte'), 'id')
        new_ags = ags[new_id][0]
        new_market['AGS'] = new_ags
        self.update_table('Maerkte', column_values={'AGS': new_ags},
                          where='id={}'.format(new_id))

    def betriebstyp_to_vkfl(self, id_betriebstyp, id_kette):
        """
        return the sales area (vkfl) matching the type of use (betriebstyp)
        of a single market
        """
        # some discounters have (since there is no specific betriebstyp and
        # therefore no hint on possible vkfl for them)
        if id_betriebstyp == 7:
            default_vkfl = self.df_chains[
                self.df_chains['id_kette']==id_kette]
            if len(default_vkfl) != 0:
                vkfl = default_vkfl['default_vkfl'].values[0]
                return vkfl
        # all other vkfl are assigned via betriebstyp (+ unmatched discounters)
        idx = self.df_types['id_betriebstyp'] == id_betriebstyp
        vkfl = self.df_types[idx]['default_vkfl'].values[0]
        return vkfl

    def _open(self, params):
        # reset markets dataframe on opening of toolbox
        self.markets_df = self.get_markets()
        self.markets_df['do_delete'] = False
        self.markets_df.sort_values(by='id', inplace=True)
        if len(self.markets_df) == 0:
            return

        # check, if there is a specific location set (most likely via addin)
        x, y = self.config.active_coord
        closest_idx = None
        if x and y:
            closest_idx, c = closest_point((x, y),
                                           self.markets_df['SHAPE'].values)

        # update the names of the markets and list them
        pretty_names = []
        for idx, market in self.markets_df.iterrows():
            pretty = self.get_pretty_market_name(market)
            pretty_names.append(pretty)
        self.markets_df['pretty'] = pretty_names
        self.update_market_list(closest_idx)
        self.set_selected_market_inputs()

    def get_pretty_market_name(self, market):
        '''assemble a meaningful name for the market incl. name and additional
        informations'''
        # type before doesn't matter in planfall (it's zero and not in list)
        if self.setting in [NULLFALL, CHANGE]:
            type_before = self.df_types['name'][
                self.df_types['id_betriebstyp'] ==
                market['id_betriebstyp_nullfall']].values[0]
        a_idx = (self.df_types['id_betriebstyp'] ==
                 market['id_betriebstyp_planfall'])
        # closing is not listed in Nullfall
        if a_idx.sum() == 0:
            type_after = u'Schließung'
        else:
            type_after = self.df_types['name'][a_idx].values[0]

        type_name = type_before if self.setting in [NULLFALL, CHANGE] \
            else type_after

        chain_name = self.df_chains['name'][
            self.df_chains['id_kette'] == market['id_kette']].values[0]
        pretty = u'"{name}" ({id}) - {typ} ({chain})'.format(
            id=market['id'], name=market['name'], typ=type_name,
            chain=chain_name)
        if self.setting in [NULLFALL, CHANGE] and type_before != type_after:
            pretty += u' -> geplant: {}'.format(type_after)
        if market['do_delete']:
            pretty += u' - WIRD ENTFERNT'
        return pretty

    def set_selected_market_inputs(self):
        '''set all input fields to match data of currently selected market'''
        market_idx = self.markets_df['pretty'] == self.par.markets.value
        market = self.markets_df.loc[market_idx]
        betriebstyp_col = 'id_betriebstyp_nullfall' \
            if self.setting == NULLFALL else 'id_betriebstyp_planfall'
        pretty_idx = (self.df_types['id_betriebstyp'] ==
                      market[betriebstyp_col].values[0])
        typ_pretty = self.df_types['pretty'][pretty_idx]
        self.par.type_name.value = typ_pretty.values[0]

        if self.setting != CHANGE:
            self.par.delete_all.value = False
            self.par.name.value = market['name'].values[0]
            chain_name = self.df_chains['name'][
                self.df_chains['id_kette'] == market['id_kette'].values[0]]
            self.par.chain.value = chain_name.values[0]
            do_delete = market['do_delete'].values[0]
            # strange: can't assign the bool of do_delete directly, arcpy is
            # ignoring it
            self.par.do_delete.value = True if do_delete else False
        else:
            do_close = market['id_betriebstyp_planfall'].values[0] == 0
            self.par.do_close.value = True if do_close else False

    def validate_inputs(self):
        df_markets = self.get_markets()
        if len(df_markets) == 0:
            if self.setting in [NULLFALL, CHANGE]:
                msg = (u'Es sind keine Märkte im Bestand vorhanden. '
                       u'Bitte lesen Sie zunächst Märkte ein oder fügen Sie '
                       u'sie dem Bestand manuell hinzu.')
            else:
                msg = (u'Es sind keine geplanten Märkte vorhanden. '
                       u'Bitte fügen Sie sie manuell hinzu.')
            return False, msg
        return True, ''

    def update_market_list(self, idx=None):
        '''update the input list of markets with pretty names in dataframe'''
        if idx is None:
            idx = self.par.markets.filter.list.index(
                self.par.markets.value) if self.par.markets.value else 0
        pretty = self.markets_df['pretty'].values.tolist()
        self.par.markets.filter.list = pretty
        self.par.markets.value = pretty[idx] if idx >= 0 else pretty[0]

    def _updateParameters(self, params):
        if len(self.markets_df) == 0:
            return
        market_idx = self.markets_df['pretty'] == self.par.markets.value

        if self.par.changed('name'):
            self.markets_df.loc[market_idx, 'name'] = self.par.name.value

        elif self.par.changed('chain'):
            chain = self.par.chain.value
            id_chain = self.df_chains['id_kette'][
                self.df_chains['name'] == chain].values[0]
            self.markets_df.loc[market_idx, 'id_kette'] = id_chain
            self.markets_df.loc[market_idx, 'kette'] = chain

        elif self.par.changed('type_name'):
            id_typ = self.df_types['id_betriebstyp'][
                self.df_types['pretty'] == self.par.type_name.value].values[0]
            typ = self.df_types[self.df_types['id_betriebstyp']
                                == id_typ].name.values[0]
            # ToDo: set different type/vkfl for planfall if nullfall is edited?
            self.markets_df.loc[market_idx, 'id_betriebstyp_planfall'] = id_typ
            self.markets_df.loc[market_idx, 'betriebstyp_planfall'] = typ
            id_kette = self.markets_df.loc[market_idx, 'id_kette'].values[0]
            vkfl = self.betriebstyp_to_vkfl(id_typ, id_kette)
            self.markets_df.loc[market_idx, 'vkfl_planfall'] = vkfl
            # only change nullfall type when toolbox is set to nullfall
            # in case of planfall it stays 0
            if self.setting == NULLFALL:
                self.markets_df.loc[market_idx, 'id_betriebstyp_nullfall'] = id_typ
                self.markets_df.loc[market_idx, 'betriebstyp_nullfall'] = typ
                self.markets_df.loc[market_idx, 'vkfl'] = vkfl

        elif self.par.changed('do_delete'):
            do_delete = self.par.do_delete.value
            self.markets_df.loc[market_idx, 'do_delete'] = do_delete

        elif self.par.changed('delete_all'):
            delete_all = self.par.delete_all.value
            self.par.do_delete.value = delete_all
            self.markets_df['do_delete'] = delete_all
            # update the pretty names of ALL markets in list
            # (setting the prefix that indicates the deletion)
            for index, market in self.markets_df.iterrows():
                pretty = self.get_pretty_market_name(market)
                self.markets_df.loc[index, 'pretty'] = pretty
            self.update_market_list()

        # update the pretty names of the selected market
        if (self.par.changed('name') or
            self.par.changed('chain') or
            self.par.changed('type_name') or
            self.par.changed('do_delete')):
            i = np.where(market_idx == True)[0][0]
            pretty = self.get_pretty_market_name(
                self.markets_df.iloc[i])
            self.markets_df.loc[market_idx, 'pretty'] = pretty
            self.update_market_list()

        # market changed -> change values of input fields
        if self.par.changed('markets'):
            self.set_selected_market_inputs()
        return params

    def _updateMessages(self, params):
        valid, msg = self.validate_inputs()
        if not valid:
            self.par.projectname.setErrorMessage(msg)


class TbxEditMarketsNullfall(TbxEditMarkets):
    setting = NULLFALL
    _label = encode(u'Märkte im Bestand bearbeiten')


class TbxEditMarketsPlanfall(TbxEditMarkets):
    setting = PLANFALL
    _label = encode(u'Geplante Märkte im Planfall bearbeiten')


class TbxExtendMarkets(TbxEditMarkets):
    setting = CHANGE
    _label = encode(u'Bestehende Märkte im Planfall verändern')

    def _updateParameters(self, params):
        if len(self.markets_df) == 0:
            return
        market_idx = self.markets_df['pretty'] == self.par.markets.value
        altered = False
        if self.par.changed('type_name'):
            id_typ = self.df_types['id_betriebstyp'][
                self.df_types['pretty'] == self.par.type_name.value].values[0]
            self.markets_df.loc[market_idx, 'id_betriebstyp_planfall'] = id_typ
            altered = True
        elif self.par.changed('do_close'):
            if self.par.do_close.value:
                self.markets_df.loc[market_idx, 'id_betriebstyp_planfall'] = 0
            else:
                self.markets_df.loc[market_idx, 'id_betriebstyp_planfall'] = \
                    self.markets_df.loc[market_idx, 'id_betriebstyp_nullfall']
            altered = True
        if altered:
            id_typ = self.markets_df.loc[market_idx, 'id_betriebstyp_planfall'].values[0]
            id_kette = self.markets_df.loc[market_idx, 'id_kette'].values[0]
            if id_typ == 0:
                vkfl = 0
            else:
                vkfl = self.betriebstyp_to_vkfl(id_typ, id_kette)
            self.markets_df.loc[market_idx, 'vkfl_planfall'] = vkfl
            i = np.where(market_idx == True)[0][0]
            pretty = self.get_pretty_market_name(
                self.markets_df.iloc[i])
            self.markets_df.loc[market_idx, 'pretty'] = pretty
            self.update_market_list()

        # market changed -> change values of input fields
        if self.par.changed('markets') or altered:
            self.set_selected_market_inputs()
        return params

if __name__ == '__main__':
    t = TbxExtendMarkets()
    t._getParameterInfo()
    t.set_active_project()
    #t.add_market_to_db('Test add', (3544252, 5925427))
    t.open()
    t._updateParameters(None)
    t.execute()
