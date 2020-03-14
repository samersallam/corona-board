from data_preprocessing import DataPreprocessing , DataFiltering
from data_analysis import DataSummary, LocationProfileSummary, AnalysisFacad, DataTimeAnalysis,    DataLocationLevelAnalysis, LocationProfileAnalysisFacad, DataCountryAnalysis

from abc import ABCMeta, abstractmethod
from bokeh.models.widgets import Tabs, Panel
from bokeh.plotting import figure, show, output_notebook, reset_output, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, LogColorMapper, ColorBar, BasicTicker, Label
from bokeh.transform import transform
from bokeh.tile_providers import get_provider, Vendors
from bokeh.layouts import column, row
from bokeh.models.tickers import FixedTicker
from datetime import datetime, date, timedelta
import numpy as np
from bs4 import BeautifulSoup
import codecs
import pandas as pd

import warnings
warnings.filterwarnings("ignore")


# In[2]:


class SummaryParams:
    plot_width3 = 300
    plot_width2 = 450

    plot_height = 60
        
    text_font_size = '12pt'
    title_text_font_size = '16pt'
    text_color = 'white'
    text_font = 'times'
    
    title = ['Corona Board']

class WWSummaryParams:    
    title_offset = {
        'x': [80],
        'y': [120]
    }
    
    x_offset = [
        [[130, 110], [130, 110], [100, 140]],
        [[80, 130], [80, 130], [80, 140]],
        [[80, 130], [80, 130], [100, 120]],
        [[80, 130], [80, 130], [100, 130]],
        [[80, 130], [80, 130], [20, 130]]
    ]

    y_offset = [
        [[30, 10], [30, 10], [30, 10]],
        [[30, 10], [30, 10], [30, 10]],
        [[30, 10], [30, 10], [30, 10]],
        [[30, 10], [30, 10], [30, 10]],
        [[30, 10], [30, 10], [30, 10]]
    ]
    
class ProfileLocationSummaryParams:
    title_offset = {
        'x': [80],
        'y': [100]
    }
    
    x_offset = [
        [[210, 180], [210, 180]],
        [[170, 200], [170, 200]],
        [[130, 190], [130, 190]],
        [[80, 130], [80, 130], [100, 130]]
    ]

    y_offset = [
        [[30, 10], [30, 10]],
        [[30, 10], [30, 10]],
        [[30, 10], [30, 10]],
        [[30, 10], [30, 10], [30, 10]]
    ]
    
class Color:
    country = '#136207'
    daily_cases = '#4f74e3'
    total_cases = '#002952'
    daily_deaths = '#c2233d'
    total_deaths = '#420000'
    title = 'darkslategray'
    fatal_rate = '#c2233d'
    
class FigureParams:
    plot_width = 600
    plot_height = 350
    tools = "pan,reset,save"
    
class LineGraphParams:
    line_width = 3
    circle_line_width = 3
    circle_size = 8
    circle_fill_color = 'white'

class BarParams:
    bar_width = 0.5
    single_bar_width = 0.2
    plot_width = FigureParams.plot_width
    plot_height = 900
    legend_font_size = '4pt'
    color = ['#002952', '#006ab8', '#97a3ff']
    legend_font_size = '8pt'
    tools = "pan,reset,save,hover"
    
class MapParams:
    plot_width = 1200
    plot_height = 575
    world_wide_x_range = [-19857991.737816792, 19180984.47683482]
    world_wide_y_range = [-6484240.26926857, 6668894.01535062]
    plot_scale = np.log10
    plot_scale_factor = 10
    lat = 'merc_lat'
    long = 'merc_long'
    tools = "pan,reset,save,box_zoom"

class Graph(metaclass=ABCMeta):
    
    periods_names = {
            'd': 'Day',
            'w': 'Week',
            'm': 'Month'
        }
    
    def __init__(self, data_df):
        
        self.data_df = data_df
        self.data_df = self.data_df.fillna(0)
        self.source = ColumnDataSource(self.data_df)
        self.figure = None
    
    def show_in_notebook(self):
        output_notebook()
        show(self.figure)
    
    def set_legend_location(self, location):
        self.figure.legend.location = location
        
    @staticmethod
    def final_layout(figures):
        layout = list()
        for f in figures:
            layout.append(row(f))
            
        return column(layout)
    
    @abstractmethod
    def render(self):
        pass
    
class Utilities:
    @staticmethod
    def cases_deaths_to_log(total_cases_deaths, fatality_rate, selected_level):
        data_df = total_cases_deaths.merge(fatality_rate, on='country')

        data_df['total_cases_log'] = data_df.total_cases.apply(
            lambda x: np.log(x + 0.1) * 50 if x != 0 else 0)
        
        data_df['total_deaths_log'] = data_df.apply(
            lambda x: (x['total_cases_log'] * x['fatality_rate']) / 100, axis=1)

        data_df['total_cases_log'] = data_df['total_cases_log'] - data_df['total_deaths_log']
        
        return data_df
    
    
    @staticmethod
    def create_progress_df(df, to_be_dropped, columns_names):
        df = df.drop(columns = to_be_dropped)
        
        df.columns = columns_names
        df['accumelator'] = df[[columns_names[len(columns_names) - 1]]].apply(lambda r: 100 - r)
        return df
    
    
    @staticmethod
    def get_level_data(df, level, location):
        level_df = df[df[level] == location]
        
        return level_df

