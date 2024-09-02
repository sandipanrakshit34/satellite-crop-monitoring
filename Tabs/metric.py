import os
import main 
import utils
import joblib
import streamlit as st
import geopandas as gpd
from zipfile import ZipFile
from datetime import datetime
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from streamlit_folium import st_folium
from plotly.subplots import make_subplots

@st.cache_data()
def get_and_cache_available_dates(_df, field_id, year, start_date, end_date):
    dates = main.get_available_dates_for_field(_df, field_id, year, start_date, end_date)
    print(f'Caching Dates for {field_id}')
    return dates


def app(metric):
    f_id = -1
    st.title(f"{metric} Analysis")

    # Get the app config
    CONFIG = utils.parse_app_config()

    # Get the GeoJSON file for the client
    data_path = CONFIG['Client']['DataPath'].get()
    src_df = gpd.read_file(data_path)
    client_name = CONFIG['Client']['Name'].get()

    #Convert LastUpdated to string
    src_df['LastUpdate'] = src_df['LastUpdate'].astype(str)
    
    # Create a choropleth map of the client Fields
    m = src_df.explore(
        column="Crop_Type",
        tooltip=["Field_Id", "Crop_Type"],
        popup=True,
        style_kwds=dict(color="black", fillOpacity=0.1))
    
    # Add Google Satellite as a base map  
    google_map = utils.basemaps['Google Satellite']
    google_map.add_to(m)

    # Display the map inside an expander
    with st.expander("Show Client Fields"):
        st_folium(m, key=f'Client Fields - {metric}') 

    
    st.markdown('---')
    st.header('Select Field')

    # Initlize field_name as None
    field_name = 'None'

    # Set field_name as Crop_Type and field_id as Field_Id
    field_names = src_df.Crop_Type.tolist()

    # Add None to the end of the list to be used as a default value
    field_names.append('None')

    # Display the dropdown menu
    field_name = st.selectbox(
        "Check Field (or click on the map)",
        field_names, index=len(field_names)-1,
        key=f'Select Field Dropdown Menu - {metric}',
        )
    
    # If a field is selected, display the field name and get the field_id
    if field_name != 'None':
        f_id = src_df[src_df.Crop_Type == field_name].Field_Id.values[0]
        f_id = int(f_id)
        st.write(f'You selected {field_name} (Field ID: {f_id})')
    else:
        st.write('Please Select A Field')



    st.markdown('---')
    st.header('Select Observation Date')

    # Initlize date as -1 and dates as an empty list
    dates = []
    date = -1

    # If dates and date are not in session state, set them to the default values, else get them from the session state
    if 'dates' not in st.session_state:
        st.session_state['dates'] = dates
    else:
        dates = st.session_state['dates']
    if 'date' not in st.session_state:
        st.session_state['date'] = date
    else:
        date = st.session_state['date']

    # If a field is selected, Get the dates with available data for that field
    if f_id != -1 :

        # Give the user the option to select year, start date and end date
        with st.expander('Select Year, Start Date and End Date'):
            # Get the year
            years = [f'20{i}' for i in range(16, 23)]
            year = st.selectbox('Select Year: ', years, index=len(years)-2, key=f'Select Year Dropdown Menu - {metric}')
           
            # Set the min, max and default values for start and end dates
            min_val = f'{year}-01-01'
            max_val = f'{year}-12-31'
            default_val = f'{year}-07-01'
            min_val = datetime.strptime(min_val, '%Y-%m-%d')
            max_val = datetime.strptime(max_val, '%Y-%m-%d')
            default_val = datetime.strptime(default_val, '%Y-%m-%d')

            # Get the start and end dates
            start_date = st.date_input('Start Date', value=default_val, min_value=min_val, max_value=max_val, key=f'Start Date - {metric}')
            end_date = st.date_input('End Date', value=max_val, min_value=min_val, max_value=max_val, key=f'End Date - {metric}')


        # Get the dates with available data for that field when the user clicks the button
        get_dates_button = st.button(f'Get Dates for Field {field_name} (Field ID: {f_id}) in {year} (from {start_date} to {end_date})',
                                     key=f'Get Dates Button - {metric}',
                                     help='Click to get the dates with available data for the selected field',
                                     use_container_width=True, type='primary')
        if get_dates_button:
            dates = get_and_cache_available_dates(src_df, f_id, year, start_date, end_date)
            # Add None to the end of the list to be used as a default value
            dates.append(-1)
            #Add the dates to the session state
            st.session_state['dates'] = dates

        # Display the dropdown menu
        if len(dates) > 0:
            date = st.selectbox('Select Observation Date: ', dates, index=len(dates)-1, key=f'Select Date Dropdown Menu - {metric}')
            if date != -1:
                st.write('You selected:', date)
                #Add the date to the session state
                st.session_state['date'] = date
            else:
                st.write('Please Select A Date')
        else:
            st.info('No dates available for the selected field and dates range, select a different range or click the button to fetch the dates again')

    else:
        st.info('Please Select A Field')

    st.markdown('---')
    st.header('Show Field Data')

    # If a field and a date are selected, display the field data
    if (date != -1) and (f_id != -1):   

        # Get the field data at the selected date
        with st.spinner('Loading Field Data...'):
            # Get the metric data and cloud cover data for the selected field and date
            metric_data = main.get_cuarted_df_for_field(src_df, f_id, date, metric, client_name)
            cloud_cover_data = main.get_cuarted_df_for_field(src_df, f_id, date, 'CLP', client_name)
            
            #Merge the metric and cloud cover data on the geometry column
            field_data = metric_data.merge(cloud_cover_data, on='geometry')

        # Display the field data
        st.write(f'Field Data for {field_name} (Field ID: {f_id}) on {date}')
        st.write(field_data.head(2))

        #Get Avarage Cloud Cover
        avg_clp = field_data[f'CLP_{date}'].mean() *100

        # If the avarage cloud cover is greater than 80%, display a warning message
        if avg_clp > 80:
            st.warning(f'⚠️ The Avarage Cloud Cover is {avg_clp}%')
            st.info('Please Select A Different Date')

        ## Generate the field data Map ##

        #Title, Colormap and Legend
        title = f'{metric} for selected field {field_name} (Field ID: {f_id}) in {date}'
        cmap = 'RdYlGn'

        # Create a map of the field data
        field_data_map  = field_data.explore(
            column=f'{metric}_{date}',
            cmap=cmap,
            legend=True,
            vmin=0,
            vmax=1,
            marker_type='circle', marker_kwds={'radius':5.3, 'fill':True})
        
        # Add Google Satellite as a base map
        google_map = utils.basemaps['Google Satellite']
        google_map.add_to(field_data_map)

        # Display the map
        st_folium(field_data_map, width = 725, key=f'Field Data Map - {metric}')


        #Dwonload Links

        # If the field data is not empty, display the download links
        if len(field_data) > 0:
            # Create two columns for the download links
            download_as_shp_col, download_as_tiff_col = st.columns(2)

            # Create a shapefile of the field data and add a download link
            with download_as_shp_col:

                #Set the shapefile name and path based on the field id, metric and date
                extension = 'shp'
                shapefilename = f"{f_id}_{metric}_{date}.{extension}"
                path = f'./shapefiles/{f_id}/{metric}/{extension}'

                # Create the target directory if it doesn't exist
                os.makedirs(path, exist_ok=True)
                
                # Save the field data as a shapefile
                field_data.to_file(f'{path}/{shapefilename}')

                # Create a zip file of the shapefile
                files = []
                for i in os.listdir(path):
                    if os.path.isfile(os.path.join(path,i)):
                        if i[0:len(shapefilename)] == shapefilename:
                            files.append(os.path.join(path,i))
                zipFileName = f'{path}/{f_id}_{metric}_{date}.zip'
                zipObj = ZipFile(zipFileName, 'w')
                for file in files:
                    zipObj.write(file)
                zipObj.close()

                # Add a download link for the zip file
                with open(zipFileName, 'rb') as f:
                    st.download_button('Download as ShapeFile', f,file_name=zipFileName)

            # Get the tiff file path and create a download link
            with download_as_tiff_col:
                #get the tiff file path
                tiff_path = utils.get_masked_location_img_path(client_name, metric, date, f_id)
                # Add a download link for the tiff file
                donwnload_filename = f'{metric}_{f_id}_{date}.tiff'
                with open(tiff_path, 'rb') as f:
                    st.download_button('Download as Tiff File', f,file_name=donwnload_filename)

    else:
        st.info('Please Select A Field and A Date')
    

    st.markdown('---')
    st.header('Show Historic Averages')

    # If a field is selected, display the historic averages
    if f_id != -1:

        #Let the user select the year, start date and end date
        with st.expander('Select Year, Start Date and End Date'):
            # Get the year
            years = [f'20{i}' for i in range(16, 23)]
            year = st.selectbox('Select Year: ', years, index=len(years)-2, key=f'Select Year Dropdown Menu - {metric}- Historic Averages')
           
            # Set the start and end dates to the first and last dates of the year
            start_date = f'{year}-01-01'
            end_date = f'{year}-12-31'

        # Get the dates for historic averages
        historic_avarages_dates_for_field = get_and_cache_available_dates(src_df, f_id, year, start_date, end_date)

        # Convert the dates to datetime objects and sort them ascendingly then convert them back to strings
        historic_avarages_dates_for_field = [datetime.strptime(date, '%Y-%m-%d') for date in historic_avarages_dates_for_field]
        historic_avarages_dates_for_field.sort()
        historic_avarages_dates_for_field = [datetime.strftime(date, '%Y-%m-%d') for date in historic_avarages_dates_for_field]

        # Get the number of dates
        num_historic_dates = len(historic_avarages_dates_for_field)
        st.write(f' Found {num_historic_dates} dates for field {f_id} in {year} (from {start_date} to {end_date})')

        # Display the historic averages when the user clicks the button
        display_historic_avgs_button = st.button(f'Display Historic Averages for Field {field_name} (Field ID: {f_id}) in {year} (from {start_date} to {end_date})',
                                                 key=f'Display Historic Averages Button - {metric}',
                                                 help='Click to display the historic averages for the selected field',
                                                 use_container_width=True, type='primary')
        
        # If the button is clicked, display the historic averages
        if display_historic_avgs_button:

            #Initlize the historic averages cache dir and file path
            historic_avarages_cache_dir = './historic_avarages_cache'
            historic_avarages_cache_path = f'{historic_avarages_cache_dir}/historic_avarages_cache.joblib'
            historic_avarages_cache_clp_path = f'{historic_avarages_cache_dir}/historic_avarages_cache_clp.joblib'

            # Load the historic averages cache if it exists, else create it
            if os.path.exists(historic_avarages_cache_path):
                historic_avarages_cache = joblib.load(historic_avarages_cache_path)
            else:
                os.makedirs(historic_avarages_cache_dir, exist_ok=True)
                joblib.dump({}, historic_avarages_cache_path)
                historic_avarages_cache = joblib.load(historic_avarages_cache_path)
            if os.path.exists(historic_avarages_cache_clp_path):
                historic_avarages_cache_clp = joblib.load(historic_avarages_cache_clp_path)
            else:
                os.makedirs(historic_avarages_cache_dir, exist_ok=True)
                joblib.dump({}, historic_avarages_cache_clp_path)
                historic_avarages_cache_clp = joblib.load(historic_avarages_cache_clp_path)

            #Check if the field and year are in the cache for the current metric and client
            client_name = CONFIG['Client']['Name'].get()
            found_in_cache = False
            if client_name not in historic_avarages_cache:
                historic_avarages_cache[client_name] = {}
            if metric not in historic_avarages_cache[client_name]:
                historic_avarages_cache[client_name][metric] = {}
            if f_id not in historic_avarages_cache[client_name][metric]:
                historic_avarages_cache[client_name][metric][f_id] = {}
            if year not in historic_avarages_cache[client_name][metric][f_id]:
                historic_avarages_cache[client_name][metric][f_id][year] = {}
            if len(historic_avarages_cache[client_name][metric][f_id][year]) > 0:
                found_in_cache = True


            #Check if the field and year are in the cache_clp for the current metric and client
            found_in_cache_clp = False
            if client_name not in historic_avarages_cache_clp:
                historic_avarages_cache_clp[client_name] = {}
            if 'CLP' not in historic_avarages_cache_clp[client_name]:
                historic_avarages_cache_clp[client_name]['CLP'] = {}
            if f_id not in historic_avarages_cache_clp[client_name]['CLP']:
                historic_avarages_cache_clp[client_name]['CLP'][f_id] = {}
            if year not in historic_avarages_cache_clp[client_name]['CLP'][f_id]:
                historic_avarages_cache_clp[client_name]['CLP'][f_id][year] = {}
            if len(historic_avarages_cache_clp[client_name]['CLP'][f_id][year]) > 0:
                found_in_cache_clp = True


            # If Found in cache, get the historic averages from the cache
            if found_in_cache and found_in_cache_clp:
                st.info('Found Historic Averages in Cache')
                historic_avarages = historic_avarages_cache[client_name][metric][f_id][year]['historic_avarages']
                historic_avarages_dates = historic_avarages_cache[client_name][metric][f_id][year]['historic_avarages_dates']
                historic_avarages_clp = historic_avarages_cache_clp[client_name]['CLP'][f_id][year]['historic_avarages_clp']

            # Else, calculate the historic averages and add them to the cache
            else:
                st.info('Calculating Historic Averages...')


                #Empty lists for the historic averages , dates and cloud cover
                historic_avarages = []
                historic_avarages_dates = []
                historic_avarages_clp = []

                # Get the historic averages
                dates_for_field_bar = st.progress(0)
                with st.spinner('Calculating Historic Averages...'):
                    with st.empty():
                        for i in range(num_historic_dates):
                            # Get the historic average for the current date
                            current_date = historic_avarages_dates_for_field[i]
                            current_df = main.get_cuarted_df_for_field(src_df, f_id, current_date, metric, client_name)
                            current_df_clp = main.get_cuarted_df_for_field(src_df, f_id, current_date, 'CLP', client_name)
                            current_avg = current_df[f'{metric}_{current_date}'].mean()
                            current_avg_clp = current_df_clp[f'CLP_{current_date}'].mean()
                            # Add the historic average and date to the lists
                            historic_avarages.append(current_avg)
                            historic_avarages_dates.append(current_date)
                            historic_avarages_clp.append(current_avg_clp)
                            # Update the progress bar
                            dates_for_field_bar.progress((i + 1)/(num_historic_dates))

                            # Create a plot of the historic averages with the cloud cover as dashed line and dates as x axis (rotated 90 degrees when needed)
                            fig, ax = plt.subplots(figsize=(10, 5))

                            # Set the x axis ticks and labels
                            x = historic_avarages_dates
                            x_ticks = [i for i in range(len(x))]
                            ax.set_xticks(x_ticks)
                            
                            #Set rotation to 90 degrees if the number of dates is greater than 10
                            rot = 0 if len(x) < 10 else 90
                            ax.set_xticklabels(x, rotation=rot)

                            # Set the y axis ticks and labels
                            y1 = historic_avarages
                            y2 = historic_avarages_clp
                            y_ticks = [i/10 for i in range(11)]
                            ax.set_yticks(y_ticks)
                            ax.set_yticklabels(y_ticks)

                            # Plot the historic averages and cloud cover
                            ax.plot(x_ticks, y1, label=f'{metric} Historic Averages')
                            ax.plot(x_ticks, y2, '--', label='Cloud Cover')
                            ax.legend()

                            # Set the title and axis labels
                            ax.set_title(f'{metric} Historic Averages for {field_name} (Field ID: {f_id}) in {year}')
                            ax.set_xlabel('Date')
                            ax.set_ylabel(f'{metric} Historic Averages')

                            # Display the plot
                            st.pyplot(fig)

                # Add the historic averages to the cache
                historic_avarages_cache[client_name][metric][f_id][year]['historic_avarages'] = historic_avarages
                historic_avarages_cache[client_name][metric][f_id][year]['historic_avarages_dates'] = historic_avarages_dates
                historic_avarages_cache_clp[client_name]['CLP'][f_id][year]['historic_avarages_clp'] = historic_avarages_clp
                # Save the cache
                joblib.dump(historic_avarages_cache, historic_avarages_cache_path)
                joblib.dump(historic_avarages_cache_clp, historic_avarages_cache_clp_path)
                # Tell the user that the historic averages are saved in the cache
                st.info('Historic Averages Saved in Cache')
                st.write(f'Cache Path: {historic_avarages_cache_path}')
                st.write(f'Cache CLP Path: {historic_avarages_cache_clp_path}')


            # Display the historic averages in nice plotly plot
            fig = make_subplots(specs=[[{"secondary_y": True}]])

            # Add the historic averages to the plot
            fig.add_trace(
                go.Scatter(x=historic_avarages_dates, y=historic_avarages, name=f'{metric} Historic Averages'),
                secondary_y=False,
            )

            # Add the cloud cover to the plot
            fig.add_trace(
                go.Scatter(x=historic_avarages_dates, y=historic_avarages_clp, name='Cloud Cover'),
                secondary_y=True,
            )

            # Set the title and axis labels
            fig.update_layout(title_text=f'{metric} Historic Averages for {field_name} (Field ID: {f_id}) in {year}')
            fig.update_xaxes(title_text='Date')
            fig.update_yaxes(title_text=f'{metric} Historic Averages', secondary_y=False)
            fig.update_yaxes(title_text='Cloud Cover', secondary_y=True)

            # Display the plot
            st.plotly_chart(fig)            
    else:
        st.info('Please Select A Field')
        

    st.markdown('---')
    st.header('Show Historic GIF')

    # If a field is selected, display the historic GIF of the field (as 1D images)
    if f_id != -1:

        #Let the user select the year, start date and end date of the GIF
        with st.expander('Select Year, Start Date and End Date of the GIF'):
            # Get the year
            years = [f'20{i}' for i in range(16, 23)]
            year = st.selectbox('Select Year: ', years, index=len(years)-2, key=f'Select Year Dropdown Menu - {metric}- Historic Averages GIF')
           
            # Set the start and end dates to the first and last dates of the year
            start_date = f'{year}-01-01'
            end_date = f'{year}-12-31'

        # Get the dates for historic GIF
        historic_avarages_dates_for_field = get_and_cache_available_dates(src_df, f_id, year, start_date, end_date)

        # Convert the dates to datetime objects and sort them ascendingly then convert them back to strings
        historic_avarages_dates_for_field = [datetime.strptime(date, '%Y-%m-%d') for date in historic_avarages_dates_for_field]
        historic_avarages_dates_for_field.sort()
        historic_avarages_dates_for_field = [datetime.strftime(date, '%Y-%m-%d') for date in historic_avarages_dates_for_field]

        # Get the number of dates
        num_historic_dates = len(historic_avarages_dates_for_field)
        st.write(f' Found {num_historic_dates} dates for field {f_id} in {year} (from {start_date} to {end_date})')

        # Display the historic GIF when the user clicks the button
        display_historic_GIF_button = st.button(f'Display Historic GIF  for Field {field_name} (Field ID: {f_id}) in {year} (from {start_date} to {end_date})',
                                                 key=f'Display Historic GIF Button - {metric}',
                                                 help='Click to display the historic GIF for the selected field',
                                                 use_container_width=True, type='primary')
        
        # If the button is clicked, display the historic GIF
        if display_historic_GIF_button:

            #Initlize the historic GIF imgs and dates
            st.info('Generating Historic GIF...')
            historic_imgs = []
            historic_imgs_dates = []

            # Gen the historic GIF
            dates_for_field_bar = st.progress(0)
            with st.spinner('Generating Historic GIF...'):
                with st.empty():
                    for i in range(num_historic_dates):
                        current_date = historic_avarages_dates_for_field[i]
                        current_df = main.get_cuarted_df_for_field(src_df, f_id, current_date, metric, client_name)
                        historic_imgs.append(current_df)
                        historic_imgs_dates.append(current_date)
                        dates_for_field_bar.progress((i + 1)/(num_historic_dates))

                        # Create a fig of the historic Img 
                        fig, ax = plt.subplots(figsize=(10, 5))

                        # Get the current img
                        current_df_lat_lon = utils.add_lat_lon_to_gdf_from_geometry(current_df)
                        current_img = utils.gdf_column_to_one_band_array(current_df_lat_lon, f'{metric}_{current_date}')

                        # Plot the historic Img
                        title = f'{metric} for selected field {field_name} (Field ID: {f_id}) in {current_date}'
                        ax.imshow(current_img)
                        ax.set_title(title)

                        # Display the plot
                        st.pyplot(fig)

            # Create the historic GIF
            historic_GIF_name = f'{metric}_{f_id}_{year}.gif'
            st.write('Creating Historic GIF...', historic_GIF_name)
       
    else:
        st.info('Please Select A Field')
        