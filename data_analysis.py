from data_preprocessing import DataPreprocessing , DataFiltering
from pprint import pprint
import pandas as pd
import numpy as np
from pyproj import Proj, transform
import warnings
from datetime import datetime


warnings.filterwarnings("ignore")

# This class is to get the data summary
class DataSummary:
    """ This class is to get the data summary"""
    def __init__(self, preprocessed_data, filtered_data , to_date = None):
        self.preprocessed_data = preprocessed_data
        self.filtered_data = filtered_data
        if to_date is None:
            _,self.to_date = self.preprocessed_data.get_start_and_end_date()   
        else:
            self.to_date = to_date
    
    def get_data_summary(self):
        # define summary needed
        summary = {
             'date_summary':{},
             'location_summary':{},
             'cases_summary':{},
             'deaths_summary':{},
             'who_risk_assesment':{}
        }
        
        # get date summary
        data_df = self.filtered_data.get_until_specific_date_stats(self.to_date)
        from_date, _ = self.preprocessed_data.get_start_and_end_date()
        summary['date_summary']['from'] = str(from_date)
        summary['date_summary']['to']   = str(self.to_date)
        num_of_days =  self.to_date - from_date
        summary['date_summary']['num_of_days'] = num_of_days.days
        
        # get location summary
        location_df = self.filtered_data.get_specific_date_stats(self.to_date)
        summary['location_summary']['num_of_countries']=location_df [location_df.total_cases != 0].country.nunique()
        summary['location_summary']['num_of_regions']=location_df[location_df.total_cases != 0].region.nunique()
        summary['location_summary']['num_of_continents'] = location_df[location_df.total_cases != 0].continent.nunique()
        
        #get cases summary
        cases_inside_china = self.filtered_data.get_specific_date_location_stats(
            self.to_date,'country','China').iloc[0].total_cases
        total_cases = self.filtered_data.get_specific_date_stats(self.to_date).total_cases.sum()
        cases_outside_china = total_cases - cases_inside_china
        summary['cases_summary']['cases_inside_china'] = cases_inside_china
        summary['cases_summary']['cases_outside_china'] = cases_outside_china
        summary['cases_summary']['total_cases'] = total_cases
        
        # get deaths summary
        deaths_inside_china = self.filtered_data.get_specific_date_location_stats(
            self.to_date,'country','China').iloc[0].total_deaths
        total_deaths = self.filtered_data.get_specific_date_stats(self.to_date).total_deaths.sum()
        deaths_outside_china = total_deaths - deaths_inside_china
        fatality_rate = "%.2f" % ((total_deaths/total_cases) * 100)
        
        summary['deaths_summary']['deaths_inside_china'] = deaths_inside_china
        summary['deaths_summary']['deaths_outside_china'] = deaths_outside_china
        summary['deaths_summary']['fatality_rate %'] = fatality_rate
        
        # get risk assesment summary
        risk_assesment = self.filtered_data.get_latest_risk_assessment()
        risk_assesment2=risk_assesment[['location','risk_assesment']]
        risk_assesment2.set_index('location',inplace = True)
        
        summary['who_risk_assesment']['china']=risk_assesment2.to_dict()['risk_assesment']['china']
        summary['who_risk_assesment']['globally']=risk_assesment2.to_dict()['risk_assesment']['globally']
        summary['who_risk_assesment']['outside_of_china']=risk_assesment2.to_dict()['risk_assesment']['outside_of_china']
        return summary
    
class LocationProfileSummary:
    """ This class is to get location profile data """
    def __init__(self, preprocessed_data, filtered_data ,to_date = None ):
        
        self.preprocessed_data = preprocessed_data  
        self.from_date,_ = self.preprocessed_data.get_start_and_end_date() 
        if to_date is None:
            _,self.to_date = self.preprocessed_data.get_start_and_end_date()   
        else:
            self.to_date = to_date
            
        self.filtered_data = filtered_data
        
    def get_specific_location_summary(self, selected_level = 'country',
                                      location_name = 'China'):
        # define summary needed
        summary = {}
        df = self.filtered_data.get_specific_date_location_stats(self.to_date,selected_level,location_name)
        df_summary = df[['total_cases','total_deaths']].sum()
        
        #get first reported date case death
        first_df = self.filtered_data.get_specific_location_stats(selected_level,location_name)
        for i,row in first_df.iterrows():
            if row['total_cases'] > 0:
                first_case_date = row['date']
                break        
                
            else:
                first_case_date = 'not registered yet'
        
        for i,row in first_df.iterrows():
            if row['total_deaths'] > 0:
                first_death_date = row['date']
                #print(first_death_date)
                break
            else:
                first_death_date = 'not registered yet'
                
        summary['selected_level'] = selected_level
        summary['location_name']  = location_name
        summary['from_date']      = str(self.from_date)
        summary['to_date']        = str(self.to_date)
        summary['num_cases']      = df_summary.total_cases
        summary['num_deaths']     = df_summary.total_deaths
        summary['fatality_rate']  = "%.2f" % (df_summary.total_deaths / df_summary.total_cases *100)
        summary['first_reported_cases'] = str(first_case_date)
        summary['first_reported_deaths'] = str(first_death_date)
        return summary   