class NumCountriesDateGraph(Graph):
    x_axis_label = 'Date'
    y_axis_label = '# Countries'
    x_axis_type = 'datetime'
    
    def __init__(self, time_analyser, rate, selected_level= None,location_name=None):
        data_df = time_analyser.number_of_countries(rate, selected_level=selected_level,
                                                    location_name=location_name)

        if data_df.empty:
            data_df = time_analyser.number_of_countries(rate, selected_level=None,
                                                    location_name=None)
            data_df['country'] = data_df.country.apply(lambda x: 0)
            
        super().__init__(data_df)
        self.rate = rate
        
    @property
    def title(self):
        t = 'Number Of Infected Countries Per {} (2019 - nCoV)'
        return t.format(Graph.periods_names[self.rate])
    
    def render(self):
        # Create the main figure
        x_range = [self.data_df.date.min() - timedelta(days=1), 
                   self.data_df.date.max() + timedelta(days=1)]
        y_range = [self.data_df.country.min() - 1, self.data_df.country.max() + 1]
        
        self.figure = figure(
            plot_width = FigureParams.plot_width, 
            plot_height = FigureParams.plot_height, 
            title = self.title,
            x_axis_label = NumCountriesDateGraph.x_axis_label, 
            y_axis_label = NumCountriesDateGraph.y_axis_label,
            x_axis_type = NumCountriesDateGraph.x_axis_type,
            x_range=x_range,
            y_range=y_range,
            tools=FigureParams.tools)
        
        # Render the line
        x,y = 'date', 'country'
        self.figure.line(x, y, source=self.source,
            line_width = LineGraphParams.line_width, 
            legend_label = NumCountriesDateGraph.y_axis_label,
            color = Color.country)

        
        # Render the circle
        self.figure.circle(x,y, source=self.source,
            line_width = LineGraphParams.circle_line_width,
            fill_color = LineGraphParams.circle_fill_color,
            size = LineGraphParams.circle_size,
            legend_label = NumCountriesDateGraph.y_axis_label,
            color = Color.country)
        
        
        self.set_legend_location('top_left')
        self.set_up_hovering()
        
    def set_up_hovering(self):
        hover = HoverTool(
                    tooltips=[(NumCountriesDateGraph.x_axis_label, '@date{%F}'),
                              (NumCountriesDateGraph.y_axis_label, '@country')],
                    formatters={'date': 'datetime'})
        self.figure.add_tools(hover)

class TotalDailyDeathsDateGraph(Graph):
    x_axis_label = 'Date'
    y_axis_label_daily = '# Deaths'
    y_axis_label_total = '# Total Deaths'
    x_axis_type = 'datetime'
    
    def __init__(self, time_analyser, rate, selected_level= None,location_name=None):
        self.selected_level = selected_level
        self.location_name= location_name
        self.time_analyser = time_analyser
        self.data_df = self.time_analyser.daily_and_total_deaths(rate,'daily_deaths', 'total_deaths',
                                                       self.selected_level,self.location_name)
        super().__init__(self.data_df)
        self.rate = rate
        
    @property
    def title(self):
        if self.rate == 'd':
            return 'Daily And Total Number Of Deaths (2019 - nCoV)'
        elif self.rate == 'm':
            return 'Monthly And Total Number Of Deaths (2019 - nCoV)'
    
    def render(self):
        # Create the main figure
        x_range = [self.data_df.date.min() - timedelta(days=1), 
                   self.data_df.date.max() + timedelta(days=1)]
        y_range = [self.data_df.total_deaths.min() - 10, self.data_df.total_deaths.max() + 10]
        
        self.figure = figure(
            plot_width = FigureParams.plot_width, 
            plot_height = FigureParams.plot_height, 
            title = self.title,
            x_axis_label = TotalDailyDeathsDateGraph.x_axis_label, 
            y_axis_label = '# Deaths',
            x_axis_type = TotalDailyDeathsDateGraph.x_axis_type,
            x_range=x_range,
            y_range=y_range,
            tools=FigureParams.tools)
        
        # Render the line2  
        x,y = 'date', 'total_deaths'
        self.figure.line(x, y, source=self.source,
            line_width = LineGraphParams.line_width, 
            #legend_label = TotalDailyDeathsDateGraph.y_axis_label,
            legend_label = '# ' + ' '.join(y.split('_')).title(),            
            color = Color.total_deaths)
        
        # Render the circle
        fig = self.figure.circle(x,y, source=self.source,
            line_width = LineGraphParams.circle_line_width,
            fill_color = LineGraphParams.circle_fill_color,
            size = LineGraphParams.circle_size,
            #legend_label = TotalDailyDeathsDateGraph.y_axis_label,
            legend_label = '# ' + ' '.join(y.split('_')).title(),               
            color =Color.total_deaths)
        
        self.set_up_hovering(TotalDailyDeathsDateGraph.y_axis_label_total, y, fig)
        
        
        # Render the line
        if self.rate == 'm':
            x,y = 'date', 'monthly_deaths'
        else:
            x,y = 'date', 'daily_deaths'
            
        leg = {
            'm': '# Monthly Deaths',
            'd': '# Daily Deaths',
        }
        self.figure.line(x, y, source=self.source,
            line_width = LineGraphParams.line_width, 
            #legend_label = TotalDailyDeathsDateGraph.y_axis_label,
            legend_label = leg[self.rate],
            color = Color.daily_deaths)
        
        # Render the circle
        fig = self.figure.circle(x, y, source=self.source,
            line_width = LineGraphParams.circle_line_width,
            fill_color = LineGraphParams.circle_fill_color,
            size = LineGraphParams.circle_size,
            #legend_label = TotalDailyDeathsDateGraph.y_axis_label,
            legend_label = leg[self.rate],
            color = Color.daily_deaths)
        
        self.set_up_hovering(TotalDailyDeathsDateGraph.y_axis_label_daily, y, fig)
        self.set_legend_location('top_left')
        
    def set_up_hovering(self, label, value, fig):
        hover = HoverTool(
            renderers=[fig],
            tooltips=[(TotalDailyDeathsDateGraph.x_axis_label, '@date{%F}'),
                      (label, f'@{value}')],
            formatters={'date': 'datetime'})
        
        self.figure.add_tools(hover)

