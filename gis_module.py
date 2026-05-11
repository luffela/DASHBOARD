import pandas as pd
import folium
from folium.plugins import HeatMap

# =====================================================
# LOAD CSV FILE
# =====================================================

df = pd.read_csv("road_data.csv")

# Remove rows with missing coordinates
df = df.dropna(subset=['Latitude', 'Longitude'])

# =====================================================
# CREATE BASE MAP
# =====================================================

gis_map = folium.Map(
    location=[8.4700, 124.6450],
    zoom_start=13,
    tiles="OpenStreetMap"
)

# =====================================================
# ADD ROAD MARKERS
# =====================================================

for index, row in df.iterrows():

    # COLOR BASED ON ESAL
    if row['ESAL'] < 1:
        color = "green"

    elif row['ESAL'] < 3:
        color = "orange"

    else:
        color = "red"

    # POPUP DETAILS
    popup_text = f"""
    <b>Road ID:</b> {row['Road_ID']}<br>
    <b>Road Name:</b> {row['Road_Name']}<br>
    <b>Vehicle Count:</b> {row['Vehicle_Count']}<br>
    <b>ESAL:</b> {row['ESAL']}<br>
    <b>Pavement Thickness:</b> {row['Pavement_Thickness']} mm
    """

    # CREATE MARKER
    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=10,
        popup=popup_text,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7
    ).add_to(gis_map)

# =====================================================
# CREATE HEATMAP
# =====================================================

heat_data = []

for index, row in df.iterrows():

    heat_data.append([
        row['Latitude'],
        row['Longitude'],
        row['Vehicle_Count']
    ])

HeatMap(heat_data).add_to(gis_map)

# =====================================================
# SAVE MAP
# =====================================================

gis_map.save("pavetrack_map.html")

print("GIS MAP CREATED SUCCESSFULLY!")