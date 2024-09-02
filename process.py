import os
import utils
import rioxarray as rx
from senHub import SenHub
from sentinelhub import  SHConfig, MimeType

CONFIG = utils.parse_app_config()
config = SHConfig()
config.instance_id       = CONFIG['Sentinel']['InstanceId'].get()
config.sh_client_id      = CONFIG['Sentinel']['ClientId'].get()
config.sh_client_secret  = CONFIG['Sentinel']['ClientSecret'].get()


def Download_image_in_given_date(clientName, metric, df, field, date, mime_type = MimeType.TIFF):
    sen_obj = SenHub(config, mime_type = mime_type)
    download_path = f'./{clientName}/raw/{metric}/{date}/field_{field}/'
    bbox = utils.calculate_bbox(df, field)
    evalscript = utils.Scripts[metric]
    sen_obj.set_dir(download_path)
    sen_obj.make_bbox(bbox)
    sen_obj.make_request(evalscript, date)
    data = sen_obj.download_data()
    return data

def mask_downladed_image(clientName, metric, df, field, date):
    download_path = utils.get_downloaded_location_img_path(clientName, metric, date, field)
    im = rx.open_rasterio(download_path)
    field_vals = df.loc[df['Field_Id'] == field]
    field_geom = field_vals.geometry 
    crs = field_vals.crs
    clipped = im.rio.clip(field_geom, crs, drop=True)
    save_dir_path = f'./{clientName}/processed/{metric}/{date}/field_{field}/'
    os.makedirs(save_dir_path, exist_ok=True)
    save_tiff_path = save_dir_path + 'masked.tiff'
    clipped.rio.to_raster(save_tiff_path)
    return save_tiff_path

def convert_maske_image_to_geodataframe(clientName, metric, df, field, date, crs):
    imagePath = utils.get_masked_location_img_path(clientName, metric, date, field)
    im = rx.open_rasterio(imagePath)
    gdf = utils.tiff_to_geodataframe(im, metric, date, crs)
    save_dir_path = f'./{clientName}/curated/{metric}/{date}/field_{field}/'
    os.makedirs(save_dir_path, exist_ok=True)
    save_geojson_path = save_dir_path + 'masked.geojson'
    gdf.to_file(save_geojson_path, driver='GeoJSON')
    return save_geojson_path