class TotalDailyCasesDateGraph(Graph):
    x_axis_label = 'Date'
    y_axis_label_daily = '# Cases'
    y_axis_label_total = '# Total Cases'
    x_axis_type = 'datetime'
    
    def __init__(self, time_analyser, rate,selected_level = None,location_name = None):
        self.selected_level=selected_level
        self.location_name=location_name
        data_df = time_analyser.daily_and_total_cases(rate,'daily_cases', 'total_cases',
                                                      self.selected_level,self.location_name)
        super().__init__(data_df)
        self.rate = rate
        
    @property
    def title(self):
        if self.rate == 'd':
            return 'Daily And Total Number Of Cases (2019 - nCoV)'
        elif self.rate == 'm':
            return 'Monthly And Total Number Of Cases (2019 - nCoV)'
    
    def render(self):
        # Create the main figure
        x_range = [self.data_df.date.min() - timedelta(days=1), 
                   self.data_df.date.max() + timedelta(days=1)]
        y_range = [self.data_df.total_cases.min() - 500, self.data_df.total_cases.max() + 500]
        
        self.figure = figure(
            plot_width = FigureParams.plot_width, 
            plot_height = FigureParams.plot_height, 
            title = self.title,
            x_axis_label = TotalDailyCasesDateGraph.x_axis_label, 
            y_axis_label = '# Cases',
            x_axis_type = TotalDailyCasesDateGraph.x_axis_type,
            x_range=x_range,
            y_range=y_range,
            tools=FigureParams.tools)
        
        # Render the line
        x,y = 'date', 'total_cases'
        self.figure.line(x, y, source=self.source,
            line_width = LineGraphParams.line_width, 
            legend_label = '# ' + ' '.join(y.split('_')).title(),            
            color = Color.total_cases)
        
        # Render the circle
        fig = self.figure.circle(x,y, source=self.source,
            line_width = LineGraphParams.circle_line_width,
            fill_color = LineGraphParams.circle_fill_color,
            size = LineGraphParams.circle_size,
            legend_label = '# ' + ' '.join(y.split('_')).title(),               
            color =Color.total_cases)
        
        self.set_up_hovering(TotalDailyCasesDateGraph.y_axis_label_total, y, fig)
        
        # Render the line 2
        if self.rate == 'm':
            x,y = 'date', 'monthly_cases'
        else:
            x,y = 'date', 'daily_cases'
        
        leg = {
            'm': '# Monthly Cases',
            'd': '# Daily Cases',
        }
        
        self.figure.line(x, y, source=self.source,
            line_width = LineGraphParams.line_width, 
            legend_label = leg[self.rate],
            color = Color.daily_cases)
        
        # Render the circle
        fig = self.figure.circle(x,y, source=self.source,
            line_width = LineGraphParams.circle_line_width,
            fill_color = LineGraphParams.circle_fill_color,
            size = LineGraphParams.circle_size,
            legend_label = leg[self.rate],
            color = Color.daily_cases)
        
        self.set_up_hovering(TotalDailyCasesDateGraph.y_axis_label_daily, y, fig)
        
        self.set_legend_location('top_left')
        
    def set_up_hovering(self, label, value, fig):
        hover = HoverTool(
            renderers=[fig],
            tooltips=[(TotalDailyDeathsDateGraph.x_axis_label, '@date{%F}'),
                      (label, f'@{value}')],
            formatters={'date': 'datetime'})
        
        self.figure.add_tools(hover)

