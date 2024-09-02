import utils
import streamlit as st
import geopandas as gpd
from streamlit_folium import st_folium

def app():
    # Welcome message and Intro
    st.title("Crop Monitoring - Home")
    st.header("Welcome to the Crop Health Dashboard")
    st.write("This dashboard is designed to help you monitor the health of your crops. Use the tabs above to navigate to the different sections of the dashboard.")

    # Get the app config 
    CONFIG = utils.parse_app_config()

    # Get the GeoJSON file for the client
    data_path = CONFIG['Client']['DataPath'].get()
    gdf = gpd.read_file(data_path)

    # Expander to show the GeoJSON file
    client_name = CONFIG['Client']['Name'].get()
    with st.expander(f"Show {client_name} GeoJSON"):
        st.write(gdf)

    #Convert LastUpdated to string
    gdf['LastUpdate'] = gdf['LastUpdate'].astype(str)

    # Creata a map of the client Fields
    m = gdf.explore(
        column="Crop_Type",
        tooltip=["Field_Id", "Crop_Type"],
        popup=True,
        style_kwds=dict(color="black", fillOpacity=0.1))

    # Add Google Satellite as a base map  
    google_map = utils.basemaps['Google Satellite']
    google_map.add_to(m)

    # Display the map inside an expander
    with st.expander("Show Client Fields"):
        st_folium(m)  


    # Clear all cached data
    if st.button("Clear All Cached Data", key="clear_all_cached_data"):
        st.cache_resource.clear()
        st.cache_data.clear()
    
        
        
    
  