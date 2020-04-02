# -*- coding: utf-8 -*-
import os
import arcpy

from rpctools.utils.params import Tbx, Tool
from rpctools.utils.encoding import encode
from rpctools.analyst.infrastrukturkosten.kostenkennwerte_hilfsfunktionen \
     import kostenaufteilung_startwerte
from rpctools.analyst.infrastrukturkosten.tbx_gesamtkosten import Gesamtkosten
from rpctools.diagrams.infrastruktur import KostentraegerDiagramm


class KostentraegerAuswerten(Gesamtkosten):
    _shares_results_table = 'Gesamtkosten_nach_Traeger'

    def add_outputs(self):
        kosten_diagram = KostentraegerDiagramm(years=self.years)

        self.output.add_diagram(kosten_diagram)

    def run(self):
        super(KostentraegerAuswerten, self).run()
        kostenaufteilung_startwerte(self.par.get_projectname())
        self.df_shares = self.parent_tbx.table_to_dataframe('Kostenaufteilung')
        arcpy.AddMessage(u'Berechne Aufteilung der Kosten nach Kostenträgern...')
        self.calculate_shares()

    def calculate_shares(self):
        df_costs = self.parent_tbx.table_to_dataframe(
            self._costs_results_table)
        joined = df_costs.merge(self.df_shares,
                                on=['IDNetz', 'IDKostenphase'], how='right')
        joined.fillna(0, inplace=True)
        joined['Betrag_GSB'] = (joined['Euro'] *
                                joined['Anteil_GSB'] / 100.).round(2)
        joined['Betrag_GEM'] = (joined['Euro'] *
                                joined['Anteil_GEM'] / 100.).round(2)
        joined['Betrag_ALL'] = (joined['Euro'] *
                                joined['Anteil_ALL'] / 100.).round(2)
        summed = joined.groupby('IDNetz').sum()
        summed.reset_index(inplace=True)
        self.parent_tbx.dataframe_to_table(self._shares_results_table, summed,
                                           ['IDNetz'])


class TbxKostentraegerAuswerten(Tbx):

    @property
    def label(self):
        return encode(u'Kosten nach Kostenträgern auswerten')

    @property
    def Tool(self):
        return KostentraegerAuswerten

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
    t = TbxKostentraegerAuswerten()
    t.getParameterInfo()
    t.set_active_project()
    t.open()
    #t.show_outputs()
    t.execute()
