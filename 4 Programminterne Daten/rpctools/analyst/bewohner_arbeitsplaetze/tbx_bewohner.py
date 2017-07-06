# -*- coding: utf-8 -*-

from rpctools.definitions.projektverwaltung.tbx_teilflaechen_verwalten import \
     TbxFlaechendefinition
from rpctools.utils.params import Tool
from rpctools.utils.constants import Nutzungsart
from rpctools.diagrams.bewohner_arbeitsplaetze import BewohnerEntwicklung
import pandas as pd
import arcpy


class Bewohner(Tool):
    _param_projectname = 'projectname'
    _workspace = 'FGDB_Bewohner_Arbeitsplaetze.gdb'
    
    def add_outputs(self):
        area, idx = self.parent_tbx.get_selected_area()
        #area = 
        diagram = BewohnerEntwicklung(
            flaechen_id=area['id_teilflaeche'],
            flaechen_name=area['Name'])
        diagram.create()
        self.output.add_diagram(diagram)

    def run(self):
        pass


class TbxBewohner(TbxFlaechendefinition):
    _nutzungsart = Nutzungsart.WOHNEN
    
    @property
    def Tool(self):
        return Bewohner

    @property
    def label(self):
        return u'Bewohnerzahl schätzen'
    
    def set_selected_area(self):
        pass
    
if __name__ == '__main__':
    t = TbxBewohner()
    params = t.getParameterInfo()
    t.set_active_project()
    t.open()
    t.execute()
    #t.update_teilflaechen(nutzungsart=1)
    t.show_outputs(show_layers=False)