class FatalityRateDateGraph(Graph):
    x_axis_label = 'Date'
    y_axis_label = '# fatality_rate'
    x_axis_type = 'datetime'    
    
    def __init__(self, time_analyser, rate, selected_level = None, location_name = None):
        data_df = time_analyser.fatality_rate(rate, 'daily_deaths', 'daily_cases',
                                              selected_level, location_name)
        super().__init__(data_df)
        self.rate = rate
        
    @property
    def title(self):
        t = 'Fatality Rate per {} (2019 - nCoV)'
        return t.format(Graph.periods_names[self.rate])
    
    def render(self):
        # Create the main figure
        x_range = [self.data_df.date.min() - timedelta(days=1), 
                   self.data_df.date.max() + timedelta(days=1)]
        y_range = [self.data_df['fatal_rate'].min() - 1, self.data_df['fatal_rate'].max() + 1]
        
        self.figure = figure(
            plot_width = FigureParams.plot_width, 
            plot_height = FigureParams.plot_height, 
            title = self.title,
            x_axis_label = FatalityRateDateGraph.x_axis_label, 
            y_axis_label = FatalityRateDateGraph.y_axis_label,
            x_axis_type = FatalityRateDateGraph.x_axis_type,
            x_range=x_range,
            y_range=y_range,
            tools=FigureParams.tools)
        
        # Render the line
        x,y = 'date', 'fatal_rate'
        self.figure.line(x, y, source=self.source,
            line_width = LineGraphParams.line_width, 
            legend_label = FatalityRateDateGraph.y_axis_label,
            color = Color.fatal_rate)

        
        # Render the circle
        self.figure.circle(x,y, source=self.source,
            line_width = LineGraphParams.circle_line_width,
            fill_color = LineGraphParams.circle_fill_color,
            size = LineGraphParams.circle_size,
            legend_label = FatalityRateDateGraph.y_axis_label,
            color = Color.fatal_rate)
        
        
        self.set_legend_location('top_left')
        self.set_up_hovering()
        
    def set_up_hovering(self):
        hover = HoverTool(
                    tooltips=[(FatalityRateDateGraph.x_axis_label, '@date{%F}'),
                              (FatalityRateDateGraph.y_axis_label, '@fatal_rate')],
                    formatters={'date': 'datetime'})
        self.figure.add_tools(hover)

class FatalityRateBargraph(Graph):
    
    def __init__(self, fatality_df, bar_height, selected_level = 'country', selected_location = None):
        self.bar_height = bar_height
        self.selected_level = selected_level 
        fatality_df = fatality_df.loc[:,~fatality_df.columns.duplicated()]
        
            
        if selected_level != 'country':
            req_cols = [selected_level, 'country', 'fatality_rate']
            
        else:
            req_cols = [selected_level, 'fatality_rate']
        super().__init__(Utilities.create_progress_df(fatality_df, [], req_cols))

    @property
    def title(self):
        return 'Fatality Rate per location(2019-nCoV)'
        
    def render(self):
        self.figure = figure(
            title=self.title,
            y_range=self.data_df.country,
            plot_width=BarParams.plot_width, 
            tooltips="Fatality Rate: @$name%",
            plot_height=BarParams.plot_height,
            tools=BarParams.tools)

        self.figure.hbar_stack(['fatality_rate', 'accumelator'],
                               y='country', height=self.bar_height, color = [Color.daily_deaths, Color.daily_cases], 
                               source=self.source, name = 'fatality_rate')

class InOutChinaBargraph(Graph):
    
    def __init__(self, countries_df, bar_height, selected_level='country', selected_location=None):
        self.bar_height = bar_height
        self.selected_level = selected_level
        
        countries_df = countries_df.loc[:,~countries_df.columns.duplicated()]

        super().__init__(countries_df)

    @property
    def title(self):
        return 'Number of Cases with/without Travel History to China Confirmed (2019-nCoV)'
        
    def render(self):
        self.figure = figure(
            title = self.title,
            y_range=self.data_df.country,
            plot_width = BarParams.plot_width, 
            plot_height = BarParams.plot_height,
            tools=BarParams.tools, tooltips="$name: @$name")
        
        req_columns = ['total_cases_with_travel_history_to_china',
                       'total_cases_with_transmission_outside_china', 
                       'total_cases_with_transmission_site_under_investigation']
        
        legend = [' '.join(col.split('_')[2:]).title() for col in req_columns]

        self.figure.hbar_stack(req_columns, legend_label = legend,
                               y='country', height=self.bar_height, color = BarParams.color, 
                               source=self.source)
        
        self.figure.legend.label_text_font_size = BarParams.legend_font_size
        self.set_legend_location('bottom_right')

class OutbreakRateBargraph(Graph):
    
    def __init__(self, outbreak_df, bar_height, selected_level='country', selected_location=None):
        self.bar_height = bar_height
        self.selected_level = selected_level

        outbreak_df = outbreak_df.loc[:,~outbreak_df.columns.duplicated()]
        
        if selected_level != 'country':
            req_cols = [selected_level, 'country', 'epidemic_outbreak_ratio']
            
        else:
            req_cols = [selected_level, 'epidemic_outbreak_ratio']
                
        super().__init__(Utilities.create_progress_df(outbreak_df, ['total_cases'], req_cols))

    @property
    def title(self):
        return 'Epidemic Outbreak-Percentage of Cases Without Travel History to China (2019-nCoV)'
        
    def render(self):
        self.figure = figure(
            title=self.title,
            y_range=self.data_df.country,
            plot_width=BarParams.plot_width, 
            tooltips="Outbreak Rate: @$name%",
            plot_height=BarParams.plot_height,
            tools=BarParams.tools)

        self.figure.hbar_stack(['epidemic_outbreak_ratio', 'accumelator'],
                               y='country', height=self.bar_height, color = [Color.daily_deaths, Color.daily_cases], 
                               source=self.source, name = 'epidemic_outbreak_ratio')

