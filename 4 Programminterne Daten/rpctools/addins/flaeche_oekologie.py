# -*- coding: utf-8 -*-
from rpctools.addins.common import ToolboxButton, folders, config
from rpctools.addins.outputs import BodenbedeckungAnzeigen
from rpctools.addins.outputs import GrenzlinieAnzeigen
import arcpy

__all__ = [
    "Waldgebiete", "Naturschutzgebiete",
    "Landschaftsschutzgebiete", "Wasserschutzgebiete",
    "Freiraeume", "Bodenversiegelung", "Hochspannung",
    "Bodenveraenderung", "Wohnflaechendichte",
    "IntegrationsgradAnzeigen", "GrenzlinieEinzeichnen", "GrenzlinieLoeschen",
    "UZVR",
    "NullfallUeberbauteFlaechen", "NullfallNatuerlicheWasserflaeche",
    "NullfallPlatten", "NullfallBaeumeStraeucher",
    "NullfallStauden", "NullfallWiese", "NullfallRasen",
    "NullfallRasengittersteine", "NullfallBeton", "NullfallAcker",
    "NullfallKleinpflaster",
    "PlanfallUeberbauteFlaechen", "PlanfallNatuerlicheWasserflaeche",
    "PlanfallPlatten", "PlanfallBaeumeStraeucher",
    "PlanfallStauden", "PlanfallWiese", "PlanfallRasen",
    "PlanfallRasengittersteine", "PlanfallBeton", "PlanfallAcker",
    "PlanfallKleinpflaster", "BodenKontrollieren", "BodenEntfernen",
    "BodenAnzeigen"
]


