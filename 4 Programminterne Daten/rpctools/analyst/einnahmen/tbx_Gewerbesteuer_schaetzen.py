# -*- coding: utf-8 -*-

import arcpy

from rpctools.utils.params import Tbx
from rpctools.utils.encoding import encode
from rpctools.analyst.einnahmen.script_Gewerbesteuer_schaetzen import Gewerbesteuer

class TbxGewerbesteuer(Tbx):
    """Toolbox Wanderungssalden f�r Einnahmen"""

    @property
    def label(self):
        return u'Schritt 2: Steuersalden schätzen'

    @property
    def Tool(self):
        return Gewerbesteuer

    def _getParameterInfo(self):

        par = self.par

        # Projektname
        par.name = arcpy.Parameter()
        par.name.name = u'Projektname'
        par.name.displayName = u'Projektname'
        par.name.parameterType = 'Required'
        par.name.direction = 'Input'
        par.name.datatype = u'GPString'
        par.name.filter.list = []

        return par

    def _updateParameters(self, params):

        par = self.par

        cursor = self.query_table(table_name = 'Chronik_Nutzung',
                                columns = ['Arbeitsschritt', 'Letzte_Nutzung'],
                                workspace='FGDB_Einnahmen.gdb')
        for row in cursor:
            if row[0] == u"Wanderung Besch�ftigte" and row[1] is None:
                par.name.setErrorMessage(u'Es wurden noch keine Wanderungssalden für Besch�ftigte berechnet!')

        where = 'Nutzungsart = {} or Nutzungsart = {}'.format(Nutzungsart.WOHNEN, Nutzungsart.EINZELHANDEL)
        if par.changed('name'):
            where = 'Nutzungsart = {} or Nutzungsart = {}'.format(Nutzungsart.WOHNEN, Nutzungsart.EINZELHANDEL)
            rows = self.query_table('Teilflaechen_Plangebiet',
                                    ['Nutzungsart'],
                                    workspace='FGDB_Definition_Projekt.gdb',
                                    where=where)
            if not rows:
                par.name.setErrorMessage(u'In diesem Projekt sind keine Gewerbe- oder Einzelhandelsfl�chen definiert!')
                par.gemeinde.enabled = False
                par.gemeinde.filter.list = []
                par.gemeinde.value = (u'Projekt enth�lt keine Fl�chen mit der '
                                      u'ben�tigten Nutzungsart')