class CasesDeathsBargraph(Graph):
    
    def __init__(self, total_cases_deaths, fatality_rate, bar_height, selected_level='country', selected_location=None):
        self.bar_height = bar_height
        self.selected_level = selected_level
        
        total_cases_deaths = total_cases_deaths.loc[:,~total_cases_deaths.columns.duplicated()]
        fatality_rate = fatality_rate.loc[:,~fatality_rate.columns.duplicated()]
    
        super().__init__(Utilities.cases_deaths_to_log(total_cases_deaths, fatality_rate, selected_level))

    @property
    def title(self):
        return 'Total Cases and Deaths Confirmed (2019-nCoV)'
        
    def render(self):
        self.figure = figure(
            title=self.title,
            y_range=self.data_df.country,
            plot_width=BarParams.plot_width, 
            tooltips="$name: @$name",
            plot_height=BarParams.plot_height,
            tools=BarParams.tools)

        req_columns = ['total_cases_log',
                       'total_deaths_log']
        
        legend = [' '.join(col.split('_')[:2]).title() for col in req_columns]
        
        self.figure.hbar_stack(req_columns, legend_label = legend,
                               y='country', height=self.bar_height, color = [Color.daily_cases, Color.daily_deaths], 
                               source=self.source, name=['total_cases', 'total_deaths'])
                
        log_label = np.linspace(start=0, stop=self.data_df.total_cases_log.max(), num=7)
        log_label = [int(l) for l in log_label]
        self.figure.xaxis.ticker = log_label
        
        real_label = np.linspace(start=0, stop=self.data_df.total_cases.max(), num=7)
        self.figure.xaxis.major_label_overrides = {int(l): str(int(r)) for l, r in zip(log_label, real_label)}
        
        self.figure.legend.label_text_font_size = BarParams.legend_font_size
        self.set_legend_location('bottom_right')

class CountriesMap(Graph):
    def __init__(self, countries_analyser, level = None, location = None):
        if level is not None:
            countries_analyser = Utilities.get_level_data(countries_analyser, level, location)

        
        countries_analyser['circle_size'] = countries_analyser['total_cases'].apply(
            lambda x: 0 if x == 0\
            else (MapParams.plot_scale(x + 0.5) * MapParams.plot_scale_factor))

        self.sources = {
            'cases': (ColumnDataSource(countries_analyser[countries_analyser.total_deaths == 0]), 
                      Color.daily_cases,
                      'Country Without Deaths'), 
            'deaths': (ColumnDataSource(countries_analyser[countries_analyser.total_deaths > 0]), 
                       Color.daily_deaths,
                      'Country With Deaths')
        }
        self.level = level
        
    @property
    def title(self):
        return f"Infected Locations Over The World  (2019 - nCoV)"
        
    def render(self):
        tile_provider = get_provider(Vendors.CARTODBPOSITRON)
        
        self.figure = figure(plot_width=MapParams.plot_width, 
                             plot_height=MapParams.plot_height,
                             x_range=MapParams.world_wide_x_range,
                             y_range=MapParams.world_wide_y_range,
                             title = self.title,tools = MapParams.tools)
        
        
        self.figure.xaxis.visible  = False
        self.figure.yaxis.visible  = False

        self.figure.xgrid.visible = False
        self.figure.ygrid.visible = False
        
        self.figure.add_tile(tile_provider)
        color = Color.daily_cases
        
        for src in self.sources:        
            fig = self.figure.circle(MapParams.lat, MapParams.long, source = self.sources[src][0],
                               legend_label=self.sources[src][2], size='circle_size', color = self.sources[src][1])
            
            self.set_up_hovering()
        
    def set_up_hovering(self):
        if self.level is None:
            level = 'country'

        else:
            level = self.level
        hover = HoverTool(
                    tooltips=[('#country', f"@country"),
                              ('# Cases', "@total_cases"),
                              ('# Deaths', "@total_deaths"),
                              ('# Cases with travel history to china', 
                               "@total_cases_with_travel_history_to_china"),
                              ('# Cases with transmission outside china', 
                               "@total_cases_with_transmission_outside_china"),
                              ('# Cases with transmission site under investigation', 
                               "@total_cases_with_transmission_site_under_investigation")])
        
        self.figure.add_tools(hover)

class Summary:
    
    @staticmethod
    def render_item(text, x_offset, y_offset, color, width, height, font_size):
        
        f = figure(plot_width=width, plot_height=height)
        
        """Adjusting Figure Attributes"""
        f.xaxis.visible  = False
        f.yaxis.visible  = False

        f.xgrid.visible = False
        f.ygrid.visible = False

        f.toolbar.logo = None                          # remove toolbar
        f.toolbar_location = None                      # remove toolbar
        
        f.background_fill_color = color
        f.border_fill_color = None
        
        f.outline_line_color = color               # figure border color
        f.outline_line_width = 10                     # figure border width
                         
        
        for i, t in enumerate(text):           
            ## add information
            citation = Label(x_offset=x_offset[i], y_offset=y_offset[i], x_units='screen', y_units='screen',
                             text_font_size = font_size, text_color = SummaryParams.text_color, 
                             text_font = SummaryParams.text_font, text=t)

            f.add_layout(citation)
            
        return f 

