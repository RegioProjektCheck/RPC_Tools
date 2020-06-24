# -*- coding: utf-8 -*-

import arcpy
from rpctools.utils.encoding import encode
from rpctools.utils.diagram import ArcpyDiagram, MatplotDiagram
import numpy as np
#import matplotlib
import locale
#matplotlib.use('agg')
#import matplotlib.ticker as mticker
import pandas as pd


def horizontal_label_values(bars, ax, values=[], force_signum=False):
    for i, bar in enumerate(bars):
        # depending on matplot-version this might always be positive even with
        # negative values, that's why values can be passed
        width = bar.get_width()
        value = values[i] if len(values) > 0 else width
        r_format = '%.1f' if not force_signum else '%+.1f'
        val_label = locale.format_string(r_format, value)
        ha = 'right' if value < 0 else 'left'
        ax.annotate(
            ' ' + val_label if value > 0 else val_label,
            xy=(width if value >= 0 else -abs(width) - 0.4,
                bar.get_y() + bar.get_height() / 2),
            va='center', ha=ha
        )

def u_categories(categories):
    ret = []
    prev = ''
    for category in categories:
        ret.append(category if category != prev else '')
        prev = category
    return ret


class Leistungskennwerte(MatplotDiagram):
    def _create(self, **kwargs):
        labels = kwargs['columns']

        y = np.arange(len(labels))
        width = 0.35  # the width of the bars

        figure, ax = self.plt.subplots()
        bars1 = ax.barh(y + width / 2 + 0.02, kwargs['nullfall'],
                         width, label='Nullfall', color='#fc9403')
        bars2 = ax.barh(y - width / 2 - 0.02, kwargs['planfall'],
                        width, label='Planfall', color='#036ffc')
        ax.set_yticks(y)
        ax.set_yticklabels(labels)
        #categories = u_categories(kwargs['categories'])
        #ax.minorticks_on()
        #ax.set_yticks(y, minor=True)
        #ax.set_yticks(np.arange(len(categories)), minor=False)
        #ax.set_yticklabels(labels, minor=True)
        #ax.set_yticklabels(categories, minor=False)
        #ax.tick_params(axis='y', which='major', pad=150, labelsize=12)

        ax.set_title(kwargs['title'])
        x_label = 'Bewertung'
        if 'max_rating' in kwargs:
            max_rating = kwargs['max_rating']
            ax.axes.set_xlim([0, max_rating + 1])
            x_label += ' (in Punkten von 0 bis {})'.format(max_rating)
        ax.set_xlabel(x_label)
        ax.set_xticks(range(0, max_rating + 1, 1))
        #ax.get_xaxis().set_major_formatter(
            #mticker.FuncFormatter(lambda x, p: '{x:n}'.format(x=x)))
        ax.legend(loc='best')

        horizontal_label_values(bars1, ax)
        horizontal_label_values(bars2, ax)

        #figure.tight_layout()
        box = ax.get_position()
        ax.set_position([box.x0 + box.width * 0.16, box.y0,
                         box.width * 0.84, box.height])
        return ax


class LeistungskennwerteDelta(MatplotDiagram):
    def _create(self, **kwargs):
        labels = kwargs['columns']

        y = np.arange(len(labels))
        data = kwargs['delta']

        figure, ax = self.plt.subplots()
        colors = np.full(len(data), 'g')
        colors[data < 0] = 'r'

        bars = ax.barh(y, data, align='center', color=colors)

        ax.set_yticks(y)
        #categories = u_categories(kwargs['categories'])
        #ax.minorticks_on()
        #ax.set_yticks(y, minor=True)
        #ax.set_yticks(np.arange(len(categories)), minor=False)
        #ax.set_yticklabels(labels, minor=True)
        #ax.set_yticklabels(categories, minor=False)
        #ax.tick_params(axis='y', which='major', pad=150, labelsize=12)

        ax.set_xlabel('Bewertung im Planfall minus Bewertung im Nullfall')
        ax.set_title(kwargs['title'])
        max_rating = kwargs.get('max_rating', 0)
        min_val = -max_rating or min(-3, min(data))
        max_val = max_rating or max(3, max(data))

        ax.set_xlim(left=min_val-1, right=max_val+1)
        ax.set_xticks(range(min_val, max_val+1, 1))
        ax.set_yticklabels(labels)
        #ax.get_xaxis().set_major_formatter(
            #mticker.FuncFormatter(lambda x, p: locale.format_string('%+d', x)))
        ax.axvline(linewidth=1, color='grey')
        ax.legend()

        horizontal_label_values(bars, ax, values=kwargs['delta'],
                                force_signum=True)

        #figure.tight_layout()
        box = ax.get_position()
        ax.set_position([box.x0 + box.width * 0.16, box.y0,
                         box.width * 0.84, box.height])
        return ax