# Cases (Location-Based)
class DataLocationLevelAnalysis:
    """ This class is to get the cases data according to location """
    def __init__(self, preprocessed_data, filtered_data, to_date = None):
        self.preprocessed_data = preprocessed_data
        self.filtered_data = filtered_data
        if to_date is None:
            _,self.to_date = self.preprocessed_data.get_start_and_end_date()
        else:
            self.to_date = to_date
        

    def get_total_number_cases_deaths_location_date(self,selected_level = 'country', location_name = None):
        """ this function to get total cases and deaths according to location from the first day until the selected day """
        if location_name is None:
            df = self.filtered_data.get_specific_date_stats(self.to_date)
        else:
            df = self.filtered_data.get_specific_date_location_stats(self.to_date,selected_level,location_name)

        result = df.sort_values(by=['total_cases'])
        return result[[selected_level, 'country', 'total_cases', 'total_deaths']]
     
    
    def get_cases_details_location_date(self,selected_level = 'country', location_name = None):
        """ this function to get cases details according to location from the first day until the selected day """
        if location_name is None:
            df = self.filtered_data.get_specific_date_stats(self.to_date)
        else:
            df = self.filtered_data.get_specific_date_location_stats(self.to_date,selected_level,location_name)  
        if selected_level is 'country':
            df = df[df['country'] != 'China']
        else :
            df = df

        result = df.sort_values(by=['total_cases'])
        return result[[selected_level, 'country', 'total_cases_with_travel_history_to_china',
                             'total_cases_with_transmission_outside_china',
                              'total_cases_with_transmission_site_under_investigation']]
    
    
    
    def get_total_no_travel_cases_location_date(self,selected_level = 'country', location_name = None):
        """ this function to get total cases and cases with no travel history
            according to location from the first day until the selected day """
        if location_name is None:
            df = self.filtered_data.get_specific_date_stats(self.to_date)
        else:
            df = self.filtered_data.get_specific_date_location_stats(self.to_date,selected_level,location_name)
            
        df1 = df[[selected_level, 'country', 'total_cases', 
                          'total_cases_with_transmission_outside_china']]

        df1 ['epidemic_outbreak_ratio'] = df1 ['total_cases_with_transmission_outside_china'] / df1['total_cases']
        df1 ['epidemic_outbreak_ratio']= df1 ['epidemic_outbreak_ratio'].apply(lambda x:( x * 100))
        df1 ['epidemic_outbreak_ratio']= df1 ['epidemic_outbreak_ratio'].apply(lambda x: round(x, 2))
        result1 = df1.sort_values(by= ['epidemic_outbreak_ratio'])
        return result1[[selected_level, 'country','total_cases',
                    'epidemic_outbreak_ratio']].fillna(0)
    
    
    
    def get_fat_rate_location_date(self, selected_level = 'country', location_name = None):
        """ this function to get fatality rate """
        if location_name is None:
            df = self.filtered_data.get_specific_date_stats(self.to_date)
        else:
            df = self.filtered_data.get_specific_date_location_stats(self.to_date,selected_level,location_name)
        df1 = df[[selected_level, 'country', 'total_cases','total_deaths']]

        df1['fatality_rate']= df1['total_deaths'] / df1['total_cases']
        df1['fatality_rate'] = df1['fatality_rate'].apply(lambda x:( x * 100))
        df1['fatality_rate'] = df1['fatality_rate'].apply(lambda x: round(x, 2))
        result2 = df1.sort_values(by= ['fatality_rate'])
        return result2[[selected_level,'country','fatality_rate']].fillna(0)
    
    def get_all_data(self):
        result1= self.get_total_no_travel_cases_location_date()
        result2= self.get_fat_rate_location_date()
        result3= pd.merge(result2, result1, on=['country'])
        return result3


