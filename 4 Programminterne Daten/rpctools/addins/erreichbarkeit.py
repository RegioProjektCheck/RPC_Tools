# -*- coding: utf-8 -*-
from rpctools.addins.common import ToolboxButton, folders

__all__ = [
    "HaltestellenZentraleOrte", "Haltestellenplan",
    "FahrtzeitZentraleOrte", "Isochrone", 
    "EinrichtungenEinlesen"
]


class HaltestellenZentraleOrte(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Erreichbarkeit.pyt'
    _toolbox_name = 'TbxZentraleOrteOEPNV'


class Haltestellenplan(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Erreichbarkeit.pyt'
    _toolbox_name = 'TbxFahrplaene'


class FahrtzeitZentraleOrte(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Erreichbarkeit.pyt'
    _toolbox_name = '?'


class Isochrone(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Erreichbarkeit.pyt'
    _toolbox_name = 'TbxIsochrone'


class EinrichtungenEinlesen(ToolboxButton):
    """Implementation for rpc_tools.bewohner_schaetzen (Button)"""
    _path = folders.ANALYST_PYT_PATH
    _pyt_file = u'Erreichbarkeit.pyt'
    _toolbox_name = 'TbxEinrichtungen'