class WWSummary:
    def __init__(self, world_wide_summary):
        self.information = list()
        summ_element = list()

        for k in world_wide_summary:
            if summ_element != []:
                self.information.append(summ_element)
                summ_element = []
            for kk in world_wide_summary[k]:
                if kk == 'fatality_rate %':
                    summ_element.append([' '.join(kk.split()[0].split('_')).title(), str(world_wide_summary[k][kk]) + '%'])
                else:
                    summ_element.append([' '.join(kk.split()[0].split('_')).title(), str(world_wide_summary[k][kk])])

        self.information.append([('Risk Level - ' + e[0], ' '.join(e[1].split('_')).title()) for e in summ_element])
        self.colors = [
            [Color.title, Color.title, Color.title],

            [Color.country, Color.country, Color.country],

            [Color.total_cases, Color.total_cases, Color.total_cases],

            [Color.daily_deaths, Color.daily_deaths, Color.daily_deaths],
            
            [Color.title, Color.title, Color.title]
        ]

        self.world_wide_summary = world_wide_summary
        
    def render(self):
        columns = list()
        rows = list()
        
        # iterate over rows
        for i in range(len(self.information)):
            if len(rows) > 0:
                columns.append(row(rows))
            
            rows = list()  
            # iterate over columns
            for j in range(len(self.information[i])):
                rows.append(Summary.render_item(self.information[i][j], 
                                                WWSummaryParams.x_offset[i][j], 
                                                WWSummaryParams.y_offset[i][j], 
                                                self.colors[i][j],
                                                width=SummaryParams.plot_width3, 
                                                height=SummaryParams.plot_height,
                                                font_size=SummaryParams.title_text_font_size))
            
        columns.append(row(rows))
        title = Summary.render_item(SummaryParams.title, WWSummaryParams.title_offset['x'], 
                                    WWSummaryParams.title_offset['y'], Color.title,
                                    width=SummaryParams.plot_width3, 
                                    height=len(self.information) * SummaryParams.plot_height,
                                    font_size = SummaryParams.title_text_font_size)
        
        self.figure = row(title, Graph.final_layout(columns))

class LocationSummary:
    def __init__(self, location_summary):
        self.information = [
            [[f'From', location_summary['from_date']], 
             [f'To', location_summary['to_date']]],

            [['Selected Level', location_summary['selected_level']], 
             ['Location Name', location_summary['location_name']]],

            [['First Reported Case on', location_summary['first_reported_cases'].split()[0]],
             ['Number of Cases', str(location_summary['num_cases'])]],

             [['First Reported Death on', location_summary['first_reported_deaths'].split()[0]], 
              ['Number of Deaths', str(location_summary['num_deaths'])], 
              ['Fatality Rate', str(location_summary['fatality_rate']) + '%']]
        ]

        if self.information[3][2][1] == 'nan%':
            self.information[3][2][1] = '0%'
        
        self.colors = [
            [Color.title, Color.title],

            [Color.country, Color.country],

            [Color.total_cases, Color.total_cases],

            [Color.daily_deaths, Color.daily_deaths, Color.daily_deaths]
        ]

        self.location_summary = location_summary
        
    def render(self):
        columns = list()
        rows = list()
        
        # iterate over rows
        for i in range(len(self.information)):
            if len(rows) > 0:
                columns.append(row(rows))
            
            rows = list()  
            # iterate over columns
            for j in range(len(self.information[i])):
                if i == len(self.information) - 1:
                    width = SummaryParams.plot_width3
                    
                else:
                    width = SummaryParams.plot_width2
                rows.append(Summary.render_item(self.information[i][j], 
                                                ProfileLocationSummaryParams.x_offset[i][j], 
                                                ProfileLocationSummaryParams.y_offset[i][j], 
                                                self.colors[i][j],
                                                width=width, 
                                                height=SummaryParams.plot_height,
                                                font_size=SummaryParams.title_text_font_size))
            
        columns.append(row(rows))
        title = Summary.render_item(SummaryParams.title, ProfileLocationSummaryParams.title_offset['x'], 
                                    ProfileLocationSummaryParams.title_offset['y'], Color.title,
                                    width=SummaryParams.plot_width3, 
                                    height=len(self.information) * SummaryParams.plot_height,
                                    font_size = SummaryParams.title_text_font_size)
        
        self.figure = row(title, Graph.final_layout(columns))

