# -*- coding: utf-8 -*-
import os
import sys
import arcpy

from rpctools.utils.params import Tbx
from rpctools.utils.encoding import encode
from rpctools.utils.encoding import language
from rpctools.analyst.verkehr.T1_Basisdaten_bearbeiten import Basisdatenbearbeiten

class TbxBasisdatenbearbeiten(Tbx):

    @property
    def label(self):
        return encode(u'Basisdaten bearbeiten')

    @property
    def Tool(self):
        return Basisdatenbearbeiten

    def _getParameterInfo(self):

		list_projects = project_lib.get_projects()
        list_projects = sorted(list_projects)

        #set parameters
        self.params[0].filter.list = list_projects

		# Projektname
        param_1 = arcpy.Parameter()
        param_1.name = u'Projektname'
        param_1.displayName = u'Projektname'
        param_1.parameterType = 'Required'
        param_1.direction = 'Input'
        param_1.datatype = language('string')
        param_1.filter.list = []

        parameters = [param_1]
        validator = getattr(self, 'ToolValidator', None)
        validator(parameters).initializeParameters()

        return parameters


    def _updateParameters(self, params):
		return


