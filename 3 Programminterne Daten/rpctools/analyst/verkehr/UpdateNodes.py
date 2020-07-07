# -*- coding: utf-8 -*-
#

import arcpy
import numpy as np
from rpctools.utils.config import Folders
from rpctools.utils.params import Tool
from rpctools.analyst.verkehr.otp_router import OTPRouter
from rpctools.analyst.verkehr.routing import Routing


class UpdateNodes(Routing):
    pickle_file_exists = True
    def add_outputs(self):
        if not self.pickle_file_exists:
            return
        self.output.add_layer('verkehr', 'links',
                              featureclass='links',
                              template_folder='Verkehr',
                              name='Zusätzliche PKW-Fahrten gewichtet',
                              symbology_classes=(15, 'weight'))
        self.output.add_layer('verkehr', 'Zielpunkte_gewichtet',
                              featureclass='Zielpunkte',
                              template_folder='Verkehr',
                              name='Zielpunkte gewichtet',
                              symbology_classes=(10, 'Neue_Gewichte'),
                              zoom=True, zoom_extent=self._extent)
        return

    def run(self):
        pickle_path = self.folders.get_otp_pickle_filename(check=False)
        if not arcpy.Exists(pickle_path):
            arcpy.AddError("Verkehrsbelastung mit Gewichten versehen konnte "
                           "nicht ausgeführt werden.")
            arcpy.AddError("Entweder ist das Verkehrsaufkommen nicht "
                           "initialisiert worden, oder die Einstellungen der "
                           "Anbindungspunkte bzw. Kennwerte wurden verändert. "
                           "\n Bitte starten Sie 'Verkehrsaufkommen "
                           "initialisieren' neu.")
            self.pickle_file_exists = False
            return
        otp_router = OTPRouter.from_dump(pickle_path)

        toolbox = self.parent_tbx
        # get input data
        input_data = toolbox.query_table('Zielpunkte',
                                          ['node_id', 'Manuelle_Gewichtung'])
        node_ids = [tup[0] for tup in input_data]
        weights = np.array([tup[1] for tup in input_data]).astype(float)
        weights /= weights.sum()

        for i, weight in enumerate(weights):
            id_node = node_ids[i]
            otp_router.transfer_nodes[id_node].weight = weight
            where = 'node_id = {}'.format(id_node)
            toolbox.update_table('Zielpunkte',
                                 {'Neue_Gewichte': weight}, where=where)

        self.remove_output()
        otp_router.transfer_nodes.assign_weights_to_routes()
        otp_router.calc_vertex_weights()
        otp_router.create_polyline_features()
        otp_router.nodes_have_been_weighted = True
        self._extent = otp_router.extent
        otp_router.dump(pickle_path)

    def remove_output(self):
        mxd = arcpy.mapping.MapDocument("CURRENT")
        df = arcpy.mapping.ListDataFrames(mxd, "*")[0]
        layers1 = arcpy.mapping.ListLayers(mxd, "*Zielpunkte*", df)
        layers2 = arcpy.mapping.ListLayers(mxd, "*Fahrten*", df)
        layers = sum([layers1, layers2], [])
        for layer in layers:
            arcpy.mapping.RemoveLayer(df, layer)
        del(mxd)