class Tab(Graph):
    def __init__(self, summary, locations_map, locations_per_day, locations_per_month,
                 deaths_per_day, deaths_per_month, cases_per_day, cases_per_month, fatality_rate_per_day,
                 fatality_rate_per_month, fatality_rate_per_country, in_out_china_cases, out_break_rate,
                 total_cases_deaths):
        
        # Summary
        self.summary = summary
        
        # Countries Map
        self.locations_map = locations_map
        
        # Number of countries per date
        self.locations_per_day = locations_per_day
        self.locations_per_month = locations_per_month
        
        # Number of deaths per date
        self.deaths_per_day = deaths_per_day
        self.deaths_per_month = deaths_per_month
        
        # Number of cases per date
        self.cases_per_day = cases_per_day
        self.cases_per_month = cases_per_month
        
        # Fatality rate per date
        self.fatality_rate_per_day = fatality_rate_per_day
        self.fatality_rate_per_month = fatality_rate_per_month
        
        # Fatality rate per country
        self.fatality_rate_per_country = fatality_rate_per_country
        
        # Cases details
        self.in_out_china_cases = in_out_china_cases
        
        # Outbreak rate
        self.out_break_rate = out_break_rate
        
        # Cases, Deaths details
        self.total_cases_deaths = total_cases_deaths
        
        
    def render(self): 
        self.summary.render()        
        self.locations_map.render()        
        self.locations_per_day.render()        
        self.locations_per_month.render()        
        self.deaths_per_day.render()        
        self.deaths_per_month.render()        
        self.cases_per_day.render()        
        self.cases_per_month.render()        
        self.fatality_rate_per_day.render()        
        self.fatality_rate_per_month.render()
        self.fatality_rate_per_country.render()
        self.in_out_china_cases.render()        
        self.out_break_rate.render()        
        self.total_cases_deaths.render() 
        
        self.figure = self.final_layout([
            self.summary.figure,
            self.locations_map.figure,
            [self.locations_per_day.figure, self.locations_per_month.figure],
            [self.deaths_per_day.figure, self.deaths_per_month.figure],
            [self.cases_per_day.figure, self.cases_per_month.figure],
            [self.fatality_rate_per_day.figure, self.fatality_rate_per_month.figure],
            [self.in_out_china_cases.figure, self.total_cases_deaths.figure],
            [self.fatality_rate_per_country.figure, self.out_break_rate.figure]
        ])

def get_max_date():
    data_process = DataPreprocessing()
    return data_process.data_df.date.max().date()

def get_all_continent(to_date):
    data_process = DataPreprocessing()
    data_fltr = DataFiltering(data_process.data_df, data_process.locations_df, 
              data_process.risk_assessment_df, data_process.testing_laboratories_df)

    ca = DataCountryAnalysis(data_process, data_fltr, to_date=to_date).get_countries_data()

    return list(ca.continent.unique())

def set_up(to_date = None, selected_level = 'country', location_name = 'China'):
    data_process = DataPreprocessing()
    data_fltr = DataFiltering(data_process.data_df, data_process.locations_df, 
              data_process.risk_assessment_df, data_process.testing_laboratories_df)

    time_analyser = DataTimeAnalysis(data_process, data_fltr, to_date=to_date)

    lc = DataLocationLevelAnalysis(data_process, data_fltr, to_date=to_date)

    af = AnalysisFacad(lc, time_analyser)
    world_wide_stats =  af.get_visualization_data()

    ca = DataCountryAnalysis(data_process, data_fltr, to_date=to_date).get_countries_data()

    data_summary = DataSummary(data_process , data_fltr, to_date = to_date)
    world_wide_summary = data_summary.get_data_summary()

    lc_summary = LocationProfileSummary(data_process, data_fltr, to_date = to_date)
    location_summary = lc_summary.get_specific_location_summary(selected_level, location_name)

    return time_analyser, world_wide_stats, world_wide_summary, location_summary, ca

def get_world_wide_layout(to_date = None):
    time_analyser, world_wide_stats, world_wide_summary, _, ca = set_up(to_date=to_date)
    # World wide summary
    world_wide_summ = WWSummary(world_wide_summary)

    # Countris Map
    cm = CountriesMap(ca)

    #Number of countries per day
    ncv_d = NumCountriesDateGraph(time_analyser, 'd')

    #Number of countries per month
    ncv_m = NumCountriesDateGraph(time_analyser, 'm')

    #Number of deaths per day
    tdd_d = TotalDailyDeathsDateGraph(time_analyser, 'd')#,selected_level = 'country',location_name = 'Japan')

    #Number of deaths per month
    tdd_m = TotalDailyDeathsDateGraph(time_analyser, 'm')#,selected_level = 'country',location_name = 'China')

    #Number of cases per day
    tcd_d = TotalDailyCasesDateGraph(time_analyser, 'd')

    #Number of cases per month
    tcd_m = TotalDailyCasesDateGraph(time_analyser, 'm')

    # Fatality rate per day
    fr_d = FatalityRateDateGraph(time_analyser, 'd')

    # Fatality rate per month
    fr_m = FatalityRateDateGraph(time_analyser, 'm')

    # Fatality rate per country
    fr = FatalityRateBargraph(world_wide_stats['country_fatality_rate'], BarParams.bar_width)

    # Cases With/Without travel history to china
    ioc= InOutChinaBargraph(world_wide_stats['country_cases_details'], BarParams.bar_width)

    # Epidemic outbtreak range
    obr = OutbreakRateBargraph(world_wide_stats['country_outbreak_ratio'], BarParams.bar_width)

    # Total cases and deaths
    cd = CasesDeathsBargraph(world_wide_stats['country_total_cases_death'], 
                   world_wide_stats['country_fatality_rate'], BarParams.bar_width)

    # Create World wide layout
    wwt = Tab(world_wide_summ, cm, ncv_d, ncv_m, tdd_d, tdd_m,
                   tcd_d, tcd_m, fr_d, fr_m, fr, ioc, obr, cd)

    wwt.render()
    return wwt