class Waldgebiete(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _do_show = False
    _toolbox_name = 'TbxLayerWald'
    #_message = (
        #u'Nach dem Schließen dieser Meldung wird in Ihrem Webbrowser eine '
        #u'Online-Karte des BfN zu den Schutzgebieten in Deutschland aufgerufen'
        #u'und auf den Bereich des Plangebiets gezoomt. In dieser Online-Karte '
        #u'finden Sie Detailangaben zu den Schutzgebieten im Umfeld des '
        #u'Plangebiets.')

    #def onClick(self, coord=None):
        #self.output.show()
        #self.show_message()


class Naturschutzgebiete(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _do_show = False
    _toolbox_name = 'TbxLayerNatur'


class Landschaftsschutzgebiete(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _do_show = False
    _toolbox_name = 'TbxLayerLandschaft'


class Wasserschutzgebiete(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _do_show = False
    _toolbox_name = 'TbxLayerWasser'

class Freiraeume(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _do_show = False
    _toolbox_name = 'TbxLayerFreiraum'

class Bodenversiegelung(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _do_show = False
    _toolbox_name = 'TbxLayerBodenversiegelung'

class Hochspannung(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _do_show = False
    _toolbox_name = 'TbxLayerHochspannung'


class BodenAnzeigen(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _do_show = False
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _toolbox_name = 'TbxBodenAnzeigen'


class BodenEntfernen(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _do_show = False
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _toolbox_name = 'TbxBodenKontrolle'


class BodenKontrollieren(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _toolbox_name = 'TbxBodenKontrolle'


class Bodenveraenderung(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _toolbox_name = 'TbxBodenBewertung'


class Wohnflaechendichte(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _toolbox_name = 'TbxWohnflaeche'


class IntegrationsgradAnzeigen(ToolboxButton):
    """Implementation for rpc_tools.integrationsgrad_anzeigen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _toolbox_name = 'TbxIntegrationsgrad'


class GrenzlinieEinzeichnen(ToolboxButton):
    """Implementation for rpc_tools.grenzlinie_einzeichnen (Tool)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = 'Flaeche und Oekologie.pyt'
    _toolbox_name = 'TbxIntegrationsgrad'

    def __init__(self):
        super(GrenzlinieEinzeichnen, self).__init__()
        self.enabled = True
        self.cursor = 3
        self.shape = 'Line'
        self.output = GrenzlinieAnzeigen()

    def onClick(self, coord=None):
        self.output.show()

    def onLine(self, line_geometry):
        tbx = self.tbx
        tbx.set_active_project()

##        array = arcpy.Array()
##        points = line_geometry.getPart(0)
##        for point in points:
##            array.add(point)
##        first = line_geometry.firstPoint
##        array.add(first)
        #polyline = arcpy.Polyline(array)
        tbx.grenzlinie_eintragen(line_geometry)
        arcpy.RefreshActiveView()

    def onMouseDownMap(self, x, y, button, shift):
        pass


class GrenzlinieLoeschen(ToolboxButton):
    """Implementation for rpc_tools.grenzlinie_loeschen (Tool)"""
    _path = folders.ANALYST_PYT_PATH
    _do_show = False
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _toolbox_name = 'TbxIntegrationsgrad_loeschen'


class UZVR(ToolboxButton):
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _toolbox_name = 'TbxUZVR'


class Draw_Bodenbedeckung(ToolboxButton):
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = 'Flaeche und Oekologie.pyt'
    _toolbox_name = 'TbxBodenKontrolle'

    def __init__(self):
        super(Draw_Bodenbedeckung, self).__init__()
        self.enabled = True
        self.cursor = 3
        self.bodenbedeckung = 0
        self.planfall = False
        self.shape = 'Line'
        self.output = BodenbedeckungAnzeigen()

    def onClick(self, coord=None):
        self.output.show()

    def onLine(self, line_geometry):
        tbx = self.tbx
        tbx.anzeige_an = True
        tbx.set_active_project()
        array = arcpy.Array()
        points = line_geometry.getPart(0)
        for point in points:
            array.add(point)
        first = line_geometry.firstPoint
        array.add(first)
        polygon = arcpy.Polygon(array)
        tbx.bodenbedeckung_eintragen(polygon, self.bodenbedeckung, self.planfall)
        arcpy.RefreshActiveView()

    def onMouseDownMap(self, x, y, button, shift):
        pass


class NullfallUeberbauteFlaechen(Draw_Bodenbedeckung):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""

    def __init__(self):
        super(NullfallUeberbauteFlaechen, self).__init__()
        self.bodenbedeckung = 1
        self.planfall = False


class NullfallNatuerlicheWasserflaeche(Draw_Bodenbedeckung):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""

    def __init__(self):
        super(NullfallNatuerlicheWasserflaeche, self).__init__()
        self.bodenbedeckung = 2
        self.planfall = False


class NullfallPlatten(Draw_Bodenbedeckung):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""

    def __init__(self):
        super(NullfallPlatten, self).__init__()
        self.bodenbedeckung = 3
        self.planfall = False


class NullfallBaeumeStraeucher(Draw_Bodenbedeckung):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""

    def __init__(self):
        super(NullfallBaeumeStraeucher, self).__init__()
        self.bodenbedeckung = 4
        self.planfall = False


class NullfallStauden(Draw_Bodenbedeckung):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""

    def __init__(self):
        super(NullfallStauden, self).__init__()
        self.bodenbedeckung = 5
        self.planfall = False


class NullfallWiese(Draw_Bodenbedeckung):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""

    def __init__(self):
        super(NullfallWiese, self).__init__()
        self.bodenbedeckung = 6
        self.planfall = False


class NullfallRasen(Draw_Bodenbedeckung):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""

    def __init__(self):
        super(NullfallRasen, self).__init__()
        self.bodenbedeckung = 7
        self.planfall = False


class NullfallRasengittersteine(Draw_Bodenbedeckung):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""

    def __init__(self):
        super(NullfallRasengittersteine, self).__init__()
        self.bodenbedeckung = 8
        self.planfall = False


class NullfallBeton(Draw_Bodenbedeckung):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""

    def __init__(self):
        super(NullfallBeton, self).__init__()
        self.bodenbedeckung = 9
        self.planfall = False


class NullfallAcker(Draw_Bodenbedeckung):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""

    def __init__(self):
        super(NullfallAcker, self).__init__()
        self.bodenbedeckung = 10
        self.planfall = False


class NullfallKleinpflaster(Draw_Bodenbedeckung):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""

    def __init__(self):
        super(NullfallKleinpflaster, self).__init__()
        self.bodenbedeckung = 11
        self.planfall = False


class PlanfallUeberbauteFlaechen(Draw_Bodenbedeckung):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""

    def __init__(self):
        super(PlanfallUeberbauteFlaechen, self).__init__()
        self.bodenbedeckung = 1
        self.planfall = True


class PlanfallNatuerlicheWasserflaeche(Draw_Bodenbedeckung):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""

    def __init__(self):
        super(PlanfallNatuerlicheWasserflaeche, self).__init__()
        self.bodenbedeckung = 2
        self.planfall = True


class PlanfallPlatten(Draw_Bodenbedeckung):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""

    def __init__(self):
        super(PlanfallPlatten, self).__init__()
        self.bodenbedeckung = 3
        self.planfall = True


class PlanfallBaeumeStraeucher(Draw_Bodenbedeckung):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""

    def __init__(self):
        super(PlanfallBaeumeStraeucher, self).__init__()
        self.bodenbedeckung = 4
        self.planfall = True


class PlanfallStauden(Draw_Bodenbedeckung):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""

    def __init__(self):
        super(PlanfallStauden, self).__init__()
        self.bodenbedeckung = 5
        self.planfall = True


class PlanfallWiese(Draw_Bodenbedeckung):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""

    def __init__(self):
        super(PlanfallWiese, self).__init__()
        self.bodenbedeckung = 6
        self.planfall = True


class PlanfallRasen(Draw_Bodenbedeckung):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""

    def __init__(self):
        super(PlanfallRasen, self).__init__()
        self.bodenbedeckung = 7
        self.planfall = True


class PlanfallRasengittersteine(Draw_Bodenbedeckung):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""

    def __init__(self):
        super(PlanfallRasengittersteine, self).__init__()
        self.bodenbedeckung = 8
        self.planfall = True


class PlanfallBeton(Draw_Bodenbedeckung):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""

    def __init__(self):
        super(PlanfallBeton, self).__init__()
        self.bodenbedeckung = 9
        self.planfall = True


class PlanfallAcker(Draw_Bodenbedeckung):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""

    def __init__(self):
        super(PlanfallAcker, self).__init__()
        self.bodenbedeckung = 10
        self.planfall = True


class PlanfallKleinpflaster(Draw_Bodenbedeckung):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""

    def __init__(self):
        super(PlanfallKleinpflaster, self).__init__()
        self.bodenbedeckung = 11
        self.planfall = True



if __name__ == '__main__':
    a = Wohnflaechendichte()
    a.onClick()