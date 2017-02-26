#!/usr/bin/env python3
from ansicolor import blue, red, black
from Download import download_if_not_exists

urlprefix = "http://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/"
    
def download_all():
    download_if_not_exists("ne_10m_admin_0_map_units.zip",
        urlprefix + "ne_10m_admin_0_map_units.zip")
    download_if_not_exists("ne_10m_admin_1_states_provinces.zip",
        urlprefix + "ne_10m_admin_1_states_provinces.zip")
    download_if_not_exists("ne_10m_populated_places.zip",
        urlprefix + "ne_10m_populated_places.zip")

if __name__ == "__main__":
    # Download natural earth data if not present
    download_all()