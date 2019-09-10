# -*- coding: utf-8 -*-
import os
import sys
import numpy as np
import arcpy
from rpctools.utils.params import Tool
import rpctools.utils.weighted_mean as wmean
import webbrowser

class Schutzgebiete(Tool):
    """Ueberschneidungen"""

    _param_projectname = 'name'
    _workspace = 'FGDB_Flaeche_und_Oekologie.gdb'

    def add_outputs(self):
        params = self.par










