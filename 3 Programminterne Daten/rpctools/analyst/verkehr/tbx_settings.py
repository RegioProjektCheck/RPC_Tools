# -*- coding: utf-8 -*-
from rpctools.utils.params import Tbx, Tool
from rpctools.utils.encoding import encode
from rpctools.utils.constants import Nutzungsart as nart
from rpctools.analyst.verkehr.otp_router import OTPRouter
from rpctools.analyst.verkehr.routing import Routing
import arcpy
import pandas as pd
import os


class Settings(Routing):
    _workspace = 'FGDB_Verkehr.gdb'
    _param_projectname = 'project'

    def add_outputs(self):
        if self.initial_routing_done:
            super(Settings, self).add_outputs()

    def run(self):
        toolbox = self.parent_tbx
        # tbx settings
        wege_w = toolbox.par.wohnen_wege.value
        pkw_w = toolbox.par.wohnen_pkw.value
        wege_g = toolbox.par.gewerbe_wege.value
        pkw_g = toolbox.par.gewerbe_pkw.value
        wege_e = toolbox.par.einzelhandel_wege.value
        pkw_e = toolbox.par.einzelhandel_pkw.value
        # write settings into the table
        toolbox.update_table('Wege_je_Nutzung',
                          {'Wege_gesamt': wege_w, 'PKW_Anteil': pkw_w},
                          where='Nutzungsart={}'.format(nart.WOHNEN))
        toolbox.update_table('Wege_je_Nutzung',
                          {'Wege_gesamt': wege_g, 'PKW_Anteil': pkw_g},
                          where='Nutzungsart={}'.format(nart.GEWERBE))
        toolbox.update_table('Wege_je_Nutzung',
                          {'Wege_gesamt': wege_e, 'PKW_Anteil': pkw_e},
                          where='Nutzungsart={}'.format(
                              nart.EINZELHANDEL))

        if self.initial_routing_done:
            self.calculate_traffic_load()

    @property
    def initial_routing_done(self):
        table = self.parent_tbx.query_table('RouteLinks')
        return len(table) > 0


class TbxSettings(Tbx):

    @property
    def label(self):
        return encode(u'Verkehrsaufkommen und Verkehrsmittelwahl')

    @property
    def Tool(self):
        return Settings

    def round_param(self, value):
        if value >= 10000:
            return round(value, -3)
        elif value >= 1000:
            return round(value, ndigits=-2)
        return round(value, -1)

    def _open(self, params):
        # get values from fgdb
        wege_w, pkw_w= self.query_table('Wege_je_Nutzung',
                                    columns=['Wege_gesamt',
                                             'PKW_Anteil'],
                                    where='Nutzungsart={}'.format(
                                        nart.WOHNEN))[0]
        wege_g, pkw_g= self.query_table('Wege_je_Nutzung',
                                        columns=['Wege_gesamt',
                                                'PKW_Anteil'],
                                        where='Nutzungsart = {}'.format(
                                            nart.GEWERBE))[0]
        wege_e, pkw_e= self.query_table('Wege_je_Nutzung',
                                        columns=['Wege_gesamt',
                                                 'PKW_Anteil'],
                                        where='Nutzungsart = {}'.format(
                                            nart.EINZELHANDEL))[0]
        wege_w = self.round_param(wege_w)
        wege_g = self.round_param(wege_g)
        wege_e = self.round_param(wege_e)
        # set params and check if wege_x is set. if not: disable
        params.wohnen_wege.value = wege_w
        params.wohnen_pkw.value = pkw_w
        if wege_w == 0:
            params.wohnen_wege.enabled = False
            params.wohnen_pkw.enabled = False
        params.gewerbe_wege.value = wege_g
        params.gewerbe_pkw.value = pkw_g
        if wege_g == 0:
            params.gewerbe_wege.enabled = False
            params.gewerbe_pkw.enabled = False
        params.einzelhandel_wege.value = wege_e
        params.einzelhandel_pkw.value = pkw_e
        if wege_e == 0:
            params.einzelhandel_wege.enabled = False
            params.einzelhandel_pkw.enabled = False

    def _getParameterInfo(self):
        params = self.par

        # Projekt
        param = params.project = arcpy.Parameter()
        param.name = u'Projekt'
        param.displayName = u'Projekt'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'GPString'

        category = '1) Verkehrsaufkommen Wohnen'

        # Wohnen
        param = params.wohnen_wege = arcpy.Parameter()
        param.name = u'wohnen_wege'
        param.displayName = u'Gesamtzahl der Wege pro Werktag ' + \
            u'(Hin- und Rückwege)'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.category = category

        param = params.wohnen_pkw = arcpy.Parameter()
        param.name = u'wohnen_pkw'
        param.displayName = u'Anteil der Wege als Pkw-Fahrer/in an dieser ' + \
            u'Gesamtzahl (in Prozent)'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = category
        category = '2) Verkehrsaufkommen Gewerbe'

        # Gewerbe
        param = params.gewerbe_wege = arcpy.Parameter()
        param.name = u'gewerbe_wege'
        param.displayName = u'Gesamtzahl der Wege pro Werktag ' + \
            u'(Hin- und Rückwege)'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.category = category

        param = params.gewerbe_pkw = arcpy.Parameter()
        param.name = u'gewerbe_pkw'
        param.displayName = u'Anteil der Wege als Pkw-Fahrer/in an dieser ' + \
            u'Gesamtzahl (in Prozent)'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = category

        category = '3) Verkehrsaufkommen Einzelhandel'

        # Einzelhandel
        param = params.einzelhandel_wege = arcpy.Parameter()
        param.name = u'einzelhandel_wege'
        param.displayName = u'Gesamtzahl der Wege pro Werktag ' + \
            u'(Hin- und Rückwege)'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.category = category

        param = params.einzelhandel_pkw = arcpy.Parameter()
        param.name = u'einzelhandel_pkw'
        param.displayName = u'Anteil der Wege als Pkw-Fahrer/in an dieser ' + \
            u'Gesamtzahl (in Prozent)'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = category

        return params

    def _updateParameters(self, params):
        return

