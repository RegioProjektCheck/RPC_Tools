# -*- coding: utf-8 -*-
import os
import arcpy
import pandas as pd
import numpy as np

from rpctools.utils.params import Tbx, Tool
from rpctools.utils.encoding import encode
from rpctools.diagrams.infrastruktur import GesamtkostenDiagramm
from rpctools.analyst.infrastrukturkosten.kostenkennwerte_hilfsfunktionen import kostenkennwerte


class Gesamtkosten(Tool):
    _param_projectname = 'projectname'
    _workspace = 'FGDB_Kosten.gdb'
    _costs_results_table = 'Gesamtkosten'

    years = 25

    def add_outputs(self):
        kosten_diagram = GesamtkostenDiagramm()

        self.output.add_diagram(kosten_diagram)

    def run(self):
        arcpy.AddMessage('Bereite Ausgangsdaten auf...')
        kostenkennwerte(self.par.projectname.value)
        self.df_costs = self.parent_tbx.table_to_dataframe(
            'Kostenkennwerte_Linienelemente')
        del self.df_costs['IDNetz']
        self.df_lines = self.parent_tbx.table_to_dataframe(
            'Erschliessungsnetze_Linienelemente_kontrolliert')
        self.joined_lines_costs = self.df_lines.merge(
            self.df_costs, on='IDNetzelement', how='left')
        self.df_points = self.parent_tbx.table_to_dataframe(
            'Erschliessungsnetze_Punktelemente')
        self.df_elements = self.parent_tbx.table_to_dataframe(
            'Netze_und_Netzelemente', workspace='FGDB_Kosten_Tool.gdb',
            columns=['Netz', 'IDNetz'],
            is_base_table=True)
        self.df_elements.drop_duplicates(inplace=True)

        self.df_phases = self.parent_tbx.table_to_dataframe(
            'Kostenphasen', workspace='FGDB_Kosten_Tool.gdb',
            is_base_table=True)

        arcpy.AddMessage(u'Berechne Gesamtkosten der Phasen {}\n{}...'
                         .format(
                             u' für die ersten {} Jahre'.format(self.years),
                             u', \n'.join(self.df_phases['Kostenphase'].tolist())
                         ))
        self.parent_tbx.delete_rows_in_table(self._costs_results_table)
        self.calculate_phases()

    def calculate_phases(self):

        df_results = self.parent_tbx.table_to_dataframe(
            self._costs_results_table)
        #line_results = pd.DataFrame(columns=self.df_results.columns)
        #point_results = line_results.copy(deep=True)

        # points and lines have same columns and calc. basis is same as well
        grouped_lines = self.joined_lines_costs.groupby('IDNetz')
        grouped_points = self.df_points.groupby('IDNetz')
        for grouped in [grouped_lines, grouped_points]:
            for net_id, group in grouped:
                for index, phase in self.df_phases.iterrows():
                    phase_id = phase['IDKostenphase']
                    if phase_id == 1:
                        costs = group['Euro_EH']
                    elif phase_id == 2:
                        costs = self.years * group['Cent_BU'] / 100.
                    elif phase_id == 3:
                        costs = (self.years *
                                 group['Euro_EN'] / group['Lebensdauer'])
                    else:
                        raise Exception('phase {} not defined'.format(phase_id))

                    # only difference between points and lines: costs of lines
                    # are based on costs per meter, points naturally don't have
                    # a length at all ^^
                    if 'SHAPE_Length' in group:
                        costs *= group['SHAPE_Length']
                    costs = costs.sum()

                    row = pd.DataFrame({'IDNetz': net_id,
                                        'IDKostenphase': phase_id,
                                        'Euro': round(costs, 2),
                                        }, index=[0])
                    df_results = df_results.append(row, ignore_index=True)

        df_results = df_results.groupby(['IDNetz', 'IDKostenphase']).agg(np.sum)
        df_results.reset_index(inplace=True)
        df_results = df_results.merge(self.df_phases, on='IDKostenphase')
        df_results = df_results.merge(self.df_elements, on='IDNetz')
        self.parent_tbx.insert_dataframe_in_table(self._costs_results_table,
                                                  df_results)


class TbxGesamtkosten(Tbx):
    _table = 'Gesamtkosten'

    @property
    def label(self):
        return encode(u'Gesamtkosten ermitteln')

    @property
    def Tool(self):
        return Gesamtkosten

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
        return params

    def validate_inputs(self):
        return True, ''

if __name__ == "__main__":
    t = TbxGesamtkosten()
    t.getParameterInfo()
    t.set_active_project()
    t.open()
    t.show_outputs()
    t.execute()
