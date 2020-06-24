# -*- coding: utf-8 -*-
import os
import sys

import arcpy
from rpctools.utils.params import Tool
from rpctools.diagrams.diagram_oekologie import Dia_Waerme
from rpctools.diagrams.diagram_oekologie import Dia_Schadstoff
from rpctools.diagrams.diagram_oekologie import Dia_Durchlaessigkeit
from rpctools.diagrams.diagram_oekologie import Dia_Ueberformung
from rpctools.diagrams.diagram_oekologie import Dia_Abfluss
from rpctools.diagrams.diagram_oekologie import Dia_Grundwasser
from rpctools.diagrams.diagram_oekologie import Dia_Regenwasser
from rpctools.diagrams.diagram_oekologie import Dia_Biotop
from rpctools.diagrams.diagram_oekologie import Dia_Staub

class BodenbedeckungBewertung(Tool):
    """BodenbedeckungBewertung"""

    _param_projectname = 'name'
    _workspace = 'FGDB_Flaeche_und_Oekologie.gdb'

    def add_outputs(self):
        diagram = Dia_Waerme(projectname=self.par.name.value)
        self.output.add_diagram(diagram)
        diagram = Dia_Schadstoff(projectname=self.par.name.value)
        self.output.add_diagram(diagram)
        diagram = Dia_Durchlaessigkeit(projectname=self.par.name.value)
        self.output.add_diagram(diagram)
        diagram = Dia_Ueberformung(projectname=self.par.name.value)
        self.output.add_diagram(diagram)
        diagram = Dia_Abfluss(projectname=self.par.name.value)
        self.output.add_diagram(diagram)
        diagram = Dia_Grundwasser(projectname=self.par.name.value)
        self.output.add_diagram(diagram)
        diagram = Dia_Regenwasser(projectname=self.par.name.value)
        self.output.add_diagram(diagram)
        diagram = Dia_Biotop(projectname=self.par.name.value)
        self.output.add_diagram(diagram)
        diagram = Dia_Staub(projectname=self.par.name.value)
        self.output.add_diagram(diagram)

    def run(self):
        params = self.par
        projekt = self.projectname

        path_bodenbedeckung = self.folders.get_table('Bodenbedeckung_Anteile', "FGDB_Flaeche_und_Oekologie.gdb", projekt)
        path_bodenbedeckung = self.folders.get_table('Bodenbedeckung_Anteile', "FGDB_Flaeche_und_Oekologie.gdb", projekt)

        fields = ["IDBodenbedeckung", "Planfall", "Bodenbedeckung_Anteil"]
        cursor = arcpy.da.UpdateCursor(path_bodenbedeckung, fields)
        for row in cursor:
            if row[1] == 0 and row[0] == 1:
                 row[2] = params.ueberbauteflaechen_alt.value
            elif row[1] == 0 and row[0] == 2:
                 row[2] = params.wasser_alt.value
            elif row[1] == 0 and row[0] == 3:
                 row[2] = params.platten_alt.value
            elif row[1] == 0 and row[0] == 4:
                 row[2] = params.baeume_alt.value
            elif row[1] == 0 and row[0] == 5:
                 row[2] = params.rasengittersteine_alt.value
            elif row[1] == 0 and row[0] == 6:
                 row[2] = params.stauden_alt.value
            elif row[1] == 0 and row[0] == 7:
                 row[2] = params.wiese_alt.value
            elif row[1] == 0 and row[0] == 8:
                 row[2] = params.beton_alt.value
            elif row[1] == 0 and row[0] == 9:
                 row[2] =params.acker_alt.value
            elif row[1] == 0 and row[0] == 10:
                 row[2] = params.kleinpflaster_alt.value
            elif row[1] == 0 and row[0] == 11:
                 row[2] = params.rasen_alt.value
            elif row[1] == 1 and row[0] == 1:
                 row[2] = params.ueberbauteflaechen_neu.value
            elif row[1] == 1 and row[0] == 2:
                 row[2] = params.wasser_neu.value
            elif row[1] == 1 and row[0] == 3:
                 row[2] = params.platten_neu.value
            elif row[1] == 1 and row[0] == 4:
                 row[2] =params.baeume_neu.value
            elif row[1] == 1 and row[0] == 5:
                 row[2] = params.rasengittersteine_neu.value
            elif row[1] == 1 and row[0] == 6:
                 row[2] = params.stauden_neu.value
            elif row[1] == 1 and row[0] == 7:
                 row[2] = params.wiese_neu.value
            elif row[1] == 1 and row[0] == 8:
                 row[2] = params.beton_neu.value
            elif row[1] == 1 and row[0] == 9:
                 row[2] = params.acker_neu.value
            elif row[1] == 1 and row[0] == 10:
                 row[2] = params.kleinpflaster_neu.value
            elif row[1] == 1 and row[0] == 11:
                 row[2] = params.rasen_neu.value
            cursor.updateRow(row)



        boden_anteile_alt = [0,0,0,0,0,0,0,0,0,0,0]
        boden_anteile_neu = [0,0,0,0,0,0,0,0,0,0,0]

        fields = ["IDBodenbedeckung", "Planfall", "Bodenbedeckung_Anteil"]
        cursor = arcpy.da.SearchCursor(path_bodenbedeckung, fields)
        for row in cursor:
            if row[1] == 0 and row[0] == 1:
                 boden_anteile_alt[0] = row[2] / 1.0
            elif row[1] == 0 and row[0] == 2:
                 boden_anteile_alt[1] = row[2] / 1.0
            elif row[1] == 0 and row[0] == 3:
                 boden_anteile_alt[2] = row[2] / 1.0
            elif row[1] == 0 and row[0] == 4:
                 boden_anteile_alt[3] = row[2] / 1.0
            elif row[1] == 0 and row[0] == 5:
                 boden_anteile_alt[4] = row[2] / 1.0
            elif row[1] == 0 and row[0] == 6:
                 boden_anteile_alt[5] = row[2] / 1.0
            elif row[1] == 0 and row[0] == 7:
                 boden_anteile_alt[6] = row[2] / 1.0
            elif row[1] == 0 and row[0] == 8:
                 boden_anteile_alt[7] = row[2] / 1.0
            elif row[1] == 0 and row[0] == 9:
                 boden_anteile_alt[8] = row[2] / 1.0
            elif row[1] == 0 and row[0] == 10:
                 boden_anteile_alt[9] = row[2] / 1.0
            elif row[1] == 0 and row[0] == 11:
                 boden_anteile_alt[10] = row[2] / 1.0
            elif row[1] == 1 and row[0] == 1:
                 boden_anteile_neu[0] = row[2] / 1.0
            elif row[1] == 1 and row[0] == 2:
                 boden_anteile_neu[1] = row[2] / 1.0
            elif row[1] == 1 and row[0] == 3:
                 boden_anteile_neu[2] = row[2] / 1.0
            elif row[1] == 1 and row[0] == 4:
                 boden_anteile_neu[3] = row[2] / 1.0
            elif row[1] == 1 and row[0] == 5:
                 boden_anteile_neu[4] = row[2] / 1.0
            elif row[1] == 1 and row[0] == 6:
                 boden_anteile_neu[5] = row[2] / 1.0
            elif row[1] == 1 and row[0] == 7:
                 boden_anteile_neu[6] = row[2] / 1.0
            elif row[1] == 1 and row[0] == 8:
                 boden_anteile_neu[7] = row[2] / 1.0
            elif row[1] == 1 and row[0] == 9:
                 boden_anteile_neu[8] = row[2] / 1.0
            elif row[1] == 1 and row[0] == 10:
                 boden_anteile_neu[9] = row[2] / 1.0
            elif row[1] == 1 and row[0] == 11:
                 boden_anteile_neu[10] = row[2] / 1.0

        plangebiet_ha = 0
        path_teilflaechen = self.folders.get_table('Teilflaechen_Plangebiet', "FGDB_Definition_Projekt.gdb", projekt)
        fields = ["SHAPE_Area"]
        cursor = arcpy.da.SearchCursor(path_teilflaechen, fields)
        for row in cursor:
            plangebiet_ha += row[0]

        boden_ha_absolut_nullfall = [0,0,0,0,0,0,0,0,0,0,0]
        boden_ha_absolut_planfall = [0,0,0,0,0,0,0,0,0,0,0]

        for x in xrange(11):
            boden_ha_absolut_nullfall[x] = boden_anteile_alt[x] * plangebiet_ha
            boden_ha_absolut_planfall[x] = boden_anteile_neu[x] * plangebiet_ha

        #Klima
        waermespeicherung_multiplikator = [0,1,0.1,0.8,0.2,0.9,1,0,0.3,0.3,1]
        staubbindevermoegen_multiplikator = [0,1,0,0.8,0.1,0.4,0.4,0,0.1,0.1,0.2]
        #Boden
        schadstoffrueckhaltung_multiplikator = [0,0,0.2,0.8,0.4,0.8,0.8,0,0.5,0.3,0.8]
        durchlaessigkeit_multiplikator = [0,1,0.2,1,0.6,1,1,0.1,1,0.4,0.8]
        bodenueberformung_multiplikator = [0,1,0,0.8,0,0.8,1,0,0.8,0,0.8]
        #Wasser
        oberflaechenabfluss_multiplikator = [0,0,0.4,1,0.6,1,1,0.1,1,0.7,0.8]
        grundwasserneubildung_multiplikator = [0,1,0.3,0.4,0.8,0.5,0.5,0,1,0.5,0.5]
        regenwasserversickerung_multiplikator = [0,1,0.4,0.9,0.5,0.9,1,0.1,1,0.5,0.8]
        #Biotop
        biotopausbildungsvermoegen_multiplikator = [0.1,1,0.2,0.9,0.4,0.9,1,0.1,0.5,0.3,0.6]

        # 1 = Überbaute Fläche
        # 2 = natürliche Wasserflächen
        # 3 = Platten
        # 4 = Bäume / Sträucher
        # 5 = wassergeb. Decke / Rasengittersteine
        # 6 = Stauden
        # 7 = Wiese
        # 8 = Asphalt / Beton
        # 9 = offener Boden / Acker
        # 10 = Kleinpflaster
        # 11 = Rasen

        faktor_waermespeicherung_nullfall = []
        faktor_waermespeicherung_planfall = []

        faktor_staubbindevermoegen_nullfall = []
        faktor_staubbindevermoegen_planfall = []

        faktor_schadstoffrueckhaltung_nullfall = []
        faktor_schadstoffrueckhaltung_planfall = []

        faktor_durchlaessigkeit_nullfall = []
        faktor_durchlaessigkeit_planfall = []

        faktor_bodenueberformung_nullfall = []
        faktor_bodenueberformung_planfall = []

        faktor_oberflaechenabfluss_nullfall = []
        faktor_oberflaechenabfluss_planfall = []

        faktor_grundwasserneubildung_nullfall = []
        faktor_grundwasserneubildung_planfall = []

        faktor_regenwasserversickerung_nullfall = []
        faktor_regenwasserversickerung_planfall = []

        faktor_biotopausbildungsvermoegen_nullfall = []
        faktor_biotopausbildungsvermoegen_planfall = []


        for x in xrange(11):
            faktor_waermespeicherung_nullfall.append(boden_anteile_alt[x] * waermespeicherung_multiplikator[x])
            faktor_waermespeicherung_planfall.append(boden_anteile_neu[x] * waermespeicherung_multiplikator[x])

            faktor_staubbindevermoegen_nullfall.append(boden_anteile_alt[x] * staubbindevermoegen_multiplikator[x])
            faktor_staubbindevermoegen_planfall.append(boden_anteile_neu[x] * staubbindevermoegen_multiplikator[x])

            faktor_schadstoffrueckhaltung_nullfall.append(boden_anteile_alt[x] * schadstoffrueckhaltung_multiplikator[x])
            faktor_schadstoffrueckhaltung_planfall.append(boden_anteile_neu[x] * schadstoffrueckhaltung_multiplikator[x])

            faktor_durchlaessigkeit_nullfall.append(boden_anteile_alt[x] * durchlaessigkeit_multiplikator[x])
            faktor_durchlaessigkeit_planfall.append(boden_anteile_neu[x] * durchlaessigkeit_multiplikator[x])

            faktor_bodenueberformung_nullfall.append(boden_anteile_alt[x] * bodenueberformung_multiplikator[x])
            faktor_bodenueberformung_planfall.append(boden_anteile_neu[x] * bodenueberformung_multiplikator[x])

            faktor_oberflaechenabfluss_nullfall.append(boden_anteile_alt[x] * oberflaechenabfluss_multiplikator[x])
            faktor_oberflaechenabfluss_planfall.append(boden_anteile_neu[x] * oberflaechenabfluss_multiplikator[x])

            faktor_grundwasserneubildung_nullfall.append(boden_anteile_alt[x] * grundwasserneubildung_multiplikator[x])
            faktor_grundwasserneubildung_planfall.append(boden_anteile_neu[x] * grundwasserneubildung_multiplikator[x])

            faktor_regenwasserversickerung_nullfall.append(boden_anteile_alt[x] * regenwasserversickerung_multiplikator[x])
            faktor_regenwasserversickerung_planfall.append(boden_anteile_neu[x] * regenwasserversickerung_multiplikator[x])

            faktor_biotopausbildungsvermoegen_nullfall.append(boden_anteile_alt[x] * biotopausbildungsvermoegen_multiplikator[x])
            faktor_biotopausbildungsvermoegen_planfall.append(boden_anteile_neu[x] * biotopausbildungsvermoegen_multiplikator[x])

        #arcpy.AddMessage("Faktoren Nullfall: " + str(faktor_biotopausbildungsvermoegen_nullfall))
        #arcpy.AddMessage("Faktoren Planfall: " + str(faktor_biotopausbildungsvermoegen_planfall))
        table_kennwerte = self.folders.get_table("Leistungskennwerte")
        cursor = arcpy.da.UpdateCursor(table_kennwerte, ["*"])
        for row in cursor:
            cursor.deleteRow()

        def get_kennwert(quotient):
            return round(quotient/10, 1)

        quotient_waermespeicherung_nullfall = sum(faktor_waermespeicherung_nullfall)
        waermespeicherung_nullfall = get_kennwert(quotient_waermespeicherung_nullfall)
        quotient_waermespeicherung_planfall = sum(faktor_waermespeicherung_planfall)
        waermespeicherung_planfall = get_kennwert(quotient_waermespeicherung_planfall)

        quotient_staubbindevermoegen_nullfall = sum(faktor_staubbindevermoegen_nullfall)
        staubbindevermoegen_nullfall = get_kennwert(quotient_staubbindevermoegen_nullfall)
        quotient_staubbindevermoegen_planfall = sum(faktor_staubbindevermoegen_planfall)
        staubbindevermoegen_planfall = get_kennwert(quotient_staubbindevermoegen_planfall)

        quotient_schadstoffrueckhaltung_nullfall = sum(faktor_schadstoffrueckhaltung_nullfall)
        schadstoffrueckhaltung_nullfall = get_kennwert(quotient_schadstoffrueckhaltung_nullfall)
        quotient_schadstoffrueckhaltung_planfall = sum(faktor_schadstoffrueckhaltung_planfall)
        schadstoffrueckhaltung_planfall = get_kennwert(quotient_schadstoffrueckhaltung_planfall)

        quotient_durchlaessigkeit_nullfall = sum(faktor_durchlaessigkeit_nullfall)
        durchlaessigkeit_nullfall  = get_kennwert(quotient_durchlaessigkeit_nullfall)
        quotient_durchlaessigkeit_planfall = sum(faktor_durchlaessigkeit_planfall)
        durchlaessigkeit_planfall = get_kennwert(quotient_durchlaessigkeit_planfall)

        quotient_bodenueberformung_nullfall = sum(faktor_bodenueberformung_nullfall)
        bodenueberformung_nullfall = get_kennwert(quotient_bodenueberformung_nullfall)
        quotient_bodenueberformung_planfall = sum(faktor_bodenueberformung_planfall)
        bodenueberformung_planfall = get_kennwert(quotient_bodenueberformung_planfall)

        quotient_oberflaechenabfluss_nullfall = sum(faktor_oberflaechenabfluss_nullfall)
        oberflaechenabfluss_nullfall = get_kennwert(quotient_oberflaechenabfluss_nullfall)
        quotient_oberflaechenabfluss_planfall = sum(faktor_oberflaechenabfluss_planfall)
        oberflaechenabfluss_planfall = get_kennwert(quotient_oberflaechenabfluss_planfall)

        quotient_grundwasserneubildung_nullfall = sum(faktor_grundwasserneubildung_nullfall)
        grundwasserneubildung_nullfall = get_kennwert(quotient_grundwasserneubildung_nullfall)
        quotient_grundwasserneubildung_planfall = sum(faktor_grundwasserneubildung_planfall)
        grundwasserneubildung_planfall = get_kennwert(quotient_grundwasserneubildung_planfall)

        quotient_regenwasserversickerung_nullfall = sum(faktor_regenwasserversickerung_nullfall)
        regenwasserversickerung_nullfall = get_kennwert(quotient_regenwasserversickerung_nullfall)
        quotient_regenwasserversickerung_planfall = sum(faktor_regenwasserversickerung_planfall)
        regenwasserversickerung_planfall = get_kennwert(quotient_regenwasserversickerung_planfall)

        quotient_biotopausbildungsvermoegen_nullfall = sum(faktor_biotopausbildungsvermoegen_nullfall)
        #arcpy.AddMessage("Quotient Nullfall: " + str(quotient_biotopausbildungsvermoegen_nullfall))
        biotopausbildungsvermoegen_nullfall = get_kennwert(quotient_biotopausbildungsvermoegen_nullfall)
        quotient_biotopausbildungsvermoegen_planfall = sum(faktor_biotopausbildungsvermoegen_planfall)
        #arcpy.AddMessage("Quotient Planfall: " + str(quotient_biotopausbildungsvermoegen_planfall))
        biotopausbildungsvermoegen_planfall = get_kennwert(quotient_biotopausbildungsvermoegen_planfall)
        #arcpy.AddMessage("Kennwert Nullfall: " + str(biotopausbildungsvermoegen_nullfall))
        #arcpy.AddMessage("Kennwert Planfall: " + str(biotopausbildungsvermoegen_planfall))

        column_values = {"Kategorie": [u"Nullfall", u"Planfall", u"Veränderung"],
                         "Schadstoffrueckhaltung": [schadstoffrueckhaltung_nullfall,schadstoffrueckhaltung_planfall,  schadstoffrueckhaltung_planfall - schadstoffrueckhaltung_nullfall],
                         "Waermespeicherung": [waermespeicherung_nullfall,waermespeicherung_planfall,  waermespeicherung_planfall - waermespeicherung_nullfall],
                         "Durchlaessigkeit": [durchlaessigkeit_nullfall,durchlaessigkeit_planfall, durchlaessigkeit_planfall - durchlaessigkeit_nullfall],
                         "Bodenueberformung": [bodenueberformung_nullfall,bodenueberformung_planfall,  bodenueberformung_planfall - bodenueberformung_nullfall],
                         "Oberflaechenabfluss": [oberflaechenabfluss_nullfall,oberflaechenabfluss_planfall,  oberflaechenabfluss_planfall - oberflaechenabfluss_nullfall],
                         "Grundwasserneubildung": [grundwasserneubildung_nullfall,grundwasserneubildung_planfall,  grundwasserneubildung_planfall - grundwasserneubildung_nullfall],
                         "Regenwasserversickerung": [regenwasserversickerung_nullfall,regenwasserversickerung_planfall,  regenwasserversickerung_planfall - regenwasserversickerung_nullfall],
                         "Biotopausbildungsvermoegen": [biotopausbildungsvermoegen_nullfall,biotopausbildungsvermoegen_planfall, biotopausbildungsvermoegen_planfall - biotopausbildungsvermoegen_nullfall],
                         "Staubbindevermoegen": [staubbindevermoegen_nullfall,staubbindevermoegen_planfall,  staubbindevermoegen_planfall - staubbindevermoegen_nullfall]
                         }
        self.parent_tbx.insert_rows_in_table("Leistungskennwerte", column_values)
