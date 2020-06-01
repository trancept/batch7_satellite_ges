# AUTOGENERATED! DO NOT EDIT! File to edit: notebooks/oco2peak-datasets.ipynb (unless otherwise specified).

__all__ = ['Datasets']

# Cell
import swiftclient
import json
import glob
import os
import pandas as pd
from fastprogress.fastprogress import master_bar, progress_bar
from swiftclient.exceptions import ClientException

class Datasets:
    """
    Utility class to access the Open Stack Swift storage of the project.
    """
    config = None # Dict configuration
    conn = None # swiftclient.Connection object
    container_name = 'oco2'

    def __init__(self, config_file):
        """
        Constructor
        :param config_file: str, Path to config file
        :return:
        """
        # Load config
        with open(config_file) as json_data_file:
            self.config = json.load(json_data_file)
        self.conn = self.swift_con()

    def swift_con(self, config=None):
        """
        Connect to Open Stack Swift
        :param config: dict, Config dictionary.
        :return: swiftclient.Connection
        """
        if config is None:
            config = self.config
        user=config['swift_storage']['user']
        key=config['swift_storage']['key']
        auth_url=config['swift_storage']['auth_url']
        tenant_name=config['swift_storage']['tenant_name']
        auth_version=config['swift_storage']['auth_version']
        options = config['swift_storage']['options']
        self.conn = swiftclient.Connection(user=user,
                                      key=key,
                                      authurl=auth_url,
                                      os_options=options,
                                      tenant_name=tenant_name,
                                      auth_version=auth_version)
        return self.conn

    def upload(self, mask='c:\datasets\*.csv', prefix="/Trash/",content_type='text/csv', recursive=False):
        """
        Upload files to Open Stack Swift
        :param mask: str, Mask for seraching file to upload.
        :param prefix: str, Prefix in destination. Useful to mimic folders.
        :param content_type: str, Content type on the destination.
        :param recursive: boolean, To allow search in sub-folder.
        :return:
        """
        master_progress_bar = master_bar([0])
        for _ in master_progress_bar: None

        for file in progress_bar(glob.glob(mask, recursive=recursive), parent=master_progress_bar):
            with open(file, 'rb') as one_file:
                    upload_to = prefix+ os.path.basename(file)
                    #print('Copy from',file,'to',upload_to)
                    self.conn.put_object(self.container_name, upload_to,
                                                    contents= one_file.read(),
                                                    content_type=content_type) # 'text/csv'
    def get_files_urls(self, prefix, pattern=""):
        """
        Retreive the list of file filtered by the given parameters.
        :param prefix: str, Mandatory to avoid retreiving too many files.
        :param pattern: str, Filter the list of files by this pattern. Complemantary of prefix.
        :return: Array of url
        """
        result=[]
        objects = self.conn.get_container(self.container_name, prefix=prefix, full_listing=True)[1]
        for data in objects:
            if pattern in data['name']:
                url = self.config['swift_storage']['base_url']+data['name']
                result.append(url)
        return result

    def delete_files(self, prefix="/Trash/", pattern='', dry_run=True):
        if dry_run:
            print('Nothing will be deleted. Use dry_run=False to delete.')
        master_progress_bar = master_bar([0])
        for _ in master_progress_bar: None
        objects = self.conn.get_container(self.container_name, prefix=prefix, full_listing=True)[1]
        if len(objects) < 1:
            master_progress_bar.write(f'Nothing to delete')
            return
        for data in progress_bar(objects, parent=master_progress_bar):
            file = data['name']
            if pattern in file:
                #master_progress_bar.write(f'Deleting {file}')
                if not dry_run:
                    try:
                        self.conn.delete_object(self.container_name, file)
                    except ClientException:
                        master_progress_bar.write(f'Error deleting {file}')


    def get_containers(self):
        return self.conn.get_account()[1]
    def get_container(self, container_name='oco2', prefix='/datasets/oco-2/'):
        return self.conn.get_container(container_name, prefix=prefix, full_listing=True)[1]

    def get_url_from_sounding_id(self, sounding_id):
        base_url = self.config['swift_storage']['base_url']
        return base_url+'/datasets/oco-2/peaks-detected-details/peak_data-si_'+sounding_id+'.json'

    def get_dataframe(self, url):
        """
        Read the url of a file and load it with Pandas
        :param url: str, URL of the file to load.
        :return: DataFrame
        """
        # TODO : Switch to GeoPandas ?
        df = None
        extension = url.split('.')[-1].lower()
        if extension == 'csv' or extension == 'xz' or extension == 'bz2':
            df = pd.read_csv(url, sep=';')
            if len(df.columns) == 1: # Very bad because we load it twice !
                df = pd.read_csv(url, sep=',')
        elif extension == 'json':
            df = pd.read_json(url)
        if 'tcwv' not in df.columns:
            df['tcwv'] = 25
        if 'surface_pressure' not in df.columns:
            df['surface_pressure'] = 979
        if 'sounding_id' in df.columns:
            df['sounding_id']= df['sounding_id'].astype('int64')
        return df

    def get_peak_param(self, sounding_id, df_all_peak):
        df_param = df_all_peak.query("sounding_id==@sounding_id")
        if len(df_param)<1:
            print(f'ERROR in oco2peak.Datasets.get_peak_param(...) : sounding_id -{sounding_id}- not found in dataframe !')
            #return {'slope' : 1,'intercept' : 1,'amplitude' : 1,'sigma': 1,'delta': 1,'R' : 1}
            return {}
        param_index = df_param.index[0]
        gaussian_param = df_param.loc[param_index].to_dict()
#         gaussian_param = {
#             'slope' : df_param.loc[param_index, 'slope'],
#             'intercept' : df_param.loc[param_index, 'intercept'],
#             'amplitude' : df_param.loc[param_index, 'amplitude'],
#             'sigma': df_param.loc[param_index, 'sigma'],
#             'delta': df_param.loc[param_index, 'delta'],
#             'R' : df_param.loc[param_index, 'R'],
#         }
        return gaussian_param
    def get_gaussian_param(self, sounding_id, df_all_peak):
        return self.get_peak_param(sounding_id, df_all_peak)