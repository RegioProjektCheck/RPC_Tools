# -*- coding: utf-8 -*-
import arcpy
import requests

from rpctools.utils.params import Tool, Tbx
from rpctools.utils.spatial_lib import get_project_centroid, Point
from rpctools.utils.encoding import encode
from rpctools.analyst.erreichbarkeit.routing_query import RoutingQuery
from rpctools.definitions.projektverwaltung.tbx_teilflaechen_verwalten \
     import TbxFlaechendefinition


class Isochrone(Tool):
    _param_projectname = 'projectname'
    _workspace = 'FGDB_Erreichbarkeit.gdb'
    cutoff = None
    area = None

    modes = {
        'CAR': ('Auto', 5),
        'BICYCLE': ('Fahrrad', 5),
        'WALK': (u'zu Fuß', 1.33)
    }

    def add_outputs(self):
        group_layer = ("erreichbarkeit")
        layers = ['Isochrone zu Fuß',
                  'Isochrone Fahrrad',
                  'Isochrone Auto']
        fc = u'Isochrone'
        for layer in layers:
            name = layer
            if self.cutoff:
                name += ' ({} Minuten)'.format(self.cutoff)
            self.output.add_layer(group_layer, layer, fc,
                                  name=name,
                                  template_folder='Erreichbarkeit',
                                  zoom=False)

    def run(self):
        table = 'Isochrone'
        self.cutoff = self.par.cutoff.value
        cutoff_sec = self.cutoff * 60
        self.area, i = self.parent_tbx.get_selected_area()
        area_id = self.area['id_teilflaeche']
        rows = self.parent_tbx.query_table(
            'Anbindungspunkte', workspace='FGDB_Verkehr.gdb',
            where='id_teilflaeche={}'.format(area_id), columns='SHAPE')

        x, y = rows[0][0]
        centroid = Point(x, y, epsg=self.parent_tbx.config.epsg)
        query = RoutingQuery()
        target_epsg = self.parent_tbx.config.epsg
        column_values = {'modus': [], 'SHAPE@': [],
                         'cutoff': [self.cutoff] * len(self.modes)}
        try:
            for mode, (name, walk_speed) in self.modes.iteritems():
                arcpy.AddMessage(u'Ermittle die Isochronen für den Modus "{}"'
                                 .format(name))
                iso_poly = query.get_isochrone(centroid, target_epsg,
                                               mode, cutoff_sec, walk_speed)
                column_values['modus'].append(name)
                column_values['SHAPE@'].append(iso_poly)
            arcpy.AddMessage('Schreibe die Isochronen in die Datenbank...')
            self.parent_tbx.delete_rows_in_table(table)
            self.parent_tbx.insert_rows_in_table(table, column_values)
        except requests.HTTPError:
            arcpy.AddError('Fehler bei der Anfrage an den Routingserver. '
                           'Entweder ist der Server nicht erreichbar oder der '
                           'Anbindungspunkt kann nicht an das Straßennetz '
                           'angebunden werden.')



class TbxIsochrone(TbxFlaechendefinition):
    @property
    def label(self):
        return encode(u'Isochronen zur Umfelderreichbarkeit erzeugen')

    @property
    def Tool(self):
        return Isochrone

    def _getParameterInfo(self):

        params = self.par

        # Projekt_auswählen
        param = self.add_parameter('projectname')
        param.name = encode(u'Projekt_auswählen')
        param.displayName = encode(u'Projekt')
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'GPString'
        param.filter.list = []

        params = super(TbxIsochrone, self)._getParameterInfo()
        params.area.displayName = encode(
            u'Teilfläche, von deren Anbindungspunkt aus die Erreichbarkeit '
            'ermittelt wird')

        param = self.add_parameter('cutoff')
        param.name = encode(u'Erreichbarkeit')
        param.displayName = encode(u'Erreichbarkeit in x Minuten')
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'GPLong'
        param.filter.type = 'Range'
        param.filter.list = [5, 60]
        param.value = 10

        return params

    def set_selected_area(self):
        pass


if __name__ == '__main__':
    t = TbxIsochrone()
    params = t.getParameterInfo()
    t.set_active_project()
    t.open()
    t.execute()