class Dia_Integrationsgrad(ArcpyDiagram):
    _workspace = 'FGDB_Definition_Projekt.gdb'

    def _create(self, **kwargs):
        project_name = self.tbx.par.get_projectname()
        title = encode(
            "{}: Anteil der Plangebietsgrenze (in Prozent), der ..."
            .format(project_name))
        input_template = self.tbx.folders.get_diagram_template(
            'Integrationsgrad')

        graph = arcpy.Graph()
        input_data = self.tbx.folders.get_table("Integrationsgrad", "FGDB_Flaeche_und_Oekologie.gdb")
        graph.addSeriesPie(dataSrc=input_data,
                                   fieldValue = "Umfang",
                                   fieldLabel="Grenze")
        graph.graphPropsGeneral.title = title
        return graph, input_template


class Dia_Wohndichte(ArcpyDiagram):
    _workspace = 'FGDB_Definition_Projekt.gdb'

    def _create(self, **kwargs):
        project_name = self.tbx.par.get_projectname()
        title = encode(
            u"{}: Wohneinheiten pro Hektar Nettowohnbauland"
            .format(project_name))
        input_template = self.tbx.folders.get_diagram_template(
            'Wohndichte')

        graph = arcpy.Graph()
        input_data = self.tbx.folders.get_table("Wohndichte", "FGDB_Flaeche_und_Oekologie.gdb")
        graph.addSeriesBarVertical(dataSrc=input_data,
                                   fieldY= "Wohndichte",
                                   fieldLabel="Typ")
        graph.graphPropsGeneral.title = title
        return graph, input_template

class Dia_Wohnflaechendichte(ArcpyDiagram):
    _workspace = 'FGDB_Definition_Projekt.gdb'

    def _create(self, **kwargs):
        project_name = self.tbx.par.get_projectname()
        title = encode(
            u"{}: qm Wohnfläche pro Hektar Nettowohnbauland"
            .format(project_name))
        input_template = self.tbx.folders.get_diagram_template(
            'Wohnflaechendichte')

        graph = arcpy.Graph()
        input_data = self.tbx.folders.get_table("Wohnflaechendichte", "FGDB_Flaeche_und_Oekologie.gdb")
        graph.addSeriesBarVertical(dataSrc=input_data,
                                   fieldY= "Wohnflaechendichte",
                                   fieldLabel="Typ")
        graph.graphPropsGeneral.title = title
        return graph, input_template

class Dia_Nullfall(ArcpyDiagram):
    _workspace = 'FGDB_Definition_Projekt.gdb'

    def _create(self, **kwargs):
        project_name = self.tbx.par.get_projectname()
        title = encode(
            u"{}: Bodenbedeckung im Nullfall"
            .format(project_name))
        input_template = self.tbx.folders.get_diagram_template(
            'Bodenbedeckung')

        graph = arcpy.Graph()
        input_data = self.tbx.folders.get_table("Bodenbedeckung_Zeichnung", "FGDB_Flaeche_und_Oekologie.gdb")
        graph.addSeriesBarVertical(dataSrc=input_data,
                                   fieldY= "Nullfall",
                                   fieldLabel="Bodenbedeckung")
        graph.graphPropsGeneral.title = title
        return graph, input_template

