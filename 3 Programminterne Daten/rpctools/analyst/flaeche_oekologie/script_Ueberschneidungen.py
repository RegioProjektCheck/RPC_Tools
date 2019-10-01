# -*- coding: utf-8 -*-
import os
import sys
import numpy as np
import arcpy
from rpctools.utils.params import Tool
import rpctools.utils.weighted_mean as wmean
import webbrowser

class Ueberschneidungen(Tool):
    """Ueberschneidungen"""

    _param_projectname = 'name'
    _workspace = 'FGDB_Flaeche_und_Oekologie.gdb'

    def add_outputs(self):
        params = self.par

        if self.parent_tbx.layer_number == 1:
            path = "Waldgebiete"
            legend = "Legende_Waldgebiete"
            title = u"Legende: Walgbeiete"
        elif self.parent_tbx.layer_number == 2:
            path = "Natur_und_Artenschutz"
            legend = "Legende_Natur_und_Artenschutz"
            title = u"Legende: Natur- und Artenschutz"
        elif self.parent_tbx.layer_number == 3:
            path = "Landschaftsschutz"
            legend = "Legende_Landschaftsschutz"
            title = u"Legende: Landschaftsschutz"
        elif self.parent_tbx.layer_number == 4:
            path = "Unzerschnittene_Freiraeume_100qkm"
            legend = "Legende_unzerschnittene_freiraeume_100qkm"
            title = u"Legende: Unzerschnittene Freiräume > 100 qkm"
        elif self.parent_tbx.layer_number == 5:
            path = "Unzerschnittene_Freiraeume_50qkm"
            legend = "Legende_unzerschnittene_freiraeume_50qkm"
            title = u"Legende: Unzerschnittene Freiräume > 50 qkm"
        elif self.parent_tbx.layer_number == 6:
            path = "Freiraumflaeche"
            legend = "Legende_Freiraumflaeche"
            title = u"Legende: Freiraumfläche"
        elif self.parent_tbx.layer_number == 7:
            path = "Unzerschnittene_Waelder_50qkm"
            legend = "Legende_unzerschnittene_waelder_50qkm"
            title = u"Legende: Unzerschnittene Wälder > 50 qkm"
        elif self.parent_tbx.layer_number == 8:
            path = "Hochspannungsleitungen"
            legend = "Legende_Hochspannungsleitungen"
            title = u"Legende: Hochspannungsleitungen"

        self.output.add_layer(
            groupname = "oekologie", template_layer = path,
            template_folder="oekologie", zoom=False,
            disable_other = True, show_wms_legends=False
        )
        arcpy.RefreshTOC()
        arcpy.RefreshActiveView()

    def run(self):
        pass










