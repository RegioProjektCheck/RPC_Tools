# -*- coding: utf-8 -*-

from rpctools.analyst.infrastrukturkosten.tbx_massnahmen_editieren import \
     TbxMassnahmenEditieren
from rpctools.analyst.infrastrukturkosten.tbx_gesamtkosten import \
     TbxGesamtkosten
from rpctools.analyst.infrastrukturkosten.tbx_infrastrukturmengenbilanz import \
     TbxInfrastrukturmengenBilanz
from rpctools.analyst.infrastrukturkosten.tbx_kostenkennwerte_kontrollieren \
     import TbxKostenkennwerteKontrollieren
from rpctools.analyst.infrastrukturkosten.tbx_kostentraeger_auswerten \
     import TbxKostentraegerAuswerten
from rpctools.analyst.infrastrukturkosten.tbx_kosten_vergleichen \
     import TbxKostenVergleichen
from rpctools.analyst.infrastrukturkosten.tbx_netzkostenaufteilung \
     import TbxNetzKostenaufteilungInnere
from rpctools.analyst.infrastrukturkosten.tbx_infrastrukturmengen_kontrollieren \
	 import TbxInfrastrukturmengenKontrollieren

class Toolbox(object):
    def __init__(self):
        self.label = u'Infrastrukturkosten'
        self.alias = ''
        self.tools = [TbxKostenkennwerteKontrollieren,
                      TbxMassnahmenEditieren,
					  TbxInfrastrukturmengenKontrollieren,
                      TbxInfrastrukturmengenBilanz,
                      TbxGesamtkosten,
                      TbxKostenVergleichen,
                      TbxNetzKostenaufteilungInnere,
                      TbxKostentraegerAuswerten]