class DataTimeAnalysis:
    """ This class is to get the cases data according to location """
    def __init__(self, preprocessed_data,filtered_data,to_date = None):
        self.preprocessed_data = preprocessed_data
        if to_date is None:
            _,self.to_date = self.preprocessed_data.get_start_and_end_date()   
        else:
            self.to_date = to_date
        self.filtered_data = filtered_data
    
    def daily_and_total_cases(self, rate,daily_col, total_col,selected_level = None,location_name= None):
        """ this function to get  number of cases  per day,month """
        if selected_level is None:
            df = self.filtered_data.get_until_specific_date_stats(self.to_date).set_index('date')
        else:
            df = self.filtered_data.get_until_date_location_stats(self.to_date,selected_level,location_name).set_index('date')
        daily_vals = df.resample(rate)[daily_col].sum()
        total_vals = daily_vals.cumsum()
        if rate == 'd':
            result = pd.DataFrame({'daily_cases': daily_vals, 'total_cases': total_vals})
        else:
            result = pd.DataFrame({'monthly_cases': daily_vals, 'total_cases': total_vals})
        return result.reset_index()
    
    def daily_and_total_deaths(self, rate, daily_col, total_col,selected_level = None,location_name= None):
        """ this function to get  number of deaths per day,month """
        if selected_level is None:
            df = self.filtered_data.get_until_specific_date_stats(self.to_date).set_index('date')
        else:
            df = self.filtered_data.get_until_date_location_stats(self.to_date,selected_level,location_name).set_index('date')
        daily_vals = df.resample(rate)[daily_col].sum()
        total_vals = daily_vals.cumsum()
        if rate == 'd':
            result = pd.DataFrame({'daily_deaths': daily_vals, 'total_deaths': total_vals})
        else:
            result = pd.DataFrame({'monthly_deaths': daily_vals, 'total_deaths': total_vals})
        return result.reset_index()
     
    
    def fatality_rate(self, rate, deaths_col, cases_col,selected_level = None,location_name= None):
        """ this function to get fatality rate per day,month """
        if selected_level is None:
            df = self.filtered_data.get_until_specific_date_stats(self.to_date).set_index('date')
        else:
            df = self.filtered_data.get_until_date_location_stats(self.to_date,selected_level,location_name).set_index('date')
        deaths_vals = df.resample(rate)[deaths_col].sum()
        cases_vals =  df.resample(rate)[cases_col].sum()
        fat_vals = deaths_vals / cases_vals
        result = pd.DataFrame({'fatal_rate':fat_vals})
        result['fatal_rate'] = result['fatal_rate'].apply(lambda x:( x * 100))
        result['fatal_rate'] = result['fatal_rate'].apply(lambda x: round(x, 2))
        return result[['fatal_rate']].reset_index()
    
    def number_of_countries(self, rate='d',selected_level = None,location_name= None):
        """ Number of countries infected over time """
        if selected_level is None:
            df = self.filtered_data.get_until_specific_date_stats(self.to_date).set_index('date')
        else:
            df = self.filtered_data.get_until_date_location_stats(self.to_date,selected_level,location_name).set_index('date')
        df = df[df['total_cases'] != 0]
        result = df.resample(rate)['country'].apply(lambda x: x.nunique())
        result = pd.DataFrame(result).reset_index()
        
        return result
    
class AnalysisFacad:
    """ this class to get all our results """
    def __init__(self, location_based_data, data_time):
        self.location_based_data = location_based_data
        self.data_time = data_time
    
    
    def get_visualization_data(self):
        
        visualization = {}
        
        visualization['region_total_cases_death']=self.location_based_data.get_total_number_cases_deaths_location_date('region')
        visualization['region_cases_details'] =self.location_based_data.get_cases_details_location_date('region')
        visualization['region_outbreak_ratio'] =self.location_based_data.get_total_no_travel_cases_location_date('region')
        visualization['region_fatality_rate'] =self.location_based_data.get_fat_rate_location_date('region')
        
        visualization['continent_total_cases_death']=self.location_based_data.get_total_number_cases_deaths_location_date('continent')
        visualization['continent_cases_details'] =self.location_based_data.get_cases_details_location_date('continent')
        visualization['continent_outbreak_ratio'] =self.location_based_data.get_total_no_travel_cases_location_date('continent')
        visualization['continent_fatality_rate'] =self.location_based_data.get_fat_rate_location_date('continent')
        
        visualization['country_total_cases_death']=self.location_based_data.get_total_number_cases_deaths_location_date('country')
        visualization['country_cases_details'] =self.location_based_data.get_cases_details_location_date('country')
        visualization['country_outbreak_ratio'] =self.location_based_data.get_total_no_travel_cases_location_date('country')
        visualization['country_fatality_rate'] =self.location_based_data.get_fat_rate_location_date('country')
        
        visualization['num_countries_per_day'] = self.data_time.number_of_countries('d')
        visualization['num_countries_per_month'] = self.data_time.number_of_countries('m')
        
        visualization['num_cases_per_day']=self.data_time.daily_and_total_cases('d', 'daily_cases', 'total_cases')
        visualization['num_cases_per_month']=self.data_time.daily_and_total_cases('m', 'daily_cases', 'total_cases')
        
        visualization['num_deaths_per_day']=self.data_time.daily_and_total_deaths('d', 'daily_deaths', 'total_deaths')
        visualization['num_deaths_per_month']=self.data_time.daily_and_total_deaths('m', 'daily_deaths', 'total_deaths')
        
        visualization['fatilaty_rate_per_day']=self.data_time.fatality_rate('d', 'daily_deaths', 'daily_cases')
        visualization['fatilaty_rate_per_month']=self.data_time.fatality_rate('m', 'daily_deaths', 'daily_cases')
        
        return visualization  

