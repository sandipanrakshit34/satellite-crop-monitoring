import utils
import process
import requests
import geopandas as gpd
from senHub import SenHub
import matplotlib.image as mpimg

from PIL import Image
from sentinelhub import  SHConfig, MimeType

CONFIG = utils.parse_app_config()
config = SHConfig()
config.instance_id       = CONFIG['Sentinel']['InstanceId'].get()
config.sh_client_id      = CONFIG['Sentinel']['ClientId'].get()
config.sh_client_secret  = CONFIG['Sentinel']['ClientSecret'].get()

def get_available_dates_for_field(df, field, year, start_date='', end_date=''):
    bbox = utils.calculate_bbox(df, field)
    token = SenHub(config).token
    headers = utils.get_bearer_token_headers(token)
    if start_date == '' or end_date == '':
        start_date = f'{year}-01-01'
        end_date = f'{year}-12-31'
    data = f'{{ "collections": [ "sentinel-2-l2a" ], "datetime": "{start_date}T00:00:00Z/{end_date}T23:59:59Z", "bbox": {bbox}, "limit": 100, "distinct": "date" }}'
    response = requests.post('https://services.sentinel-hub.com/api/v1/catalog/search', headers=headers, data=data)
    try:
        features = response.json()['features']
    except:
        print(response.json())
        features = []
    return features

def get_cuarted_df_for_field(df, field, date, metric, clientName):
    curated_date_path =  utils.get_curated_location_img_path(clientName, metric, date, field)
    if curated_date_path is not None:
        curated_df = gpd.read_file(curated_date_path)
    else:
        process.Download_image_in_given_date(clientName, metric, df, field, date)
        process.mask_downladed_image(clientName, metric, df, field, date)
        process.convert_maske_image_to_geodataframe(clientName, metric, df, field, date, df.crs)
        curated_date_path =  utils.get_curated_location_img_path(clientName, metric, date, field)
        curated_df = gpd.read_file(curated_date_path)
    return curated_df

def get_True_color_data(df, field, date, clientName):
    metric = 'TRUECOLOR'
    image_date_path =  utils.get_downloaded_location_img_path(clientName, metric, date, field, extension='png')
    if image_date_path is not None:
       img = mpimg.imread(image_date_path)
    else:
        process.Download_image_in_given_date(clientName, metric, df, field, date, mime_type = MimeType.PNG)
        image_date_path =  utils.get_downloaded_location_img_path(clientName, metric, date, field, extension='png')
        img = mpimg.imread(image_date_path)
    return img
