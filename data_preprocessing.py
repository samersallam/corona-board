import pandas as pd

class DataPreprocessing:
    """ This class is responsible for data reading and cleaning """
    def __init__(self, dataset_file_name='data/corona_report.xlsx', 
                 locations_file_name='data/coordinates.xlsx',
                 risk_assessment_file_name='data/risk_assessment.xlsx',
                 testing_laboratories='data/testing_laboratories.xlsx'):
        
        self.data_df = pd.read_excel(dataset_file_name)
        self.locations_df = pd.read_excel(locations_file_name)
        self.risk_assessment_df = pd.read_excel(risk_assessment_file_name)
        self.testing_laboratories_df = pd.read_excel(testing_laboratories)
        
        self.convert_date_str_to_datetime()
        self.expand_data_df()
        self.merge_location_info()
        
    def change_country_name(self, old_name, new_name):
        self.data_df.country = self.data_df.country.apply(
            lambda x: x if x != old_name else new_name)
    
    def convert_date_str_to_datetime(self):
        """ This is necessary for resampling the dataframe """
        self.data_df.date = pd.to_datetime(self.data_df.date)
    
    def expand_data_df(self):
        """ Generate one data point for each country per each day """
        
        countries = self.get_list_of_countries()
        from_date, to_date = self.get_start_and_end_date()
        temp_df = self.data_df.set_index('country')

        cases_per_day = []
        first_day = True
        
        for date in pd.date_range(from_date, to_date):
            df = temp_df[temp_df.date == date]
            df = df.reindex(countries).fillna(
                {
                    'total_cases': 0, 
                    'total_deaths': 0,
                    'total_cases_with_travel_history_to_china':0,
                    'total_cases_with_transmission_outside_china':0,
                    'total_cases_with_transmission_site_under_investigation':0,
                    'date': date
                })

            if first_day:
                first_day = False
                df['daily_cases'] = df.total_cases
                df['daily_deaths'] = df.total_deaths
                
            else:
                df['daily_cases'] = df.total_cases - prev_day.total_cases
                df['daily_deaths'] = df.total_deaths - prev_day.total_deaths
        
    
            cases_per_day.append(df)
            prev_day = df

        self.data_df = pd.concat(cases_per_day).reset_index()
    
    def get_list_of_countries(self):
        countries = self.data_df.country.unique().tolist()
        return sorted(countries)
    
    def get_list_of_dates(self):
        return sorted(list(set(self.data_df.date.astype(str).tolist())))
    
    def get_start_and_end_date(self):
        from_date = self.data_df.date.min().date()
        to_date = self.data_df.date.max().date()
        
        return from_date, to_date
    
    def merge_location_info(self):
        self.data_df = self.data_df.merge(self.locations_df, how='left', 
                                          left_on='country', right_on='country')

class DataFiltering:
    """ This class is responsible for data filtering according to the dashboard use cases """
    def __init__(self, data_df, locations_df, risk_assessment_df, testing_laboratories_df):
        self.data_df = data_df
        self.locations_df = locations_df
        self.risk_assessment_df = risk_assessment_df
        self.testing_laboratories_df = testing_laboratories_df
    
    def get_data_df(self):
        return self.data_df
    
    def set_date_as_index(self):
        return self.data_df.set_index('date')
    
    def set_country_as_index(self):
        return self.data_df.set_index('country')
    
    def get_specific_date_stats(self, date):
        return self.data_df[self.data_df.date == pd.Timestamp(date)]
    
    def get_until_specific_date_stats(self, date):
        return self.data_df[self.data_df.date <= pd.Timestamp(date)]
    
    def get_specific_location_stats(self, loc_column, loc_value):
        return self.data_df[self.data_df[loc_column] == loc_value]
    
    def get_specific_date_location_stats(self, date, loc_column, loc_value):
        return self.data_df[(self.data_df[loc_column] == loc_value) & 
                            (self.data_df.date == pd.Timestamp(date))]
    
    def get_until_date_location_stats(self, date, loc_column, loc_value):
        return self.data_df[(self.data_df[loc_column] == loc_value) & 
                            (self.data_df.date <= pd.Timestamp(date))]

    def get_specific_date_level_stats(self,loc_column):
        return self.data_df.groupby([loc_column]).sum()

    def get_locations_df(self):
        return self.locations_df
    
    def get_num_labs_per_country(self, country):
        return self.testing_laboratories_df[self.testing_laboratories_df.country == country]
    
    def get_latest_risk_assessment(self):
        return self.risk_assessment_df.iloc[-3:]
