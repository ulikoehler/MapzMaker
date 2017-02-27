#!/usr/bin/env python3
from ansicolor import blue, red, black
from .Download import download_if_not_exists
from .NaturalEarth import *
from .ShapefileRecords import *
from .MapRenderer import *
from .Rasterizer import *
import sys
import os
import os.path
import concurrent.futures

urlprefix = "http://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/"

def perform_render(args):
    # Download natural earth data if not present
    download_all()

    svgdir = os.path.join(args.outdir, "SVG")
    if not args.all and not args.country:
        print("Use either --all or specify at least one country")
        parser.print_help()
        sys.exit(1)
    os.makedirs(svgdir, exist_ok=True)
    # Read data
    countries = RecordSet(read_naturalearth_zip("ne_10m_admin_0_countries.zip"))
    mapunits = RecordSet(read_naturalearth_zip("ne_10m_admin_0_map_units.zip"))
    states = RecordSet(read_naturalearth_zip("ne_10m_admin_1_states_provinces.zip"))

    if args.all:
        pool = concurrent.futures.ProcessPoolExecutor(args.parallel)
        # Render all types of structures
        futures = []
        futures += render_all_countries(pool, countries, svgdir, args.color)
        futures += render_all_countries(pool, mapunits, svgdir, args.color)
        futures += render_all_countries(pool, states, svgdir, args.color)
        concurrent.futures.wait(futures)
    else:
        raise NotImplementedError("Please use render --all for the moment")

def rasterize_single(filename, directory, width):
    fileprefix, ext = os.path.splitext(filename)
    svg = os.path.join(directory, "SVG", filename)
    png = os.path.join(directory, "PNG-{}/{}.png".format(width, fileprefix))
    rasterize_svg(svg, png, width)
    print ("Rasterizing {} to {}...".format(filename, png))


def perform_rasterize(args):
    # Check args
    if not args.all and not args.country:
        print("Use either --all or specify at least one country")
        parser.print_help()
        sys.exit(1)
    width = args.width
    # Create directory
    pngdir = os.path.join(args.outdir, "PNG-{}".format(width))
    os.makedirs(pngdir, exist_ok=True)

    if args.all:
        files = os.listdir(os.path.join(args.outdir, "SVG"))
        # Assume we'll rasterize a lot
        pool = concurrent.futures.ThreadPoolExecutor(5) # Don't care about GILs
        futures = []
        for file in files:
            futures.append(pool.submit(rasterize_single, file, args.outdir, width))
        concurrent.futures.wait(futures)
    else:
        for file in args.country:
            rasterize_single(file, args.outdir, width)

def download_all():
    print(blue("Downloading Natural Earth files...", bold=True))
    download_if_not_exists("ne_10m_admin_0_map_units.zip",
        urlprefix + "ne_10m_admin_0_map_units.zip")
    download_if_not_exists("ne_10m_admin_1_states_provinces.zip",
        urlprefix + "ne_10m_admin_1_states_provinces.zip")
    download_if_not_exists("ne_10m_populated_places.zip",
        urlprefix + "ne_10m_populated_places.zip")
    download_if_not_exists("ne_10m_admin_0_countries.zip",
        urlprefix + "ne_10m_admin_0_countries.zip")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--outdir', default="output", help='Output directory')
    parser.add_argument('-p', '--parallel', default=4, type=int, help='If supported, run [n] tasks in parallel')
    parser.set_defaults(func=None)
    subparsers = parser.add_subparsers(title='command', description='Specify one action to perform')
    # Render
    render = subparsers.add_parser("render")
    render.add_argument('country', nargs='*', help='The countries to render')
    render.add_argument('-a', '--all', action="store_true", help='Render all countries')
    render.add_argument('-c', '--color', default="#000", help='HTML color code for SVG')
    render.set_defaults(func=perform_render)
    # Render
    render = subparsers.add_parser("rasterize")
    render.add_argument('country', nargs='*', help='The countries to rasterize')
    render.add_argument('-a', '--all', action="store_true", help='Rasterize all countries')
    render.add_argument('-w', '--width', type=int, default=1000, help='Width of the PNG to create')
    render.set_defaults(func=perform_rasterize)

    args = parser.parse_args()
    if args.func is None:
        print("No command given (try using render)")
        parser.print_help()
        sys.exit(0)
    args.func(args)
