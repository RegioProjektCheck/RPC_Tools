# -*- coding: utf-8 -*-
from rpctools.addins.common import ToolboxButton, folders, config
from rpctools.addins.outputs import BodenbedeckungAnzeigen_Nullfall
from rpctools.addins.outputs import BodenbedeckungAnzeigen_Planfall
from rpctools.addins.outputs import GrenzlinieAnzeigen
from rpctools.addins.common import FileButton
from rpctools.analyst.flaeche_oekologie.script_Schutzgebiete import Schutzgebiete
import pythonaddins
import arcpy

__all__ = [
    "Erlaeuterung", "Waldgebiete", "Naturschutz",
    "Landschaftsschutz", "Schutzgebiete",
    "Freiraeume_100qkm", "Freiraeume_50qkm", "Freiraeume",
    "Waelder_50qkm", "Hochspannungsleitungen",

    "Kennwerte_berechnen", "Wohnflaechendichte", "Wohndichte",

    "Integrationsgrad_berechnen", "Grenze_zeichnen", "Grenze_loeschen",

    "NullfallUeberbauteFlaechen", "NullfallNatuerlicheWasserflaeche",
    "NullfallPlatten", "NullfallBaeumeStraeucher",
    "NullfallStauden", "NullfallWiese", "NullfallRasen",
    "NullfallRasengittersteine", "NullfallBeton", "NullfallAcker",
    "NullfallKleinpflaster",
    "PlanfallUeberbauteFlaechen", "PlanfallNatuerlicheWasserflaeche",
    "PlanfallPlatten", "PlanfallBaeumeStraeucher",
    "PlanfallStauden", "PlanfallWiese", "PlanfallRasen",
    "PlanfallRasengittersteine", "PlanfallBeton", "PlanfallAcker",
    "PlanfallKleinpflaster", "BodenKontrollieren", "BodenEntfernen_Nullfall",
    "BodenAnzeigen_Nullfall", "Zeichnung_Nullfall", "BodenEntfernen_Planfall",
    "BodenAnzeigen_Planfall", "Zeichnung_Planfall"
]


class Erlaeuterung(FileButton):
    _file = 'ProjektCheck_Erlaeuterung_Kennwerte_Leistungsfaehigkeit_Boden.pdf'


class Naturschutz(ToolboxButton):
    """Implementation for rpc_tools.naturschutzgebiete (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _do_show = False
    _toolbox_name = 'TbxLayerNatur'


class Landschaftsschutz(ToolboxButton):
    """Implementation for rpc_tools.landschaftsschutzgebiete (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _do_show = False
    _toolbox_name = 'TbxLayerLandschaft'


class Schutzgebiete(ToolboxButton):
    """Implementation for rpc_tools.detail_schutzgebiete (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _do_show = False
    _toolbox_name = 'TbxSchutzgebiete'
    _message = u"Nach dem Schließen dieser Meldung wird in Ihrem Webbrowser eine Online-Karte des BfN zu den Schutzgebieten in Deutschland aufgerufen und auf den Bereich des Plangebiets gezoomt. \n\n In dieser Online-Karte finden Sie Detailangaben zu den Schutzgebieten im Umfeld des Plangebiets."

    def show_message(self):
        if self._message:
            pythonaddins.MessageBox(self._message, 'Hinweis', 0)

class Freiraeume_100qkm(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _do_show = False
    _toolbox_name = 'TbxLayerFreiraum_100'


class Freiraeume_50qkm(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _do_show = False
    _toolbox_name = 'TbxLayerFreiraum_50'


class Freiraeume(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _do_show = False
    _toolbox_name = 'TbxLayerFreiraum'


class Waldgebiete(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _do_show = False
    _toolbox_name = 'TbxLayerWald'


class Waelder_50qkm(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _do_show = False
    _toolbox_name = 'TbxLayerWald_50'


class Hochspannungsleitungen(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _do_show = False
    _toolbox_name = 'TbxLayerHochspannung'


class Wohndichte(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _do_show = True
    _toolbox_name = 'TbxWohndichte'


class Wohnflaechendichte(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _do_show = True
    _toolbox_name = 'TbxWohnflaechendichte'


class Integrationsgrad_berechnen(ToolboxButton):
    """Implementation for rpc_tools.integrationsgrad_anzeigen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _do_show = False
    _toolbox_name = 'TbxIntegrationsgrad_berechnen'


class Grenze_zeichnen(ToolboxButton):
    """Implementation for rpc_tools.grenzlinie_einzeichnen (Tool)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = 'Flaeche und Oekologie.pyt'
    _toolbox_name = 'TbxIntegrationsgrad_zeichnen'
    _message = u"Zeichnen Sie nach dem Schließen dieser Meldung mit dem dann verfügbaren Zeichenwerkzeug die Außenkante Ihres Plangebiets in den Abschnitten nach, in denen Ihr Plangebiet an eine bestehende Siedlungsfläche angrenzt. \n\n Schließen Sie jede (Teil-)Linie durch einen Doppelklick ab. \n\n Klicken Sie am Ende bitte auf das grüne Häkchen am rechten Rand der Projekt-Check-Toolbox, um das Zeichentool zu verlassen."

    def __init__(self):
        super(Grenze_zeichnen, self).__init__()
        self.enabled = True
        self.cursor = 3
        self.shape = 'Line'
        self.output = GrenzlinieAnzeigen()

    def onClick(self, coord=None):
        self.output.show()
        self.show_message()

    def show_message(self):
        if self._message:
            pythonaddins.MessageBox(self._message, 'Hinweis', 0)

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


class Grenze_loeschen(ToolboxButton):
    """Implementation for rpc_tools.grenzlinie_loeschen (Tool)"""
    _path = folders.ANALYST_PYT_PATH
    _do_show = False
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _toolbox_name = 'TbxIntegrationsgrad_loeschen'


class BodenAnzeigen_Nullfall(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _do_show = False
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _toolbox_name = 'TbxBodenAnzeigen_Nullfall'

class BodenAnzeigen_Planfall(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _do_show = False
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _toolbox_name = 'TbxBodenAnzeigen_Planfall'


class BodenEntfernen_Nullfall(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _do_show = False
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _toolbox_name = 'TbxBodenEntfernen_Nullfall'


class BodenEntfernen_Planfall(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _do_show = False
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _toolbox_name = 'TbxBodenEntfernen_Planfall'


class Zeichnung_Nullfall(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _do_show = True
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _toolbox_name = 'TbxZeichnung_Nullfall'


class Zeichnung_Planfall(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _do_show = True
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _toolbox_name = 'TbxZeichnung_Planfall'


class BodenKontrollieren(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _toolbox_name = 'TbxBodenKontrolle'


class Kennwerte_berechnen(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Flaeche und Oekologie.pyt'
    _toolbox_name = 'TbxBodenBewertung'


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

    def onClick(self, coord=None):
        if self.planfall == False:
            self.output = BodenbedeckungAnzeigen_Nullfall()
        else:
            self.output = BodenbedeckungAnzeigen_Planfall()
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
