import os
import main 
import utils
import streamlit as st
import geopandas as gpd
from datetime import datetime
from streamlit_folium import st_folium
import numpy as np



@st.cache_data()
def get_and_cache_available_dates(_df, field_id, year, start_date, end_date):
    dates = main.get_available_dates_for_field(_df, field_id, year, start_date, end_date)
    print(f'Caching Dates for {field_id}')
    return dates

def app():
    metric = 'TRUECOLOR'
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
            # Get the True Color image for the selected field and date
            img = main.get_True_color_data(src_df, f_id, date, client_name)
            
            # Show the image dimensions
            st.write(f'Image Dimensions: {img.shape}')

        # Process the image for display
        fixed_img = utils.fix_image(img)

        # Display the image
        caption = f'True Color Image (Processed) for selected field no#{f_id} in {date}'
        st.image(fixed_img, caption=caption, clamp=True)

        date_dir = f'./{client_name}/raw/{metric}/{date}/field_{f_id}/'
        donwnload_filename = f'{date_dir}{os.listdir(date_dir)[0]}/response.png'
        short_filename = f'{metric}_{date}_field_{f_id}.png'
        with open(donwnload_filename, 'rb') as f:
            st.download_button('Download as PNG File', f,file_name=donwnload_filename, mime='image/png', key=f'Download Button - {metric}')
        

    
    st.markdown('---')
    st.header('Show Historic Data (Time Series GIF)')

    # If a field is selected, display the field data
    if f_id != -1:

        # Let the user select the year, start date and end date
        with st.expander('Select Year, Start Date and End Date'):
            # Get the year
            years = [f'20{i}' for i in range(16, 23)]
            year = st.selectbox('Select Year: ', years, index=len(years)-2, key=f'Select Year Dropdown Menu - {metric} - Historic')
           
            # Set the min, max and default values for start and end dates
            min_val = f'{year}-01-01'
            max_val = f'{year}-12-31'
            default_val = f'{year}-07-01'
            min_val = datetime.strptime(min_val, '%Y-%m-%d')
            max_val = datetime.strptime(max_val, '%Y-%m-%d')
            default_val = datetime.strptime(default_val, '%Y-%m-%d')

            # Get the start and end dates
            start_date = st.date_input('Start Date', value=default_val, min_value=min_val, max_value=max_val, key=f'Start Date - {metric} - Historic')
            end_date = st.date_input('End Date', value=max_val, min_value=min_val, max_value=max_val, key=f'End Date - {metric} - Historic')

        
        # Get the dates for historic averages
        historic_avarages_dates_for_field = get_and_cache_available_dates(src_df, f_id, year, start_date, end_date)

        # Convert the dates to datetime objects and sort them ascendingly then convert them back to strings
        historic_avarages_dates_for_field = [datetime.strptime(date, '%Y-%m-%d') for date in historic_avarages_dates_for_field]
        historic_avarages_dates_for_field.sort()
        historic_avarages_dates_for_field = [datetime.strftime(date, '%Y-%m-%d') for date in historic_avarages_dates_for_field]


        # Let the user select Frame Duration 
        with st.expander('Select The Frame Duration (in Milliseconds)'):
            duration = st.slider('Frame Duration (in Milliseconds)', min_value=100, max_value=1000, value=500, step=100, key=f'Frame Duration Slider - {metric}')

        # Get the number of dates
        num_historic_dates = len(historic_avarages_dates_for_field)
        st.write(f' Found {num_historic_dates} dates for field {f_id} in {year} (from {start_date} to {end_date})')

        # Display the historic GIF when the user clicks the button
        display_historic_avgs_button = st.button(f'Display Historic GIF for Field {field_name} (Field ID: {f_id}) in {year} (from {start_date} to {end_date})',
                                                 key=f'Display Historic GIF Button - {metric}',
                                                 help='Click to display the historic GIF for the selected field',
                                                 use_container_width=True, type='primary')
        
        if display_historic_avgs_button:
            # Empty list to hold the images
            historic_true_color_images = []



            # Get the historic GIF
            dates_for_field_bar = st.progress(0)
            with st.spinner('Loading Historic GIF...'):
                with st.empty():
                    for i in range(num_historic_dates):
                        current_date = historic_avarages_dates_for_field[i]
                        img = main.get_True_color_data(src_df, f_id, current_date, client_name)
                        fixed_img = utils.fix_image(img)
                        historic_true_color_images.append(fixed_img)
                        dates_for_field_bar.progress((i + 1)/(num_historic_dates))
                        st.image(fixed_img, caption=f'True Color Image (Processed) for selected field no#{f_id} in {current_date}', clamp=True, use_column_width=True)
                    st.success('Done!')


            
            gifs_dir = f'./{client_name}/gifs/'
            os.makedirs(gifs_dir, exist_ok=True)
            gif_name = f'{metric}_{year}_field_{f_id}.gif'
            gif_path = gifs_dir + gif_name
            dataset = np.array(historic_true_color_images)
            utils.creat_gif(dataset, gif_path, duration=duration)
            st.success(f'GIF Created Successfully at {gif_path}')
            st.image(gif_path, caption=f'True Color Historic GIF for selected field no#{f_id} in {year}', use_column_width=True)


            import joblib
            joblib.dump(dataset, f'images_dataset.joblib')
            


        