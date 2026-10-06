import numpy as np
import pandas as pd
import folium
from folium.plugins import HeatMap
from scipy.interpolate import griddata
from datetime import datetime, timezone
from config import SENSOR_NODES
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpatialAQIMapper:
    """Generate hyperlocal AQI maps"""
    
    def __init__(self):
        self.sensor_nodes = SENSOR_NODES
    
    def create_folium_heatmap(self, aqi_data, output_file='static/heatmap.html'):
        """Create interactive heatmap"""
        if len(aqi_data) == 0:
            logger.error("No data for heatmap")
            return None
        
        center_lat = aqi_data['lat'].mean()
        center_lon = aqi_data['lon'].mean()
        
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=15,
            tiles='OpenStreetMap'
        )
        
        # Prepare heat data
        heat_data = [
            [row['lat'], row['lon'], row['aqi']]
            for _, row in aqi_data.iterrows()
        ]
        
        # Add heatmap layer
        HeatMap(
            heat_data,
            name='AQI Heatmap',
            radius=25,
            blur=20,
            max_zoom=15,
            gradient={
                0.0: '#00C853',
                0.25: '#FBC02D',
                0.5: '#F57C00',
                0.75: '#D32F2F',
                1.0: '#4A148C'
            }
        ).add_to(m)
        
        # Add markers
        for _, row in aqi_data.iterrows():
            aqi_val = row['aqi']
            if aqi_val <= 50:
                color = 'green'
            elif aqi_val <= 100:
                color = 'yellow'
            elif aqi_val <= 200:
                color = 'orange'
            elif aqi_val <= 300:
                color = 'red'
            else:
                color = 'purple'
            
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=15,
                popup=f"{row['name']}<br>AQI: {row['aqi']:.0f}",
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.8
            ).add_to(m)
        
        folium.LayerControl().add_to(m)
        
        try:
            m.save(output_file)
            logger.info(f"✓ Heatmap saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving heatmap: {e}")
        
        return m


if __name__ == "__main__":
    mapper = SpatialAQIMapper()
    
    # Test data
    aqi_data = pd.DataFrame([
        {'lat': 26.8467, 'lon': 80.9462, 'aqi': 75, 'name': 'School Gate'},
        {'lat': 26.8468, 'lon': 80.9463, 'aqi': 65, 'name': 'Playground'},
        {'lat': 26.8469, 'lon': 80.9464, 'aqi': 80, 'name': 'Campus Center'},
    ])
    
    mapper.create_folium_heatmap(aqi_data)
    print("✓ Heatmap created")