# satellite-crop-monitoring
---
<center> <img src = "https://github.com/sandipanrakshit34/satellite-crop-monitoring/blob/main/banner.png" width = 100%>
  
title: Agricultural Remote Sensing Monitoring
emoji: 🌱
colorFrom: green
colorTo: blue
sdk: streamlit
sdk_version: 1.21.0
app_file: app.py
pinned: false
license: openrail
---

# Agricultural Remote Sensing Monitoring

This project provides a dashboard for monitoring crops via remote sensing data. It allows farmers to view vegetation metrics for their fields over time to track crop health and growth.

## Features

- Home page shows a list of all your fields
- View vegetation indices (LAI, CAB, NDVI) for each field
- Select a specific field and date to view index maps 
- Time series charts track field metrics over the season
- True color imagery lets you visualize field changes  
- Create animated gifs from imagery to see growth stages
- Add new fields by drawing boundaries on the map
- Store crop type and season for each field

## Getting Started

The dashboard is built with Streamlit and uses satellite imagery from [source].

To run locally:

```
git clone https://github.com/sandipan34/crop-monitoring
cd crop-monitoring
pip install -r requirements.txt 
streamlit run app.py
```


## Usage

The home page shows a map of your fields and a list. Choose a field to start exploring metrics and imagery.

Use the date picker to view index maps and true color images for any date. 

Charts show the full time series for the season. Toggle metrics in the sidebar. 

To add a new field, go to the Add Field page. Draw a polygon for the field boundary. Enter crop details like corn, wheat, lettuce etc.

## Future Work

Potential features to add:

- Analysis tools for comparing fields 
- Predictive crop yield models
- Integrate weather data
- Field monitoring alerts


## Author

- [@sandipanrakshit34](https://github.com/sandipanrakshit34)

##


