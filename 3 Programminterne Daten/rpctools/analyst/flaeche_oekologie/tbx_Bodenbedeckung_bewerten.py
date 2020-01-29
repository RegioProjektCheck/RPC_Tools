# -*- coding: utf-8 -*-

import arcpy

from rpctools.utils.params import Tbx
from rpctools.utils.encoding import encode
from rpctools.analyst.flaeche_oekologie.script_Bodenbedeckung_bewerten import BodenbedeckungBewertung
from rpctools.utils.constants import Nutzungsart
import rpctools.utils.lib_oekologie as lib_oeko
import os


class TbxBodenBewertung(Tbx):
    """'Bodenbedeckung bewerte"""

    values = [u"Bodenbedeckungsanteile manuell festlegen", u"Bodenbedeckungsanteile aus Zeichnungen importieren"]
    mode = "manuell"
    changed_mode = False

    @property
    def label(self):
        return u'Bodenbedeckung bewerten'

    @property
    def Tool(self):
        return BodenbedeckungBewertung

    def _getParameterInfo(self):

        params = self.par

        # Projekt_auswählen
        param = params.name = arcpy.Parameter()
        param.name = u'Projektname'
        param.displayName = u'Projekt'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'GPString'


        param = params.quelle = arcpy.Parameter()
        param.name = u'Quelle'
        param.displayName = u'Quelle der Bodenbedeckungsanteile bestimmen'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'GPString'
        param.filter.list = self.values
        param.value = self.values[0]


        heading = encode("Bodenbedeckung Nullfall")

        param = params.ueberbauteflaechen_alt = arcpy.Parameter()
        param.name = u'Anteil_an_ueberbauten_Flaechen_alt'
        param.displayName = u'Anteil an überbauten Flächen'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = 0
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = heading

        param = params.wasser_alt = arcpy.Parameter()
        param.name = u'Anteil_an_natuerlichen_Wasserflaechen_alt'
        param.displayName = u'Anteil an natürlichen Wasserflächen'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = 0
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = heading

        param = params.platten_alt = arcpy.Parameter()
        param.name = u'Anteil_an_Platten_alt'
        param.displayName = u'Anteil an Platten'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = 0
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = heading

        param = params.baeume_alt = arcpy.Parameter()
        param.name = u'Anteil_an_Baumen_und_Straeuchern_alt'
        param.displayName = u'Anteil an Bäumen und Sträuchern'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = 0
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = heading

        param = params.rasengittersteine_alt = arcpy.Parameter()
        param.name = u'Anteil_an_wassergebundener_Decke_und_Rasengittersteinen_alt'
        param.displayName = u'Anteil an wassergebundener Decke und Rasengittersteinen'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = 0
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = heading

        param = params.stauden_alt = arcpy.Parameter()
        param.name = u'Anteil_an_Stauden_alt'
        param.displayName = u'Anteil an Stauden'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = 0
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = heading

        param = params.wiese_alt = arcpy.Parameter()
        param.name = u'Anteil_an_Wiesen_alt'
        param.displayName = u'Anteil an Wiesen'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = 0
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = heading

        param = params.beton_alt = arcpy.Parameter()
        param.name = u'Anteil_an_Asphalt_und_Beton_alt'
        param.displayName = u'Anteil an Asphalt und Beton'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = 0
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = heading

        param = params.acker_alt = arcpy.Parameter()
        param.name = u'Anteil_an_Acker_und_offenem_Boden_alt'
        param.displayName = u'Anteil an Acker und offenem Boden'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = 0
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = heading

        param = params.kleinpflaster_alt = arcpy.Parameter()
        param.name = u'Anteil_an_Kleinpflaster_alt'
        param.displayName = u'Anteil an Kleinpflaster'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = 0
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = heading

        param = params.rasen_alt = arcpy.Parameter()
        param.name = u'Anteil_an_Rasen_alt'
        param.displayName = u'Anteil an Rasen'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = 100
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = heading

        param = params.undefiniert_alt = arcpy.Parameter()
        param.name = u'undefiniert_alt'
        param.displayName = u'Undefinierte Fläche'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = 0
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = heading

        heading = encode("Bodenbedeckung Planfall")

        param = params.ueberbauteflaechen_neu = arcpy.Parameter()
        param.name = u'Anteil_an_ueberbauten_Flaechen_neu'
        param.displayName = u'Anteil an überbauten Flächen'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = 0
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = heading

        param = params.wasser_neu = arcpy.Parameter()
        param.name = u'Anteil_an_natuerlichen_Wasserflaechen_neu'
        param.displayName = u'Anteil an natürlichen Wasserflächen'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = 0
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = heading

        param = params.platten_neu = arcpy.Parameter()
        param.name = u'Anteil_an_Platten_neu'
        param.displayName = u'Anteil an Platten'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = 0
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = heading

        param = params.baeume_neu = arcpy.Parameter()
        param.name = u'Anteil_an_Baumen_und_Straeuchern_neu'
        param.displayName = u'Anteil an Bäumen und Sträuchern'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = 0
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = heading

        param = params.rasengittersteine_neu = arcpy.Parameter()
        param.name = u'Anteil_an_wassergebundener_Decke_und_Rasengittersteinen_neu'
        param.displayName = u'Anteil an wassergebundener Decke und Rasengittersteinen'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = 0
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = heading

        param = params.stauden_neu = arcpy.Parameter()
        param.name = u'Anteil_an_Stauden_neu'
        param.displayName = u'Anteil an Stauden'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = 0
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = heading

        param = params.wiese_neu = arcpy.Parameter()
        param.name = u'Anteil_an_Wiesen_neu'
        param.displayName = u'Anteil an Wiesen'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = 0
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = heading

        param = params.beton_neu = arcpy.Parameter()
        param.name = u'Anteil_an_Asphalt_und_Beton_neu'
        param.displayName = u'Anteil an Asphalt und Beton'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = 0
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = heading

        param = params.acker_neu = arcpy.Parameter()
        param.name = u'Anteil_an_Acker_und_offenem_Boden_neu'
        param.displayName = u'Anteil an Acker und offenem Boden'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = 0
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = heading

        param = params.kleinpflaster_neu = arcpy.Parameter()
        param.name = u'Anteil_an_Kleinpflaster_neu'
        param.displayName = u'Anteil an Kleinpflaster'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = 0
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = heading

        param = params.rasen_neu = arcpy.Parameter()
        param.name = u'Anteil_an_Rasen_neu'
        param.displayName = u'Anteil an Rasen'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = 100
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = heading

        param = params.undefiniert_neu = arcpy.Parameter()
        param.name = u'undefiniert_neu'
        param.displayName = u'Undefinierte Fläche'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = 0
        param.filter.type = 'Range'
        param.filter.list = [0, 100]
        param.category = heading

        return params

    def sliderSummenKontrolle(self, listeSliderID, zielwertSlidersumme):
        params = self.par
        istsumme = 0
        for s in listeSliderID:
            istsumme+=params[s].value

        if istsumme <> zielwertSlidersumme:
            abweichung = zielwertSlidersumme - istsumme
            for s in reversed(listeSliderID):
                alterWert = params[s].value
                neuerWert = params[s].value + abweichung
                if neuerWert < 0:
                    neuerWert = 0
                elif neuerWert > zielwertSlidersumme:
                    neuerWert = zielwertSlidersumme
                abweichung = abweichung + alterWert - neuerWert
                params[s].value = neuerWert
        return


    def eingaben_auslesen(self, type):
        params = self.par
        projektname = params.name.value

        workspace_projekt_oekologie = self.folders.get_db('FGDB_Flaeche_und_Oekologie.gdb', projektname)
        tabelle_boden_anteile = os.path.join(workspace_projekt_oekologie, "Bodenbedeckung_Anteile")

        if type == "manuell":
            self.mode = "manuell"
            fields = ["IDBodenbedeckung", "Planfall", "Bodenbedeckung_Anteil"]
            cursor = arcpy.da.SearchCursor(tabelle_boden_anteile, fields)
            for row in cursor:
                if row[1] == 0 and row[0] == 1:
                    params['ueberbauteflaechen_alt'].value = row[2]
                elif row[1] == 0 and row[0] == 2:
                    params['wasser_alt'].value = row[2]
                elif row[1] == 0 and row[0] == 3:
                    params['platten_alt'].value = row[2]
                elif row[1] == 0 and row[0] == 4:
                    params['baeume_alt'].value = row[2]
                elif row[1] == 0 and row[0] == 5:
                    params['stauden_alt'].value = row[2]
                elif row[1] == 0 and row[0] == 6:
                    params['wiese_alt'].value = row[2]
                elif row[1] == 0 and row[0] == 7:
                    params['rasen_alt'].value = row[2]
                elif row[1] == 0 and row[0] == 8:
                    params['rasengittersteine_alt'].value = row[2]
                elif row[1] == 0 and row[0] == 9:
                    params['beton_alt'].value = row[2]
                elif row[1] == 0 and row[0] == 10:
                    params['acker_alt'].value = row[2]
                elif row[1] == 0 and row[0] == 11:
                    params['kleinpflaster_alt'].value = row[2]

                elif row[1] == 0 and row[0] == 12:
                    params['undefiniert_alt'].value = row[2]
                elif row[1] == 1 and row[0] == 1:
                    params['ueberbauteflaechen_neu'].value = row[2]
                elif row[1] == 1 and row[0] == 2:
                    params['wasser_neu'].value = row[2]
                elif row[1] == 1 and row[0] == 3:
                    params['platten_neu'].value = row[2]
                elif row[1] == 1 and row[0] == 4:
                    params['baeume_neu'].value = row[2]
                elif row[1] == 1 and row[0] == 5:
                    params['rasengittersteine_neu'].value = row[2]
                elif row[1] == 1 and row[0] == 6:
                    params['stauden_neu'].value = row[2]
                elif row[1] == 1 and row[0] == 7:
                    params['wiese_neu'].value = row[2]
                elif row[1] == 1 and row[0] == 8:
                    params['beton_neu'].value = row[2]
                elif row[1] == 1 and row[0] == 9:
                    params['acker_neu'].value = row[2]
                elif row[1] == 1 and row[0] == 10:
                    params['kleinpflaster_neu'].value = row[2]
                elif row[1] == 1 and row[0] == 11:
                    params['rasen_neu'].value = row[2]
                elif row[1] == 1 and row[0] == 12:
                    params['undefiniert_neu'].value = row[2]

        elif type == "zeichnung":

            anteile_nullfall, anteile_planfall = lib_oeko.import_zeichenanteile(projektname)
            listeSliderID = ['ueberbauteflaechen_alt',
                             'wasser_alt',
                     'platten_alt',
                     'baeume_alt',
                     'stauden_alt',
                     'wiese_alt',
                     'rasen_alt',
                     'rasengittersteine_alt',
                     'beton_alt',
                     'acker_alt',
                     'kleinpflaster_alt',
                     'undefiniert_alt']
            pointer = 0
            for slider in listeSliderID:
                params[slider].value = anteile_nullfall[pointer]
                pointer += 1

            listeSliderID = ['ueberbauteflaechen_neu',
                             'wasser_neu',
                         'platten_neu',
                         'baeume_neu',
                         'stauden_neu',
                         'wiese_neu',
                         'rasen_neu',
                         'rasengittersteine_neu',
                         'beton_neu',
                         'acker_neu',
                         'kleinpflaster_neu',
                         'undefiniert_neu']
            pointer = 0
            for slider in listeSliderID:
                params[slider].value = anteile_planfall[pointer]
                pointer += 1

            bodenarten = [u'Überbaut',
                          u'Wasser',
                         u'Platten',
                         u'Bäume',
                         u'Stauden',
                         u'Wiese',
                         u'Rasen',
                         u'Gittersteine',
                         u'Beton',
                         u'Acker',
                         u'Kleinpflaster',
                         u'Undefiniert']

            self.delete_rows_in_table("Bodenbedeckung_Zeichnung")
            column_values = {"Nullfall": anteile_nullfall,
                             "Planfall": anteile_planfall,
                             "Bodenbedeckung": bodenarten}
            self.insert_rows_in_table("Bodenbedeckung_Zeichnung", column_values)
            self.mode = "zeichnung_initial"
            self.par.quelle.value = self.values[1]




    def _updateParameters(self, params):
        params = self.par

        if params.name.altered and not params.name.hasBeenValidated:
            self.eingaben_auslesen("manuell")
            self.par.quelle.value = self.values[0]

        listeSliderID_alt = ['ueberbauteflaechen_alt',
                             'wasser_alt',
                             'platten_alt',
                             'baeume_alt',
                             'rasengittersteine_alt',
                             'stauden_alt',
                             'wiese_alt',
                             'beton_alt',
                             'acker_alt',
                             'kleinpflaster_alt',
                             'rasen_alt',
                             'undefiniert_alt'
                                                 ]

        listeSliderID_neu = ['ueberbauteflaechen_neu',
                             'wasser_neu',
                             'platten_neu',
                             'baeume_neu',
                             'rasengittersteine_neu',
                             'stauden_neu',
                             'wiese_neu',
                             'beton_neu',
                             'acker_neu',
                             'kleinpflaster_neu',
                             'rasen_neu',
                             'undefiniert_neu']

        if params.quelle.altered and not params.quelle.hasBeenValidated:
            if self.par.quelle.value == self.values[1]:
                self.eingaben_auslesen("zeichnung")
