import os
import folium
import confuse
import numpy as np
from math import isnan
import geopandas as gpd
from shapely.geometry import Point
from PIL import Image
from tqdm import tqdm

# Initialzie custom basemaps for folium
basemaps = {
    'Google Maps': folium.TileLayer(
        tiles = 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
        attr = 'Google',
        name = 'Google Maps',
        overlay = True,
        control = True
    ),
    'Google Satellite': folium.TileLayer(
        tiles = 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr = 'Google',
        name = 'Google Satellite',
        overlay = True,
        control = True
    ),
    'Google Terrain': folium.TileLayer(
        tiles = 'https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
        attr = 'Google',
        name = 'Google Terrain',
        overlay = True,
        control = True
    ),
    'Google Satellite Hybrid': folium.TileLayer(
        tiles = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr = 'Google',
        name = 'Google Satellite',
        overlay = True,
        control = True
    ),
    'Esri Satellite': folium.TileLayer(
        tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr = 'Esri',
        name = 'Esri Satellite',
        overlay = True,
        control = True
    ),
    'openstreetmap': folium.TileLayer('openstreetmap'),
    'cartodbdark_matter': folium.TileLayer('cartodbdark_matter')
}


# Dictionary of JavaScript files (More Readable)
scripts_dir = './scripts/'
scripts_files = [f for f in os.listdir(scripts_dir) if f.endswith('.js')]
Scripts = {}
for f in scripts_files:
    key = f.split('.')[0].upper()
    with open(scripts_dir + f) as f:
        Scripts[key] = f.read()

def calculate_bbox(df, field):
    '''
    Calculate the bounding box of a specfic field  ID in a  given data frame
    '''
    field = int(field)
    bbox = df.loc[df['Field_Id'] == field].bounds
    r = bbox.iloc[0]
    return [r.minx, r.miny, r.maxx, r.maxy]

def tiff_to_geodataframe(im, metric, date, crs):
    '''
    Convert a tiff image to a geodataframe
    '''
    x_cords = im.coords['x'].values
    y_cords = im.coords['y'].values
    vals = im.values
    dims = vals.shape
    points = []
    v_s = []
    for lat in range(dims[1]):
        y = y_cords[lat]
        for lon in range(dims[2]):
            x = x_cords[lon]
            v = vals[:,lat,lon]
            if isnan(v[0]):
                continue
            points.append(Point(x,y))
            v_s.append(v.item())   
    d = {f'{metric}_{date}': v_s, 'geometry': points} 
    df = gpd.GeoDataFrame(d, crs = crs)
    return df

def get_bearer_token_headers(bearer_token):
    '''
    Get the bearer token headers to be used in the request to the SentinelHub API
    '''
    headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer '+ bearer_token,
    }
    return headers

def get_downloaded_location_img_path(clientName, metric, date, field, extension='tiff'):
    '''
    Get the path of the downloaded image in TIFF based on the:
    '''
    date_dir = f'./{clientName}/raw/{metric}/{date}/field_{field}/'
    print(f'True Color Date Dir: {date_dir}')
    os.makedirs(date_dir, exist_ok=True)
    intermediate_dirs = os.listdir(date_dir)
    print(f'Intermediate Dirs: {intermediate_dirs}')
    if len(intermediate_dirs) == 0:
        return None
    imagePath = f'{date_dir}{os.listdir(date_dir)[0]}/response.{extension}'
    print(f'Image Path: {imagePath}')
    if not os.path.exists(imagePath):
        return None
    print(f'Image Path: {imagePath}')
    return imagePath

def get_masked_location_img_path(clientName, metric, date, field):
    '''
    Get the path of the downloaded image after applying the mask in TIFF based on the:
    '''
    date_dir = f'./{clientName}/processed/{metric}/{date}/field_{field}/'
    imagePath = date_dir + 'masked.tiff'
    return imagePath

def get_curated_location_img_path(clientName, metric, date, field):
    '''
    Get the path of the downloaded image after applying the mask and converting it to geojson formay based on the:
    '''
    date_dir = f'./{clientName}/curated/{metric}/{date}/field_{field}/'
    imagePath = date_dir + 'masked.geojson'

    if os.path.exists(imagePath):
        return imagePath
    else:
        return None

def parse_app_config(path=r'config-fgm-dev.yaml'):
    config = confuse.Configuration('CropHealth', __name__)
    config.set_file(path)
    return config


def fix_image(img):
    def normalize(band):
        band_min, band_max = (band.min(), band.max())
        return ((band-band_min)/((band_max - band_min)))
    def brighten(band):
        alpha=3
        beta=0
        return np.clip(alpha*band+beta, 0,255)
    def gammacorr(band):
        gamma=0.9
        return np.power(band, 1/gamma)
    red   = img[:, :, 0]
    green = img[:, :, 1]
    blue  = img[:, :, 2]
    red_b=brighten(red)
    blue_b=brighten(blue)
    green_b=brighten(green)
    red_bg=gammacorr(red_b)
    blue_bg=gammacorr(blue_b)
    green_bg=gammacorr(green_b)
    red_bgn = normalize(red_bg)
    green_bgn = normalize(green_bg)
    blue_bgn = normalize(blue_bg)
    rgb_composite_bgn= np.dstack((red_b, green_b, blue_b))
    return rgb_composite_bgn


def creat_gif(dataset, gif_name, duration=50):
    '''
    Create a gif from a list of images
    '''
    imgs = [Image.fromarray((255*img).astype(np.uint8)) for img in dataset]
    # duration is the number of milliseconds between frames; this is 40 frames per second
    imgs[0].save(gif_name, save_all=True, append_images=imgs[1:], duration=duration, loop=1)


def add_lat_lon_to_gdf_from_geometry(gdf):
    gdf['Lat'] = gdf['geometry'].apply(lambda p: p.x)
    gdf['Lon'] = gdf['geometry'].apply(lambda p: p.y)
    return gdf

def gdf_column_to_one_band_array(gdf, column_name):
    gdf = gdf.sort_values(by=['Lat', 'Lon'])
    gdf = gdf.reset_index(drop=True)
    unique_lats_count = gdf['Lat'].nunique()
    unique_lons_count = gdf['Lon'].nunique()
    rows_arr = [[] for i in range(unique_lats_count)]
    column_values = gdf[column_name].values
    for i in tqdm(range(len(column_values))):
        row_index = i // unique_lons_count
        rows_arr[row_index].append(column_values[i])

    max_row_length = max([len(row) for row in rows_arr])
    for row in rows_arr:
        while len(row) < max_row_length:
            row.append(0)

    rows_arr = np.array(rows_arr)
    return rows_arr