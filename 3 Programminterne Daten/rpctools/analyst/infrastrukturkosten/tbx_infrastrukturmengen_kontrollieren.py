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

        fields = ['IDNetzelement', 'SHAPE_Length']
        tbl_kosten = self.folders.get_table("Erschliessungsnetze_Linienelemente_kontrolliert", 'FGDB_Kosten.gdb')
        cursor = arcpy.da.UpdateCursor(tbl_kosten, fields)
        for row in cursor:
            if row[0] == 11:
                row[1] = self.par[3].value 
            elif row[0] == 12:
                row[1] = self.par[5].value 
            elif row[0] == 21:
                row[1] = self.par[2].value
            elif row[0] == 22:
                row[1] = self.par[4].value
            elif row[0] == 31:
                row[1] = self.par[6].value
            elif row[0] == 32:
                row[1] = self.par[7].value 
            elif row[0] == 33:
                row[1] = self.par[8].value
            elif row[0] == 41:
                row[1] = self.par[9].value
            elif row[0] == 51:
                row[1] = self.par[10].value

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
        param.value = param.filter.list[0]

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



    def _updateParameters(self, params):
        params = self.par
        
        if params.projectname.altered and not params.projectname.hasBeenValidated:
            self.mengen_einlesen("manuell")
            self.par.Quelle.value = self.par.Quelle.filter.list[0]

        if params.Quelle.altered and not params.Quelle.hasBeenValidated:
            if self.par.Quelle.value == self.par.Quelle.filter.list[1]:
                self.mengen_einlesen("zeichnung")
            if self.par.Quelle.value == self.par.Quelle.filter.list[2]:
                self.mengen_einlesen("schaetzung")
                
    def mengen_einlesen(self, Quelle):
        
        if Quelle == "zeichnung":
            self.par[2].value = 0
            self.par[3].value = 0
            self.par[4].value = 0
            self.par[5].value = 0
            self.par[6].value = 0
            self.par[7].value = 0
            self.par[8].value = 0
            self.par[9].value = 0
            self.par[10].value = 0
            
            fields = ['IDNetzelement', 'SHAPE_Length']
            tbl_kosten = self.folders.get_table("Erschliessungsnetze_Linienelemente", 'FGDB_Kosten.gdb')
            cursor = arcpy.da.SearchCursor(tbl_kosten, fields)
            for row in cursor:
                if row[0] == 11:
                    self.par[3].value += row[1] 
                elif row[0] == 12:
                    self.par[5].value += row[1] 
                elif row[0] == 21:
                    self.par[2].value += row[1]  
                elif row[0] == 22:
                    self.par[4].value += row[1]  
                elif row[0] == 31:
                    self.par[6].value += row[1] 
                elif row[0] == 32:
                    self.par[7].value += row[1]   
                elif row[0] == 33:
                    self.par[8].value += row[1]  
                elif row[0] == 41:
                    self.par[9].value += row[1]  
                elif row[0] == 51:
                    self.par[10].value += row[1]
                    
        elif Quelle == "schaetzung":
            self.par[2].value = 0
            self.par[3].value = 0
            self.par[4].value = 0
            self.par[5].value = 0
            self.par[6].value = 0
            self.par[7].value = 0
            self.par[8].value = 0
            self.par[9].value = 0
            self.par[10].value = 0
            
            fields = ['IDNetzelement', 'SHAPE_Length']
            tbl_kosten = self.folders.get_table("Mengenkennwerte_Gebietstyp", 'FGDB_Kosten.gdb')
            cursor = arcpy.da.SearchCursor(tbl_kosten, fields)
            for row in cursor:
                if row[0] == 11:
                    self.par[3].value += row[1] 
                elif row[0] == 12:
                    self.par[5].value += row[1] 
                elif row[0] == 21:
                    self.par[2].value += row[1]  
                elif row[0] == 22:
                    self.par[4].value += row[1]  
                elif row[0] == 31:
                    self.par[6].value += row[1] 
                elif row[0] == 32:
                    self.par[7].value += row[1]   
                elif row[0] == 33:
                    self.par[8].value += row[1]  
                elif row[0] == 41:
                    self.par[9].value += row[1]  
                elif row[0] == 51:
                    self.par[10].value += row[1]
                    
        elif Quelle == "manuell":      
            fields = ['IDNetzelement', 'SHAPE_Length']
            tbl_kosten = self.folders.get_table("Erschliessungsnetze_Linienelemente_kontrolliert", 'FGDB_Kosten.gdb')
            cursor = arcpy.da.SearchCursor(tbl_kosten, fields)
            for row in cursor:
                if row[0] == 11:
                    self.par[3].value = row[1] 
                elif row[0] == 12:
                    self.par[5].value = row[1] 
                elif row[0] == 21:
                    self.par[2].value = row[1]  
                elif row[0] == 22:
                    self.par[4].value = row[1]  
                elif row[0] == 31:
                    self.par[6].value = row[1] 
                elif row[0] == 32:
                    self.par[7].value = row[1]   
                elif row[0] == 33:
                    self.par[8].value = row[1]  
                elif row[0] == 41:
                    self.par[9].value = row[1]  
                elif row[0] == 51:
                    self.par[10].value = row[1]  



if __name__ == '__main__':
    t = TbxKostenkennwerteKontrollieren()
    t._getParameterInfo()
    t.par.project.value = t.config.active_project
    t._open(t.par)
    t._updateParameters(t.par)
    t.execute()
