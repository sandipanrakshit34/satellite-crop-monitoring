import folium
import streamlit as st
from folium.plugins import Draw
from streamlit_folium import st_folium
import utils
import geopandas as gpd
import pandas as pd
import json
import datetime


def app():
    st.markdown('### Add Polygons to the Map')

    # Get the app config
    CONFIG = utils.parse_app_config()

    # Get the GeoJSON file for the client
    data_path = CONFIG['Client']['DataPath'].get()
    src_df = gpd.read_file(data_path)

    #Warn the user to refresh the page if the map is not visible
    st.warning('If The Map is not visible, please refresh the page')
     
    # Show the map to the user and let them draw on it
    m = folium.Map(location=[14.408939060626585, 33.25127862142054], zoom_start=10)
    utils.basemaps['Google Satellite'].add_to(m)
    Draw(export=True).add_to(m)

    with st.expander('Show Map'):
        output = st_folium(m, width=700, height=500)


    # Get the drawn shapes from the map
    gdfs = []
    if output['all_drawings'] is not None:
        for drawing in output['all_drawings']:
            # write drawing dict to geojson file (temporary) in a formated way
            with open('./temp.geojson', 'w') as f:
                json.dump(drawing, f, indent=4)
            # read geojson file to geodataframe
            gdf = gpd.read_file('./temp.geojson')
            gdf.crs = 'EPSG:4326'
            gdfs.append(gdf)


    # If the user has drawn something, show the geodataframe
    if len(gdfs) > 0:
        all_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))
        all_gdf.crs = 'EPSG:4326'

        #Add Crop and Season Column
        all_gdf['Crop_Type'] = ''
        all_gdf['Season'] = ''

        #Get user input for Crop and Season
        crop_col, season_col = st.columns(2)

        #Add Crop and Season to the dataframe
        with crop_col:
            for i in range(len(all_gdf)):
                with st.expander(f'Add Crop for drawing {i}'):
                    all_gdf['Crop_Type'][i] = st.text_input(f'Crop for drawing {i}', key=f'crop_{i}')
        with season_col:
            for i in range(len(all_gdf)):
                with st.expander(f'Add Season for drawing {i}'):
                    all_gdf['Season'][i] = st.text_input(f'Season for drawing {i}', key=f'season_{i}')

        #Add Last Update Column
        # if 'LastUpdate' not in all_gdf.columns:
        #     all_gdf['LastUpdate'] = datetime.datetime.now()

        #Compare with the source dataframe and add the new fields
        with_src_col, without_src_col = st.columns(2)


        #Convert LastUpdate to string in both dataframes
        src_df['LastUpdate'] = src_df['LastUpdate'].astype(str)

        #Add the new fields to the source dataframe
        with with_src_col:
            src_df = pd.concat([src_df, all_gdf], ignore_index=True)
            src_df = gpd.GeoDataFrame(src_df)
            src_df.crs = 'EPSG:4326'
            st.write(src_df)
            m_with_src = src_df.explore(column = 'Crop_Type')
            st_folium(m_with_src)


        #Add Button to update the source dataframe
        if st.button('Update Source Dataframe'):

            #get the max field id in the source dataframe
            max_field_id = int(src_df['Field_Id'].max())

            #Fill each of the NaN values in Field_Id with a new value (max_field_id + 1, max_field_id + 2, ...)
            src_df['Field_Id'] = src_df['Field_Id'].fillna(pd.Series(range(max_field_id + 1, max_field_id + 1 + len(src_df))))

            # Get the current date and time
            now = datetime.datetime.now()
            now = now.strftime("%Y-%m-%d %H:%M:%S")

            #Fill each of the NaN values in LastUpdate with the current date and time
            src_df['LastUpdate'] = src_df['LastUpdate'].fillna(now)

            #Save the source dataframe
            pre_commit_path = data_path.split('.')[0] + '_pre_commit.geojson'

            #Save the source dataframe to a geojson file
            src_df.to_file(pre_commit_path, driver='GeoJSON')

            st.success('Source Dataframe Saved Successfully in {}'.format(pre_commit_path))

            st.info('Please commit the changes by going the commit tab and clicking on the commit button')


            


    