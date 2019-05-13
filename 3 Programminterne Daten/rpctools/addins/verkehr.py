# -*- coding: utf-8 -*-
from rpctools.addins.common import ToolboxButton, folders, config
from rpctools.utils.spatial_lib import from_project_srid
from rpctools.addins.outputs import AnbindungspunkteAnzeigen

__all__ = ['InitialRouting', 'RoutingSettings',
           'WeightedRouting', 'Anbindungspunkt']


class InitialRouting(ToolboxButton):
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = 'Verkehrserzeugung.pyt'
    _toolbox_name = 'TbxRouting'


class RoutingSettings(ToolboxButton):
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = 'Verkehrserzeugung.pyt'
    _toolbox_name = 'TbxSettings'


class WeightedRouting(ToolboxButton):
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = 'Verkehrserzeugung.pyt'
    _toolbox_name = 'TbxUpdateNodes'


class Anbindungspunkt(ToolboxButton):
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = 'Verkehrserzeugung.pyt'
    _toolbox_name = 'TbxSetSource'
    _message = (
        u'Klicken Sie nach dem Schließen dieser Meldung in die Karte um einen '
        u'Anbindungspunkt für eine der Teilflächen Ihres Plangebiets zu setzen.'
        u'\n\nWarten Sie anschließend bis sich ein Dialogfenster öffnet, mit '
        u'dem Sie festlegen können, welche Ihrer Teilflächen mit diesem '
        u'Anbindungspunkt an das bestehende Straßennetz angeschlossen werden '
        u'soll.')

    def __init__(self):
        super(Anbindungspunkt, self).__init__()
        self.enabled = True
        self.shape = 'NONE'
        self.cursor = 3
        self.output = AnbindungspunkteAnzeigen()

    def onClick(self, coord=None):
        self.output.show()
        self.show_message()

    def onMouseDownMap(self, x, y, button, shift):
        config.active_coord = from_project_srid(x, y, config.epsg)
        super(Anbindungspunkt, self).open()
