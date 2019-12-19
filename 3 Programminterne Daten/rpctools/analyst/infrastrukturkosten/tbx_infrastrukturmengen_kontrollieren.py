# -*- coding: utf-8 -*-
import arcpy

from rpctools.utils.params import Tbx, Tool, Folders
from rpctools.utils.encoding import encode
from rpctools.analyst.infrastrukturkosten.kostenkennwerte_hilfsfunktionen import kostenkennwerte
import numpy as np
import pandas as pd


class InfrastrukturmengenKontrolle(Tool):
    _workspace = 'FGDB_Kosten.gdb'
    _param_projectname = 'projectname'
    _table = 'Kostenkennwerte_Linienelemente'

    def add_outputs(self):
        pass

    def run(self):

        fields = ['IDNetz', 'Laenge']
        tbl_kosten = self.folders.get_table("Erschliessungsnetze_Linienlaengen", 'FGDB_Kosten.gdb')
        cursor = arcpy.da.UpdateCursor(tbl_kosten, fields)
        for row in cursor:
            if row[0] == 1:
                row[1] = self.par[2].value + self.par[4].value
            if row[0] == 2:
                row[1] = self.par[1].value + self.par[3].value
            if row[0] == 3:
                row[1] = self.par[5].value + self.par[6].value + self.par[7].value
            if row[0] == 4:
                row[1] = self.par[8].value
            if row[0] == 5:
                row[1] = self.par[9].value

            cursor.updateRow(row)
        return


class TbxInfrastrukturmengenKontrollieren(Tbx):
    _table = 'Kostenkennwerte_Linienelemente'
    @property
    def label(self):
        return encode(u'Infrastrukturmengen kontrollieren')

    @property
    def Tool(self):
        return InfrastrukturmengenKontrolle

    def get_from_df(self, df, columns, df_id):
        df_selected = df.loc[df_id, (columns)]
        return df_selected


    def _updateParameters(self, params):
        pass

    def _getParameterInfo(self):
        params = self.par  
        p = self.add_parameter('projectname')
        p.name = u'Projekt'
        p.displayName = u'Projekt'
        p.parameterType = 'Required'
        p.direction = 'Input'
        p.datatype = u'GPString'
        projects = self.folders.get_projects()
        p.filter.list = projects
        p.value = '' if len(projects) == 0 else p.filter.list[0]

        param = self.add_parameter('Quelle')
        param.name = u'Quelle'
        param.displayName = u'Quelle der Infrastrukturmenge bestimmen'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'GPString'
        param.filter.list = [u"Infrastrukturmengen manuell eingeben", u"Infrastrukturmengen aus Zeichnungen importieren", u"Infrastrukturmengen schätzen lassen"]
        param.value = self.values[0]

        p = self.add_parameter('anlieger_aussen')
        p.name = u'anlieger_aussen'
        p.displayName = u'Länge von Anliegerstraßen (äußere Erschließung)'.encode('cp1252')
        p.parameterType = 'Required'
        p.direction = 'Input'
        p.datatype = u'GPLong'
        p.filter.type = 'Range'
        p.filter.list = [0, 1000]
        p.value = 0

        p = self.add_parameter('anlieger_innen')
        p.name = u'anlieger_innen'
        p.displayName = u'Länge von Anliegerstraßen (innere Erschließung)'.encode('cp1252')
        p.parameterType = 'Required'
        p.direction = 'Input'
        p.datatype = u'GPLong'
        p.filter.type = 'Range'
        p.filter.list = [0, 1000]
        p.value = 0

        p = self.add_parameter('sammler_aussen')
        p.name = u'sammler_aussen'
        p.displayName = u'Länge von Sammelstraßen (äußere Erschließung)'.encode('cp1252')
        p.parameterType = 'Required'
        p.direction = 'Input'
        p.datatype = u'GPLong'
        p.filter.type = 'Range'
        p.filter.list = [0, 1000]
        p.value = 0

        p = self.add_parameter('sammler_innen')
        p.name = u'sammler_innen'
        p.displayName = u'Länge von Sammelstraßen (innere Erschließung)'.encode('cp1252')
        p.parameterType = 'Required'
        p.direction = 'Input'
        p.datatype = u'GPLong'
        p.filter.type = 'Range'
        p.filter.list = [0, 1000]
        p.value = 0

        p = self.add_parameter('kanal_trenn')
        p.name = u'kanal_trenn'
        p.displayName = u'Länge von Kanälen (Trennsystem)'.encode('cp1252')
        p.parameterType = 'Required'
        p.direction = 'Input'
        p.datatype = u'GPLong'
        p.filter.type = 'Range'
        p.filter.list = [0, 1000]
        p.value = 0

        p = self.add_parameter('kanal_misch')
        p.name = u'kanal_misch'
        p.displayName = u'Länge von Kanälen (Mischsystem)'.encode('cp1252')
        p.parameterType = 'Required'
        p.direction = 'Input'
        p.datatype = u'GPLong'
        p.filter.type = 'Range'
        p.filter.list = [0, 1000]
        p.value = 0

        p = self.add_parameter('kanal_schmutz')
        p.name = u'kanal_schmutz'
        p.displayName = u'Länge von Kanälen (Nur Schmutzwasser)'.encode('cp1252')
        p.parameterType = 'Required'
        p.direction = 'Input'
        p.datatype = u'GPLong'
        p.filter.type = 'Range'
        p.filter.list = [0, 1000]
        p.value = 0

        p = self.add_parameter('wasser')
        p.name = u'wasser'
        p.displayName = u'Länge von Trinkwasserkanälen'.encode('cp1252')
        p.parameterType = 'Required'
        p.direction = 'Input'
        p.datatype = u'GPLong'
        p.filter.type = 'Range'
        p.filter.list = [0, 1000]
        p.value = 0

        p = self.add_parameter('strom')
        p.name = u'strom'
        p.displayName = u'Länge von Stromleitungen'.encode('cp1252')
        p.parameterType = 'Required'
        p.direction = 'Input'
        p.datatype = u'GPLong'
        p.filter.type = 'Range'
        p.filter.list = [0, 1000]
        p.value = 0

        return params


if __name__ == '__main__':
    t = TbxKostenkennwerteKontrollieren()
    t._getParameterInfo()
    t.par.project.value = t.config.active_project
    t._open(t.par)
    t._updateParameters(t.par)
    t.execute()
