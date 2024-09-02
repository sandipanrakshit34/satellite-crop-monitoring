import folium
import streamlit as st
from folium.plugins import Draw
from streamlit_folium import st_folium
import utils
import geopandas as gpd
import pandas as pd
import json
import os
import datetime




def app():
    st.markdown('### Commit Changes from Add Box')

    # Get the app config
    CONFIG = utils.parse_app_config()

    # Get the GeoJSON file for the client
    data_path = CONFIG['Client']['DataPath'].get()
    src_df = gpd.read_file(data_path)

    #Get pre commit GeoJSON
    pre_commit_path = data_path.split('.')[0] + '_pre_commit.geojson'
    if os.path.exists(pre_commit_path):
        pre_commit_df = gpd.read_file(pre_commit_path)

        #Convert LastUpdated to string
        src_df['LastUpdate'] = src_df['LastUpdate'].astype(str)
        pre_commit_df['LastUpdate'] = pre_commit_df['LastUpdate'].astype(str)


        #Compare the two GeoJSON files

        st.markdown('### Original Data')
        st.write(src_df)
        st_folium(src_df.explore(), width=700, height=500)

        st.markdown('### After Commit Data')
        st.write(pre_commit_df)
        st_folium(pre_commit_df.explore(), width=700, height=500)


        #add accept and reject buttons
        accept_col, reject_col = st.columns(2)

        with accept_col:
            accept_bt = st.button('Accept Changes', key='accept_changes', type='primary', use_container_width=True)
            if accept_bt:
                #Convert LastUpdated to datetime
                src_df['LastUpdate'] = pd.to_datetime(src_df['LastUpdate'])
                pre_commit_df['LastUpdate'] = pd.to_datetime(pre_commit_df['LastUpdate'])

                #Set Crs to EPSG:4326
                src_df.crs = 'EPSG:4326'
                pre_commit_df.crs = 'EPSG:4326'

                #archive the old data
                archive_path = data_path.split('.')[0] + f'_archive_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.geojson'
                src_df.to_file(archive_path, driver='GeoJSON')

                #save the new data
                pre_commit_df.to_file(data_path, driver='GeoJSON')

                #remove the pre commit data
                os.remove(pre_commit_path)

                #Celebrate
                st.balloons()

        with reject_col:
            reject_bt = st.button('Reject Changes', key='reject_changes', type='primary', use_container_width=True)
            if reject_bt:
                #remove the pre commit data
                os.remove(pre_commit_path)

                #Inform 
                st.error('Changes Rejected')

    else:
        st.error('No Pre Commit Data Found')