##                for r in listeSliderID_alt:
##                    params[r].enabled = False
##                for r in listeSliderID_neu:
##                    params[r].enabled = False
##          else:
##                for r in listeSliderID_alt:
##                    params[r].enabled = True
##                for r in listeSliderID_neu:
##                    params[r].enabled = True

        zielwertSlidersumme = 100

        for r in listeSliderID_alt:
            if params[r].altered:
                if self.changed_mode == False:
                    if self.mode == "zeichnung":
                        self.mode = "manuell"
                        self.par.quelle.value = self.values[0]
                    elif self.mode == "zeichnung_initial":
                        self.changed_mode = True
                        self.mode = "zeichnung"
                        self.par.quelle.value = self.values[1]
                self.sliderSummenKontrolle(listeSliderID_alt, zielwertSlidersumme)

        for r in listeSliderID_neu:
            if params[r].altered:
                if self.changed_mode == False:
                    if self.mode == "zeichnung":
                        self.mode = "manuell"
                        self.par.quelle.value = self.values[0]
                    elif self.mode == "zeichnung_initial":
                        self.changed_mode = True
                        self.mode = "zeichnung"
                        self.par.quelle.value = self.values[1]
                self.sliderSummenKontrolle(listeSliderID_neu, zielwertSlidersumme)

        self.changed_mode = False

    def bodenbedeckung_eintragen(self, polygon, bodenbedeckung, planfall):
        column_values = {
            'IDBodenbedeckung': bodenbedeckung,
            'SHAPE@': polygon
        }

        tablename = 'Bodenbedeckung_Planfall' if planfall \
            else 'Bodenbedeckung_Nullfall'

        table = self.folders.get_table(
            tablename, "FGDB_Flaeche_und_Oekologie.gdb")

        cursor = arcpy.da.UpdateCursor(table, ["SHAPE@wkt"])
        for row in cursor:
            geom = arcpy.FromWKT(row[0])
            difference = geom.difference(polygon)
            row[0] = difference.WKT
            cursor.updateRow(row)

        self.insert_rows_in_table(tablename, column_values,
                                  "FGDB_Flaeche_und_Oekologie.gdb")

    def _updateMessages(self, params):

        par = self.par
        if par.undefiniert_alt.value != 0:
            par.undefiniert_alt.setErrorMessage(u'Bitte weisen Sie der kompletten Fläche eine Bodenbedeckung zu!')
        if par.undefiniert_neu.value != 0:
            par.undefiniert_neu.setErrorMessage(u'Bitte weisen Sie der kompletten Fläche eine Bodenbedeckung zu!')



class TbxBodenEntfernen(Tbx):
    """Toolbox Boden entfernen"""
    anzeige_an = False

    @property
    def label(self):
        return u'BodenbedeckungEntfernen'

    @property
    def Tool(self):
        return BodenbedeckungEntfernen

    def _getParameterInfo(self):

        params = self.par

        # Projekt_auswählen
        param = params.name = arcpy.Parameter()
        param.name = u'Projektname'
        param.displayName = u'Projekt'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'GPString'

        return params

class TbxBodenAnzeigen(Tbx):
    """Toolbox Boden anzeigen"""

    @property
    def label(self):
        return u'BodenbedeckungAnzeigen'

    @property
    def Tool(self):
        return BodenbedeckungAnzeigen

    def _getParameterInfo(self):

        params = self.par

        # Projekt_auswählen
        param = params.name = arcpy.Parameter()
        param.name = u'Projektname'
        param.displayName = u'Projekt'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'GPString'

        return params