class Dia_Planfall(ArcpyDiagram):
    _workspace = 'FGDB_Definition_Projekt.gdb'

    def _create(self, **kwargs):
        project_name = self.tbx.par.get_projectname()
        title = encode(
            u"{}: Bodenbedeckung im Planfall"
            .format(project_name))
        input_template = self.tbx.folders.get_diagram_template(
            'Bodenbedeckung')

        graph = arcpy.Graph()
        input_data = self.tbx.folders.get_table("Bodenbedeckung_Zeichnung", "FGDB_Flaeche_und_Oekologie.gdb")
        graph.addSeriesBarVertical(dataSrc=input_data,
                                   fieldY= "Planfall",
                                   fieldLabel="Bodenbedeckung")
        graph.graphPropsGeneral.title = title
        return graph, input_template

class Dia_Waerme(ArcpyDiagram):
    _workspace = 'FGDB_Definition_Projekt.gdb'

    def _create(self, **kwargs):
        project_name = self.tbx.par.get_projectname()
        title = encode(
            u"{}: Bodenkennwert Wärmespeicherung"
            .format(project_name))
        input_template = self.tbx.folders.get_diagram_template(
            'Bodenkennwerte')

        graph = arcpy.Graph()
        input_data = self.tbx.folders.get_table("Leistungskennwerte", "FGDB_Flaeche_und_Oekologie.gdb")
        graph.addSeriesBarVertical(dataSrc=input_data,
                                   fieldY= "Waermespeicherung",
                                   fieldLabel="Kategorie")
        graph.graphPropsGeneral.title = title
        return graph, input_template

class Dia_Staub(ArcpyDiagram):
    _workspace = 'FGDB_Definition_Projekt.gdb'

    def _create(self, **kwargs):
        project_name = self.tbx.par.get_projectname()
        title = encode(
            u"{}: Bodenkennwert Staubbindevermögen"
            .format(project_name))
        input_template = self.tbx.folders.get_diagram_template(
            'Bodenkennwerte')

        graph = arcpy.Graph()
        input_data = self.tbx.folders.get_table("Leistungskennwerte", "FGDB_Flaeche_und_Oekologie.gdb")
        graph.addSeriesBarVertical(dataSrc=input_data,
                                   fieldY= "Staubbindevermoegen",
                                   fieldLabel="Kategorie")
        graph.graphPropsGeneral.title = title
        return graph, input_template

class Dia_Grundwasser(ArcpyDiagram):
    _workspace = 'FGDB_Definition_Projekt.gdb'

    def _create(self, **kwargs):
        project_name = self.tbx.par.get_projectname()
        title = encode(
            u"{}: Bodenkennwert Grundwasserneubildung"
            .format(project_name))
        input_template = self.tbx.folders.get_diagram_template(
            'Bodenkennwerte')

        graph = arcpy.Graph()
        input_data = self.tbx.folders.get_table("Leistungskennwerte", "FGDB_Flaeche_und_Oekologie.gdb")
        graph.addSeriesBarVertical(dataSrc=input_data,
                                   fieldY= "Grundwasserneubildung",
                                   fieldLabel="Kategorie")
        graph.graphPropsGeneral.title = title
        return graph, input_template

class Dia_Schadstoff(ArcpyDiagram):
    _workspace = 'FGDB_Definition_Projekt.gdb'

    def _create(self, **kwargs):
        project_name = self.tbx.par.get_projectname()
        title = encode(
            u"{}: Bodenkennwert Schadstoffrückhaltung"
            .format(project_name))
        input_template = self.tbx.folders.get_diagram_template(
            'Bodenkennwerte')

        graph = arcpy.Graph()
        input_data = self.tbx.folders.get_table("Leistungskennwerte", "FGDB_Flaeche_und_Oekologie.gdb")
        graph.addSeriesBarVertical(dataSrc=input_data,
                                   fieldY= "Schadstoffrueckhaltung",
                                   fieldLabel="Kategorie")
        graph.graphPropsGeneral.title = title
        return graph, input_template

