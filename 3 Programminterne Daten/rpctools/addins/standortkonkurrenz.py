# -*- coding: utf-8 -*-
import arcpy

from rpctools.utils.spatial_lib import from_project_srid
from rpctools.addins.common import ToolboxButton, folders, config
from rpctools.addins.outputs import MaerkteAnzeigen, ZentrenAnzeigen
from rpctools.utils.params import DummyTbx

__all__ = [
    "BestandOSMEinlesen", "TemplateErzeugen",
    "TemplateEinlesenDatei", "TemplateEinlesenFeatureClass",
    "MarktBearbeiten", "MarktHinzu", "BestandMarktBearbeiten",
    "PlanfallMarktBearbeiten", "BestandMarktHinzu",
    "PlanfallMarktHinzu", "PlanfallMarktErweiterung",
    "ZentrumBearbeiten", "ZentrumHinzu", "StandortkonkurrenzProjektwirkung",
    "MaerkteZentrenAnzeigen",  "FieldSelection", "BestandOSMBuffer"
]


class BestandOSMEinlesen(ToolboxButton):
    """Implementation for rpc_tools.bestand_osm (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = 'Standortkonkurrenz_Supermaerkte.pyt'
    _toolbox_name = 'TbxOSMMarktEinlesen'
    _do_show = True


class BestandOSMBuffer(ToolboxButton):
    """Implementation for rpc_tools.bestand_osm (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = 'Standortkonkurrenz_Supermaerkte.pyt'
    _toolbox_name = 'TbxOSMBuffer'
    _do_show = True


class TemplateErzeugen(ToolboxButton):
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = 'Standortkonkurrenz_Supermaerkte.pyt'
    _toolbox_name = 'TbxCreateTemplate'


class TemplateEinlesenDatei(ToolboxButton):
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = 'Standortkonkurrenz_Supermaerkte.pyt'
    _toolbox_name = 'TbxMaerkteImportierenDatei'


class TemplateEinlesenFeatureClass(ToolboxButton):
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = 'Standortkonkurrenz_Supermaerkte.pyt'
    _toolbox_name = 'TbxMaerkteImportierenFeatureClass'


class MaerkteZentrenAnzeigen(object):
    def __init__(self):
        self.outputs = [MaerkteAnzeigen(), ZentrenAnzeigen()]

    def onClick(self, coord=None):
        for o in self.outputs:
            o.show()


class MarktBearbeiten(ToolboxButton):
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = 'Standortkonkurrenz_Supermaerkte.pyt'
    _toolbox_name = None  # Nullfall/Planfall

    def __init__(self):
        super(MarktBearbeiten, self).__init__()
        self.enabled = True
        self.shape = 'NONE'
        self.cursor = 3
        self.output = MaerkteAnzeigen()

    def onClick(self, coord=None):
        self.output.show()
        self.show_message()

    def onMouseDownMap(self, x, y, button, shift):
        config.active_coord = from_project_srid(x, y, config.epsg)
        super(MarktBearbeiten, self).open()


class MarktHinzu(MarktBearbeiten):
    '''does the same thing as MarktBearbeiten except adding a market at
    click position before opening toolbox'''
    _new_market_name = ''
    _message = (u'Klicken Sie nach dem Schließen dieser Meldung an die Stelle '
                u'in der Karte, an der Sie einen bestehenden Lebensmittelmarkt'
                u'hinzufügen möchten. Warten Sie anschließend bis sich ein '
                u'Dialogfenster öffnet, in das Sie den Namen und den Typ des '
                u'Marktes eintragen können.')

    def onMouseDownMap(self, x, y, button, shift):
        tbx = self.tbx
        tbx.set_active_project()
        tbx.add_market_to_db(self._new_market_name, (x, y))
        arcpy.RefreshActiveView()
        super(MarktHinzu, self).onMouseDownMap(x, y, button, shift)


class BestandMarktBearbeiten(MarktBearbeiten):
    _toolbox_name = 'TbxEditMarketsNullfall'
    _message = (u'Klicken Sie nach dem Schließen dieser Meldung in die Nähe '
                u'des Marktes, den Sie bearbeiten oder löschen möchten.\n\n'
                u'Warten Sie anschließend bis sich ein Dialogfenster öffnet, '
                u'mit dem Sie den Markt bearbeiten oder löschen können.')


class PlanfallMarktBearbeiten(MarktBearbeiten):
    _toolbox_name = 'TbxEditMarketsPlanfall'
    _message = (u'Klicken Sie nach dem Schließen dieser Meldung in die Nähe '
                u'des neuen Marktes im Planfall, den Sie bearbeiten oder '
                u'löschen möchten.\n\n'
                u'Warten Sie anschließend bis sich ein Dialogfenster öffnet, '
                u'mit dem Sie den neuen Markt im Planfall bearbeiten oder '
                u'löschen können.')


class PlanfallMarktErweiterung(MarktBearbeiten):
    _toolbox_name = 'TbxExtendMarkets'
    _message = (u'Klicken Sie nach dem Schließen dieser Meldung in die Nähe '
                u'des Marktes, der im Zuge Ihrer Planung erweitert oder '
                u'geschlossen werden soll ("Planfall").\n\n'
                u'Warten Sie anschließend bis sich ein Dialogfenster öffnet, '
                u'mit dem Sie die Details dieser Erweiterung bzw. Schließung '
                u'festlegen.')


class BestandMarktHinzu(MarktHinzu):
    _toolbox_name = 'TbxEditMarketsNullfall'
    _new_market_name = 'unbenannter Markt im Bestand'
    _message = (u'Klicken Sie nach dem Schließen dieser Meldung an die Stelle '
                u'in der Karte, an der Sie einen bestehenden Lebensmittelmarkt '
                u'hinzufügen möchten.\n\n'
                u'Warten Sie anschließend bis sich ein Dialogfenster öffnet, '
                u'in das Sie den Namen und den Typ des Marktes eintragen '
                u'können.')


class PlanfallMarktHinzu(MarktHinzu):
    _toolbox_name = 'TbxEditMarketsPlanfall'
    _new_market_name = 'unbenannter geplanter Markt'
    _message = (u'Klicken Sie nach dem Schließen dieser Meldung an die Stelle '
                u'in der Karte, an der Sie im Planfall einen neuen '
                u'Lebensmittelmarkt hinzufügen möchten.\n\n'
                u'Warten Sie anschließend bis sich ein Dialogfenster öffnet, '
                u'in das Sie den Namen und den Typ des Marktes eintragen '
                u'können.')


class ZentrumBearbeiten(ToolboxButton):
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = 'Standortkonkurrenz_Supermaerkte.pyt'
    _toolbox_name = 'TbxEditCenters'
    _message = (u'Klicken Sie nach dem Schließen dieser Meldung auf das '
                u'Zentrum in der Karte, das Sie (um)benennen oder '
                u'löschen möchten. \n\n'
                u'Warten Sie anschließend bis sich ein entsprechendes '
                u'Dialogfenster öffnet.')

    def __init__(self):
        super(ZentrumBearbeiten, self).__init__()
        self.enabled = True
        self.shape = 'NONE'
        self.cursor = 3
        self.output = ZentrenAnzeigen()

    def onClick(self, coord=None):
        self.output.show()
        self.show_message()

    def onMouseDownMap(self, x, y, button, shift):
        config.active_coord = from_project_srid(x, y, config.epsg)
        super(ZentrumBearbeiten, self).open()


class ZentrumHinzu(ZentrumBearbeiten):
    _new_center_name = 'unbenanntes Zentrum'
    _message = (u'Zeichnen Sie nach dem Schließen dieser Meldung in der Karte '
                u'Zentren ein.\n\n'
                u'Klicken Sie dazu mehrfach in die Karte, um Stützpunkte für '
                u'die Form eines Zentrums zu setzen. Schließen Sie '
                u'das Einzeichnen jedes Zentrums mit einem '
                u'Doppelklick ab.\n\n'
                u'Sie können unmittelbar danach ein weiteres '
                u'Zentrum einzeichnen. Wenn Sie mit dem Einzeichnen '
                u'der Zentren fertig sind, klicken Sie auf das '
                u'grüne Häkchen ganz rechts in der Projekt-Check-Toolbox.\n\n'
                u'Über die Funktion "Analysieren > Standortkonkurrenz '
                u'Supermärkte > Zentren > Zentren '
                u'bearbeiten / entfernen" können Sie bereits gezeichnete '
                u'Zentren (um)benennen oder löschen.')

    def __init__(self):
        super(ZentrumHinzu, self).__init__()
        self.shape = 'Line'

    def onLine(self, line_geometry):
        tbx = self.tbx
        tbx.set_active_project()
        array = arcpy.Array()
        points = line_geometry.getPart(0)
        for point in points:
            array.add(point)
        first = line_geometry.firstPoint
        array.add(first)
        polygon = arcpy.Polygon(array)
        tbx.add_center_to_db(self._new_center_name, polygon)
        arcpy.RefreshActiveView()
        #config.active_coord = (first.X, first.Y)
        #super(ZentrumBearbeiten, self).onClick()

    def onMouseDownMap(self, x, y, button, shift):
        pass


class StandortkonkurrenzProjektwirkung(ToolboxButton):
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = 'Standortkonkurrenz_Supermaerkte.pyt'
    _toolbox_name = 'TbxProjektwirkungMarkets'


class FieldSelection(ToolboxButton):
    _workspace = 'FGDB_Standortkonkurrenz_Supermaerkte.gdb'
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = 'Standortkonkurrenz_Supermaerkte.pyt'
    _toolbox_name = 'TbxFieldSelection'
    _table = 'Zentren'

    def __init__(self):
        super(FieldSelection, self).__init__()
        self.enabled = True
        netz_table = folders.get_base_table('FGDB_Kosten_Tool.gdb',
                                            'Netze_und_Netzelemente')
        self.cursor = 3

    def onClick(self):
        self.tbx.set_active_project()
        self.tbx.show_outputs()


    def onMouseDownMap(self, x, y, button, shift):
        coords = arcpy.Point(x, y)
        tbx = self.tbx
        cursor = tbx.query_table(self._table, workspace=self._workspace,
                                 columns=['SHAPE@', 'id', "Auswahl"])
        found = False
        for row in cursor:
            shape, object_id, selection = row
            if shape.contains(coords):
                found = True
                break
        if not found:
            return
        if selection == 0:
            new_selection = 1
        elif selection == 1:
            new_selection = 0
        else:
            new_selection = selection
        del(cursor)
        tbx.update_table(self._table,
                         column_values={'Auswahl': new_selection},
                         where="id={}".format(object_id),
                         workspace=self._workspace)
        arcpy.RefreshActiveView()
