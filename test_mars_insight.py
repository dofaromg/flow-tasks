#!/usr/bin/env python3
"""
Test for Mars InSight snapshot JSON file
Validates the structure and content of the Mars InSight coordinate snapshot
"""

import json
import os
import pytest
from pathlib import Path

# Constants
MARS_INSIGHT_FILE = Path("particle_core/examples/Mars.InSight.20250813.json")
COORDINATE_TOLERANCE = 0.1  # degrees


@pytest.fixture
def mars_insight_data():
    """Fixture to load Mars InSight JSON data"""
    with open(MARS_INSIGHT_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_mars_insight_json_exists():
    """Test that the Mars InSight JSON file exists"""
    assert MARS_INSIGHT_FILE.exists(), f"Mars InSight JSON file not found: {MARS_INSIGHT_FILE}"


def test_mars_insight_json_valid():
    """Test that the Mars InSight JSON file is valid JSON"""
    with open(MARS_INSIGHT_FILE, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in Mars InSight file: {e}")


def test_mars_insight_json_structure(mars_insight_data):
    """Test that the Mars InSight JSON has the required structure"""
    data = mars_insight_data
    
    # Check required top-level fields
    required_fields = ['id', 'body', 'coords', 'time', 'links']
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
    
    # Check id format
    assert data['id'] == "Mars.InSight.20250813", f"Unexpected id: {data['id']}"
    
    # Check body
    assert data['body'] == "Mars", f"Unexpected body: {data['body']}"
    
    # Check coords structure
    assert 'coords' in data, "Missing coords field"
    assert 'lon' in data['coords'], "Missing longitude in coords"
    assert 'lat' in data['coords'], "Missing latitude in coords"
    
    # Validate coordinate values (Mars InSight landing site coordinates)
    lon = data['coords']['lon']
    lat = data['coords']['lat']
    assert isinstance(lon, (int, float)), "Longitude must be a number"
    assert isinstance(lat, (int, float)), "Latitude must be a number"
    assert -180 <= lon <= 180, f"Longitude out of range: {lon}"
    assert -90 <= lat <= 90, f"Latitude out of range: {lat}"
    
    # Check time format (ISO 8601)
    assert 'time' in data, "Missing time field"
    assert data['time'].endswith('Z'), "Time should be in UTC (ending with Z)"
    
    # Check links structure
    assert 'links' in data, "Missing links field"
    assert isinstance(data['links'], dict), "Links should be a dictionary"
    
    # Check expected link fields
    expected_links = ['snapshot', 'kmz', 'google_earth', 'image']
    for link_field in expected_links:
        assert link_field in data['links'], f"Missing link field: {link_field}"


def test_mars_insight_coordinates(mars_insight_data):
    """Test that the Mars InSight coordinates are reasonable"""
    data = mars_insight_data
    
    # Mars InSight landed at approximately 4.5°N, 135.9°E
    # These are the expected coordinates from the NASA mission
    expected_lat = 4.5
    expected_lon = 135.9
    
    actual_lat = data['coords']['lat']
    actual_lon = data['coords']['lon']
    
    # Allow for minor variations
    assert abs(actual_lat - expected_lat) < COORDINATE_TOLERANCE, \
        f"Latitude mismatch: expected ~{expected_lat}, got {actual_lat}"
    assert abs(actual_lon - expected_lon) < COORDINATE_TOLERANCE, \
        f"Longitude mismatch: expected ~{expected_lon}, got {actual_lon}"


def test_mars_insight_google_earth_link(mars_insight_data):
    """Test that the Google Earth link is properly formatted"""
    data = mars_insight_data
    google_earth_link = data['links']['google_earth']
    
    # Check that it's a valid URL
    assert google_earth_link.startswith('https://earth.google.com/web/'), \
        f"Invalid Google Earth link format: {google_earth_link}"
    
    # Extract coordinates from the data and verify they appear in the URL
    lat = data['coords']['lat']
    lon = data['coords']['lon']
    
    # Check that the URL contains coordinate values (as strings)
    lat_str = str(lat)
    lon_str = str(lon)
    assert lat_str in google_earth_link, \
        f"Google Earth link should contain latitude {lat_str}"
    assert lon_str in google_earth_link, \
        f"Google Earth link should contain longitude {lon_str}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
