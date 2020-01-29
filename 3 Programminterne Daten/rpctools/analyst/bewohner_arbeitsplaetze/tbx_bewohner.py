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
        if area['WE_gesamt'] == 0:
            arcpy.AddError(u'Die Detailangaben zu Teilfläche "{}" fehlen!'
                           .format(area['Name']))
            return
        diagram = BewohnerEntwicklung(
            flaechen_id=area['id_teilflaeche'],
            flaechen_name=area['Name'])
        diagram.create()
        self.output.add_diagram(diagram)

    def run(self):
        return
        area, idx = self.parent_tbx.get_selected_area()

        fields = ['IDAltersklasse', 'Bewohner']
        tbl_bewohner = self.folders.get_table("Bewohner_nach_Altersgruppe_und_Jahr", 'FGDB_Bewohner_Arbeitsplaetze.gdb')
        cursor = arcpy.da.SearchCursor(tbl_bewohner, fields)
        n_unter18 = 0
        n_18_29 = 0
        n_30_44 = 0
        n_45_64 = 0
        n_65_80 = 0
        n_80plus = 0
        n_gesamt = 0
        for row in cursor:
            n_gesamt += row[1]
            if row[0] == 1:
                n_unter18 += row[1]
            elif row[0] == 2:
                n_18_29 += row[1]
            elif row[0] == 2:
                n_30_44 += row[1]
            elif row[0] == 2:
                n_45_64 += row[1]
            elif row[0] == 2:
                n_65_80 += row[1]
            elif row[0] == 2:
                n_80plus += row[1]
        anteil_u18 = (n_unter18 / n_gesamt) * 100
        anteil_18 = (n_18_29 / n_gesamt) * 100
        anteil_30 = (n_30_44 / n_gesamt) * 100
        anteil_45 = (n_45_64 / n_gesamt) * 100
        anteil_65 = (n_65_80 / n_gesamt) * 100
        anteil_80 = (n_80plus / n_gesamt) * 100
        anteil_nutzerdefiniert = self.par[2].value
        diff = anteil_nutzerdefiniert / anteil_u18
        n_unter18_neeu = n_unter18 * diff
        differenz_u18 = n_unter18 - n_unter18_neeu
        if differenz_u18 < 0:
            differenz_u18 = differenz_u18 * -1
        cursor = arcpy.da.UpdateCursor(tbl_bewohner, fields)
        for row in cursor:
            if row[0] == 1:
                row[1] = row[1] * diff
            elif row[0] == 2:
                row[1] = row[1] + anteil_18 * differenz_u18
            elif row[0] == 2:
                row[1] = row[1] + anteil_30 * differenz_u18
            elif row[0] == 2:
                row[1] = row[1] + anteil_45 * differenz_u18
            elif row[0] == 2:
                row[1] = row[1] + anteil_65 * differenz_u18
            elif row[0] == 2:
                row[1] = row[1] + anteil_80 * differenz_u18
            cursor.updateRow(row)


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

    #def _getParameterInfo(self):

        #super(TbxBewohner, self)._getParameterInfo()

        ## Beginn der Aufsiedlung (Jahreszahl)
        #param = self.add_parameter('anteilU18')
        #param.name = u'anteilU18'
        #param.displayName = u'Anteil an unter 18-Jährigen (in Prozent)'
        #param.parameterType = 'Required'
        #param.direction = 'Input'
        #param.datatype = u'Long'
        #param.filter.type = 'Range'
        #param.filter.list = [0, 40]
        #param.value = 31

        #return self.par


if __name__ == '__main__':
    t = TbxBewohner()
    params = t.getParameterInfo()
    t.set_active_project()
    t.open()
    t.execute()
    #t.update_teilflaechen(nutzungsart=1)
    t.show_outputs(show_layers=False)
