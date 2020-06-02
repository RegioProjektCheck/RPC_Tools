# -*- coding: utf-8 -*-
# reload

from rpctools.analyst.erreichbarkeit.tbx_ErreichbarkeitOEPNV import TbxErreichbarkeitOEPNV
from rpctools.analyst.erreichbarkeit.tbx_HaltestellenZentraleOrte import TbxHaltestellenZentraleOrte
from rpctools.analyst.erreichbarkeit.tbx_fahrplaene import TbxFahrplaene
from rpctools.analyst.erreichbarkeit.tbx_isochrone import TbxIsochrone
from rpctools.analyst.erreichbarkeit.tbx_Einrichtungen import TbxEinrichtungen
from rpctools.analyst.erreichbarkeit.tbx_KarteOEPNV import TbxKarteOEPNV

class Toolbox(object):
    def __init__(self):
        self.label = u'Erreichbarkeit'
        self.alias = ''
        self.tools = [TbxHaltestellenZentraleOrte,
                      TbxFahrplaene,
                      TbxErreichbarkeitOEPNV,
                      TbxIsochrone,
                      TbxEinrichtungen,
					  TbxKarteOEPNV]