class LocationProfileAnalysisFacad:
    """ this class to get all our results """
    def __init__(self,location_based_data,data_time):
        self.location_based_data = location_based_data
        self.data_time = data_time
        
    def get_location_profile_visualization_data(self,selected_level,location_name):
        location_profile_visualization = {}
        location_profile_visualization['total_cases_death']=self.location_based_data.get_total_number_cases_deaths_location_date(selected_level,location_name)
        location_profile_visualization['cases_details'] =self.location_based_data.get_cases_details_location_date(selected_level,location_name)
        location_profile_visualization['outbreak_ratio'] =self.location_based_data.get_total_no_travel_cases_location_date(selected_level,location_name)
        location_profile_visualization['fatality_rate'] =self.location_based_data.get_fat_rate_location_date(selected_level,location_name)
        
        location_profile_visualization['num_cases_per_day']=self.data_time.daily_and_total_cases('d', 'daily_cases', 'total_cases',selected_level,location_name)
        location_profile_visualization['num_cases_per_month']=self.data_time.daily_and_total_cases('m', 'daily_cases', 'total_cases',selected_level,location_name)
        
        location_profile_visualization['num_deaths_per_day']=self.data_time.daily_and_total_deaths('d', 'daily_deaths', 'total_deaths',selected_level,location_name)
        location_profile_visualization['num_deaths_per_month']=self.data_time.daily_and_total_deaths('m', 'daily_deaths', 'total_deaths',selected_level,location_name)
        
        location_profile_visualization['fatilaty_rate_per_day']=self.data_time.fatality_rate('d', 'daily_deaths', 'daily_cases',selected_level,location_name)
        location_profile_visualization['fatilaty_rate_per_month']=self.data_time.fatality_rate('m', 'daily_deaths', 'daily_cases',selected_level,location_name)
        
        return location_profile_visualization
        
class DataCountryAnalysis:
    def __init__(self, preprocessed_data, filtered_data, coordinates_file = 'data/coordinates.xlsx', to_date = None):
        self.preprocessed_data = preprocessed_data
        self.filtered_data = filtered_data
        self.coordinates_data = pd.read_excel(coordinates_file)
        self.add_mercator_coordinates()
        if to_date is None:
            _, self.to_date = self.preprocessed_data.get_start_and_end_date()
            
        else:
            self.to_date = to_date
        
    def add_mercator_coordinates(self):
        in_wgs = Proj(init='epsg:4326')
        out_mercator = Proj(init='epsg:3857')
        for i in self.coordinates_data.index:
            self.coordinates_data.at[i, 'merc_lat'], self.coordinates_data.at[i, 'merc_long'] = transform(in_wgs, 
                                                                 out_mercator, 
                                                                 self.coordinates_data.at[i, 'long'], 
                                                                 self.coordinates_data.at[i, 'lat'])

    def get_total_number_cases_deaths(self):
        #_, to_date = self.preprocessed_data.get_start_and_end_date()
        last_day_df = self.filtered_data.get_specific_date_stats(self.to_date)
        return last_day_df[['country', 'total_cases', 'total_deaths', 'date',
                            'total_cases_with_travel_history_to_china', 
                            'total_cases_with_transmission_outside_china', 
                            'total_cases_with_transmission_site_under_investigation',
                           ]]
    
    def get_countries_data(self):
        last_day_df = self.get_total_number_cases_deaths()
        return pd.merge(self.coordinates_data, last_day_df, on=['country'])