class Dia_Durchlaessigkeit(ArcpyDiagram):
    _workspace = 'FGDB_Definition_Projekt.gdb'

    def _create(self, **kwargs):
        project_name = self.tbx.par.get_projectname()
        title = encode(
            u"{}: Bodenkennwert Durchlässigkeit"
            .format(project_name))
        input_template = self.tbx.folders.get_diagram_template(
            'Bodenkennwerte')

        graph = arcpy.Graph()
        input_data = self.tbx.folders.get_table("Leistungskennwerte", "FGDB_Flaeche_und_Oekologie.gdb")
        graph.addSeriesBarVertical(dataSrc=input_data,
                                   fieldY= "Durchlaessigkeit",
                                   fieldLabel="Kategorie")
        graph.graphPropsGeneral.title = title
        return graph, input_template

class Dia_Ueberformung(ArcpyDiagram):
    _workspace = 'FGDB_Definition_Projekt.gdb'

    def _create(self, **kwargs):
        project_name = self.tbx.par.get_projectname()
        title = encode(
            u"{}: Bodenkennwert Bodenüberformung"
            .format(project_name))
        input_template = self.tbx.folders.get_diagram_template(
            'Bodenkennwerte')

        graph = arcpy.Graph()
        input_data = self.tbx.folders.get_table("Leistungskennwerte", "FGDB_Flaeche_und_Oekologie.gdb")
        graph.addSeriesBarVertical(dataSrc=input_data,
                                   fieldY= "Bodenueberformung",
                                   fieldLabel="Kategorie")
        graph.graphPropsGeneral.title = title
        return graph, input_template

class Dia_Abfluss(ArcpyDiagram):
    _workspace = 'FGDB_Definition_Projekt.gdb'

    def _create(self, **kwargs):
        project_name = self.tbx.par.get_projectname()
        title = encode(
            u"{}: Bodenkennwert Oberflächenabfluss"
            .format(project_name))
        input_template = self.tbx.folders.get_diagram_template(
            'Bodenkennwerte')

        graph = arcpy.Graph()
        input_data = self.tbx.folders.get_table("Leistungskennwerte", "FGDB_Flaeche_und_Oekologie.gdb")
        graph.addSeriesBarVertical(dataSrc=input_data,
                                   fieldY= "Oberflaechenabfluss",
                                   fieldLabel="Kategorie")
        graph.graphPropsGeneral.title = title
        return graph, input_template

class Dia_Regenwasser(ArcpyDiagram):
    _workspace = 'FGDB_Definition_Projekt.gdb'

    def _create(self, **kwargs):
        project_name = self.tbx.par.get_projectname()
        title = encode(
            u"{}: Bodenkennwert Regenwasserversickerung"
            .format(project_name))
        input_template = self.tbx.folders.get_diagram_template(
            'Bodenkennwerte')

        graph = arcpy.Graph()
        input_data = self.tbx.folders.get_table("Leistungskennwerte", "FGDB_Flaeche_und_Oekologie.gdb")
        graph.addSeriesBarVertical(dataSrc=input_data,
                                   fieldY= "Regenwasserversickerung",
                                   fieldLabel="Kategorie")
        graph.graphPropsGeneral.title = title
        return graph, input_template

class Dia_Biotop(ArcpyDiagram):
    _workspace = 'FGDB_Definition_Projekt.gdb'

    def _create(self, **kwargs):
        project_name = self.tbx.par.get_projectname()
        title = encode(
            u"{}: Bodenkennwert Biotopausbildungsvermögen"
            .format(project_name))
        input_template = self.tbx.folders.get_diagram_template(
            'Bodenkennwerte')

        graph = arcpy.Graph()
        input_data = self.tbx.folders.get_table("Leistungskennwerte", "FGDB_Flaeche_und_Oekologie.gdb")
        graph.addSeriesBarVertical(dataSrc=input_data,
                                   fieldY= "Biotopausbildungsvermoegen",
                                   fieldLabel="Kategorie")
        graph.graphPropsGeneral.title = title
        return graph, input_template