def get_location_profile_layout(to_date = None, selected_level = 'country', location_name = 'China'):
    time_analyser, world_wide_stats, _, location_summary, ca = set_up(to_date=to_date, 
        selected_level=selected_level, location_name=location_name)
    
    # location profile summary
    loc_summ = LocationSummary(location_summary)

    # Countris Map
    cm = CountriesMap(ca, selected_level, location_name)

    #Number of countries per day
    ncv_d = NumCountriesDateGraph(time_analyser, 'd', selected_level = selected_level, location_name = location_name)

    #Number of countries per month
    ncv_m = NumCountriesDateGraph(time_analyser, 'm', selected_level = selected_level, location_name = location_name)

    #Number of deaths per day
    tdd_d = TotalDailyDeathsDateGraph(time_analyser, 'd', selected_level = selected_level, location_name = location_name)

    #Number of deaths per month
    tdd_m = TotalDailyDeathsDateGraph(time_analyser, 'm', selected_level = selected_level, location_name = location_name)

    #Number of cases per day
    tcd_d = TotalDailyCasesDateGraph(time_analyser, 'd', selected_level = selected_level, location_name = location_name)

    #Number of cases per month
    tcd_m = TotalDailyCasesDateGraph(time_analyser, 'm', selected_level = selected_level, location_name = location_name)

    # Fatality rate per day
    fr_d = FatalityRateDateGraph(time_analyser, 'd', selected_level = selected_level, location_name = location_name)

    # Fatality rate per month
    fr_m = FatalityRateDateGraph(time_analyser, 'm', selected_level = selected_level, location_name = location_name)

    # Fatality rate per country
    fatality_df = world_wide_stats[f'{selected_level.lower()}_fatality_rate']
    fatality_df = fatality_df[fatality_df[selected_level.lower()] == location_name]
    fr = FatalityRateBargraph(fatality_df, BarParams.single_bar_width, 
                              selected_level = selected_level.lower(), selected_location = location_name)

    # Cases With/Without travel history to china
    cases_df = world_wide_stats[f'{selected_level.lower()}_cases_details']
    cases_df = cases_df[cases_df[selected_level.lower()] == location_name]
    ioc= InOutChinaBargraph(cases_df, BarParams.single_bar_width, 
                            selected_level = selected_level.lower(), selected_location = location_name)

    # Epidemic outbtreak range
    outbreak_df = world_wide_stats[f'{selected_level.lower()}_outbreak_ratio']
    outbreak_df = outbreak_df[outbreak_df[selected_level.lower()] == location_name]
    obr = OutbreakRateBargraph(outbreak_df, BarParams.single_bar_width, 
                               selected_level = selected_level.lower(), selected_location = location_name)

    # Total cases and deaths
    cases_deaths_df = world_wide_stats[f'{selected_level.lower()}_total_cases_death']
    cases_deaths_df = cases_deaths_df[cases_deaths_df[selected_level.lower()] == location_name]
    cd = CasesDeathsBargraph(cases_deaths_df, fatality_df, BarParams.single_bar_width, 
                             selected_level = selected_level.lower(), selected_location = location_name)


    location_tap = Tab(loc_summ, cm, ncv_d, ncv_m, tdd_d, tdd_m,
                       tcd_d, tcd_m, fr_d, fr_m, fr, ioc, obr, cd)

    location_tap.render()
    return location_tap

def render_dashboard(active_tab=0, file_name = 'template/dash_board.html'):
    def update_html_element(title, file_name):
        with codecs.open(file_name, 'r') as f:
            layout = f.read()

        # Change the title of the page
        soup = BeautifulSoup(layout, 'lxml')
        tag = soup.title
        tag.string = title

        # Center the dashboard
        body = soup.find("div", {"class": "bk-root"})['align'] = 'center'

        html = soup.prettify("utf-8")
        with open(file_name, 'wb') as f:
            f.write(html)
    
    world_wide = get_world_wide_layout(to_date=get_max_date())

    cont = get_all_continent(get_max_date())
    continent_tabs = [Panel(child=get_location_profile_layout(to_date=get_max_date(), 
        selected_level='continent', 
        location_name=c).figure, title=c.title())
    for c in cont]

    all_tabs = [Panel(child=world_wide.figure, title="World Wide")] + continent_tabs
    dash_board = Tabs(tabs=all_tabs, active=active_tab)
    
    output_file(file_name)
    
    template = """
    {% block postamble %}
    <style>
    .bk-root .bk-tab {
    font-style: normal;
    font-size: medium;
    }


    .bk-root .bk-tabs-header .bk-tab.bk-active{
    background-color: #2F4F4F;
    color: white;
    font-style: normal;
    font-weight: bold;
    font-size: medium;
    }

    </style>
    {% endblock %}
    """    

    save(dash_board, template=template)
    
    update_html_element('Corona Board', file_name)
