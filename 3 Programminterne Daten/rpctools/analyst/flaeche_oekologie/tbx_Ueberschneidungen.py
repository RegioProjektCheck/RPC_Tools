# -*- coding: utf-8 -*-

import arcpy

from rpctools.utils.params import Tbx
from rpctools.utils.encoding import encode
from rpctools.analyst.flaeche_oekologie.script_Ueberschneidungen import Ueberschneidungen
from rpctools.utils.constants import Nutzungsart
from rpctools.utils.params import Tool

class TbxUeberschneidungen(Tbx):
    """Toolbox Ueberschneidungen"""

    @property
    def label(self):
        return u'Ueberschneidungen anzeigen'

    @property
    def Tool(self):
        return Ueberschneidungen

    def _getParameterInfo(self):

        par = self.par

        # Projekt_auswählen
        par.name = arcpy.Parameter()
        par.name.name = u'Projektname'
        par.name.displayName = u'Projekt'
        par.name.parameterType = 'Required'
        par.name.direction = 'Input'
        par.name.datatype = u'GPString'
        par.name.filter.list = []


        return par


class TbxLayerWald(TbxUeberschneidungen):

    def _getParameterInfo(self):
        super(TbxLayerWald, self)._getParameterInfo()
        par = self.par
        self.layer_number = 1
        return par


class TbxLayerNatur(TbxUeberschneidungen):

    def _getParameterInfo(self):
        super(TbxLayerNatur, self)._getParameterInfo()
        par = self.par
        self.layer_number = 2
        return par


class TbxLayerLandschaft(TbxUeberschneidungen):

    def _getParameterInfo(self):
        super(TbxLayerLandschaft, self)._getParameterInfo()
        par = self.par
        self.layer_number = 3
        return par


class TbxLayerFreiraum_100(TbxUeberschneidungen):

    def _getParameterInfo(self):
        super(TbxLayerFreiraum_100, self)._getParameterInfo()
        par = self.par
        self.layer_number = 4
        return par


class TbxLayerFreiraum_50(TbxUeberschneidungen):

    def _getParameterInfo(self):
        super(TbxLayerFreiraum_50, self)._getParameterInfo()
        par = self.par
        self.layer_number = 5
        return par


class TbxLayerFreiraum(TbxUeberschneidungen):

    def _getParameterInfo(self):
        super(TbxLayerFreiraum, self)._getParameterInfo()
        par = self.par
        self.layer_number = 6
        return par


class TbxLayerWald_50(TbxUeberschneidungen):

    def _getParameterInfo(self):
        super(TbxLayerWald_50, self)._getParameterInfo()
        par = self.par
        self.layer_number = 7
        return par


class TbxLayerHochspannung(TbxUeberschneidungen):

    def _getParameterInfo(self):
        super(TbxLayerHochspannung, self)._getParameterInfo()
        par = self.par
        self.layer_number = 8
        return par


class TbxSchutzgebiete(TbxUeberschneidungen):

    def _getParameterInfo(self):
        super(TbxSchutzgebiete, self)._getParameterInfo()
        par = self.par
        self.layer_number = 9
        return par
