#!/usr/bin/env python3
from ansicolor import blue, red, black
from .Download import download_if_not_exists
from .NaturalEarth import *
from .ShapefileRecords import *
from .MapRenderer import *
import sys

urlprefix = "http://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/"

def download_all():
    print(blue("Downloading Natural Earth files...", bold=True))
    download_if_not_exists("ne_10m_admin_0_map_units.zip",
        urlprefix + "ne_10m_admin_0_map_units.zip")
    download_if_not_exists("ne_10m_admin_1_states_provinces.zip",
        urlprefix + "ne_10m_admin_1_states_provinces.zip")
    download_if_not_exists("ne_10m_populated_places.zip",
        urlprefix + "ne_10m_populated_places.zip")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('country', nargs='*', help='The countries to render')
    parser.add_argument('-a', '--all', action="store_true", help='Render all countries')
    args = parser.parse_args()
    # Download natural earth data if not present
    download_all()

    if not args.all and not args.country:
        print("Use either --all or specify at least one country")
        parser.print_help()
        sys.exit(1)
    # Map
    countries = RecordSet(read_naturalearth_zip("ne_10m_admin_0_map_units.zip"))
    states = RecordSet(read_naturalearth_zip("ne_10m_admin_1_states_provinces.zip"))

    render_all_countries(countries, "output/SVG")
