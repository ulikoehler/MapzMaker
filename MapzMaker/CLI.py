#!/usr/bin/env python3
from ansicolor import blue, red, black
import sys
import os
import os.path
import concurrent.futures

def perform_render(args):
    from .ShapefileRecords import RecordSet
    from .NaturalEarth import read_naturalearth_zip
    from .MapRenderer import render_all_states
    # Download natural earth data if not present
    check_download_all()

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

    pool = concurrent.futures.ProcessPoolExecutor(args.parallel)
    futures = []

    if args.all:
        # Render all types of structures
        futures += render_all_states(pool, countries, states, svgdir, args.color)
    else:
        futures += render_all_states(pool, countries, states, svgdir, args.color, only=args.country)
    concurrent.futures.wait(futures)

def rasterize_single(filename, directory, width):
    fileprefix, ext = os.path.splitext(filename)
    svg = os.path.join(directory, "SVG", filename)
    png = os.path.join(directory, "PNG-{}/{}.png".format(width, fileprefix))
    rasterize_svg(svg, png, width)
    print ("Rasterizing {} to {}...".format(filename, png))


def perform_rasterize(args):
    from .Rasterizer import rasterize_svg
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

def check_download_all():
    files = ["ne_10m_admin_0_map_units.zip",
             "ne_10m_admin_1_states_provinces.zip",
             "ne_10m_populated_places.zip",
             "ne_10m_admin_0_countries.zip"]
    if not all([os.path.exists(file) for file in files]):
        download_all(files)

def download_all(files):
    from .Download import download_file
    urlprefix = "http://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/"
    print(blue("Downloading Natural Earth files...", bold=True))
    for file in files:
        download_file(file, urlprefix + file)

def mapzmaker_cli():
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
