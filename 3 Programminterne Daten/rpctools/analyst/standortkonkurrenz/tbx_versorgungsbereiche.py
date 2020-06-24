# -*- coding: utf-8 -*-
import arcpy

from rpctools.utils.params import Tbx, Tool
from rpctools.utils.encoding import encode
from rpctools.utils.spatial_lib import closest_point, get_ags
import numpy as np
import pandas as pd

NULLFALL = 0
PLANFALL = 1


class EditCenters(Tool):
    _param_projectname = 'projectname'
    _workspace = 'FGDB_Standortkonkurrenz_Supermaerkte.gdb'

    def add_outputs(self):
        group_layer = ("standortkonkurrenz")
        folder = 'Standortkonkurrenz'
        fc = 'Zentren'
        layer = 'Zentren'
        self.output.add_layer(group_layer, layer, fc, zoom=False,
                              template_folder=folder,
                              subgroup='Betrachtungsraum')

    def run(self):
        centers_df = self.parent_tbx.centers_df
        delete_df = centers_df.loc[centers_df['do_delete'] == True]
        update_df = centers_df.loc[centers_df['do_delete'] == False]
        if len(delete_df) > 0:
            arcpy.AddMessage(u'Lösche Zentren')
        for idx, center in delete_df.iterrows():
            arcpy.AddMessage(u' - {}'.format(center['pretty']))
            self.parent_tbx.delete_rows_in_table(
                'Zentren',
                where='id={}'.format(center['id']))
        arcpy.AddMessage(u'Schreibe Änderungen in Datenbank...')
        self.parent_tbx.dataframe_to_table('Zentren', update_df,
                                           ['id'], upsert=False)
        arcpy.RefreshActiveView()


class TbxEditCenters(Tbx):

    @property
    def label(self):
        return 'Zentren bearbeiten oder entfernen'

    @property
    def Tool(self):
        return EditCenters

    def _getParameterInfo(self):

        # Projekt_auswählen
        param = self.add_parameter('projectname')
        param.name = encode(u'Projekt_auswählen')
        param.displayName = encode(u'Projekt')
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'GPString'
        param.filter.list = []

        param = self.add_parameter('centers')
        param.name = encode(u'Zentren')
        param.displayName = encode(u'Zentrum auswählen')
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'GPString'
        param.filter.list = []

        param = self.add_parameter('name')
        param.name = encode(u'Name')
        param.displayName = encode(u'Name des Zentrums')
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'GPString'

        param = self.add_parameter('do_delete')
        param.name = encode(u'Löschen')
        param.displayName = encode(u'Zentrum entfernen')
        param.parameterType = 'Optional'
        param.direction = 'Input'
        param.datatype = u'GPBoolean'

        self.centers_df = []
        return self.par

    def get_centers(self, user_only=True):
        '''return the centers in db as a dataframe, filtered by existance
        in nullfall and planfall (dependent on setting of this toolbox)'''
        where = 'nutzerdefiniert=1' if user_only else None
        df_centers = self.table_to_dataframe('Zentren', where=where)
        return df_centers

    def add_center_to_db(self, name, polygon):
        '''add a center to the database with given polygon as shape
        '''
        df_centers = self.get_centers(user_only=False)
        if len(df_centers) == 0:
            new_id = 1
        else:
            new_id = df_centers['id'].max() + 1
        column_values = {
            'id': new_id,
            'name': name,
            'nutzerdefiniert': 1,
            'SHAPE@': polygon,
            'umsatz_differenz': 0,
            'umsatz_planfall': 0,
            'umsatz_nullfall': 0
        }
        self.insert_rows_in_table('Zentren', column_values)

    def _open(self, params):
        self.centers_df = self.get_centers()
        if len(self.centers_df) == 0:
            return
        self.centers_df['do_delete'] = False
        self.centers_df.sort(columns='id', inplace=True)

        x, y = self.config.active_coord
        closest_idx = None
        if x and y:
            closest_idx, c = closest_point((x, y), self.centers_df['SHAPE'])

        pretty_names = []
        for idx, center in self.centers_df.iterrows():
            pretty = self.get_pretty_center_name(center)
            pretty_names.append(pretty)
        self.centers_df['pretty'] = pretty_names
        self.update_center_list(closest_idx)
        self.set_selected_center_inputs()
        pass

    def set_selected_center_inputs(self):
        center_idx = self.centers_df['pretty'] == self.par.centers.value
        center = self.centers_df.loc[center_idx]
        self.par.name.value = center['name'].values[0]
        do_delete = center['do_delete'].values[0]
        # strange: can't assign the bool of do_delete directly, arcpy is
        # ignoring it
        self.par.do_delete.value = True if do_delete else False

    def validate_inputs(self):
        if len(self.table_to_dataframe('Zentren', columns=['id'])) == 0:
            msg = (u'Es sind keine Zentren definiert. '
                   u'Bitte fügen Sie sie manuell hinzu.')
            return False, msg
        return True, ''

    def update_center_list(self, idx=None):
        if idx is None:
            idx = self.par.centers.filter.list.index(
                self.par.centers.value) if self.par.centers.value else 0
        pretty = self.centers_df['pretty'].values.tolist()
        self.par.centers.filter.list = pretty
        self.par.centers.value = pretty[idx] if idx >= 0 else pretty[0]

    def get_pretty_center_name(self, center):
        pretty = u'"{name}" ({id})'.format(
            id=center['id'],
            name=center['name'])
        if center['do_delete']:
            pretty += u' - WIRD ENTFERNT'
        return pretty

    def _updateParameters(self, params):
        if len(self.centers_df) == 0:
            return
        center_idx = self.centers_df['pretty'] == self.par.centers.value

        if self.par.changed('name'):
            self.centers_df.loc[center_idx, 'name'] = self.par.name.value

        elif self.par.changed('do_delete'):
            do_delete = self.par.do_delete.value
            self.centers_df.loc[center_idx, 'do_delete'] = do_delete

        # update the pretty names of the center

        if (self.par.changed('name') or
            self.par.changed('do_delete')):
            i = np.where(center_idx == True)[0][0]
            pretty = self.get_pretty_center_name(
                self.centers_df.iloc[i])
            self.centers_df.loc[center_idx, 'pretty'] = pretty
            self.update_center_list()

        if self.par.changed('centers'):
            self.set_selected_center_inputs()
        return params

    def _updateMessages(self, params):
        valid, msg = self.validate_inputs()
        if not valid:
            self.par.projectname.setErrorMessage(msg)

if __name__ == '__main__':
    t = TbxEditCenters()
    t._getParameterInfo()
    t.set_active_project()
    t._open(None)
    t._updateParameters(None)
    t.execute()
