#!/usr/bin/env python3
from ansicolor import blue, red, black
import sys
import os
import glob
import os.path
import concurrent.futures

def perform_render(parser, args):
    from .ShapefileRecords import RecordSet
    from .NaturalEarth import read_naturalearth_zip
    from .MapRenderer import render_all_states
    # Download natural earth data if not present
    check_download_all()

    svgdir = os.path.join(args.directory, "SVG")
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

def perform_rasterize(parser, args):
    from .Rasterizer import rasterize_svg
    # Check args
    if not args.all and not args.country:
        print("Use either --all or specify at least one country")
        parser.print_help()
        sys.exit(1)
    width = args.width
    # Create directory
    pngdir = os.path.join(args.directory, "PNG-{}".format(width))
    os.makedirs(pngdir, exist_ok=True)

    # Assume we'll rasterize a lot
    # GIL can be ignored, because we're rasterizing using subprocess (inkscape)
    pool = concurrent.futures.ThreadPoolExecutor(args.parallel) # Don't care about GILs
    futures = []

    svgdir = os.path.join(args.directory, "SVG")
    pngdir = os.path.join(args.directory, "PNG.{}".format(width))
    for dirpath, subdirs, filenames in os.walk(svgdir):
        relpath = os.path.relpath(dirpath, svgdir)
        # Check country filter
        country = os.path.split(relpath)[0]
        if not args.all and country not in args.country:
            continue
        for filename in filenames:
            canonical, ext = os.path.splitext(filename)
            # Only handle SVGs
            if ext.lower() != ".svg":
                continue
            # Build input/output paths
            svgpath = os.path.join(dirpath, filename)
            pngpath = os.path.join(pngdir, relpath, canonical + ".png")
            # Create directory tree
            os.makedirs(os.path.dirname(pngpath), exist_ok=True)
            print("Rasterizing to {}".format(pngpath))
            # Rasterize async
            futures.append(pool.submit(rasterize_svg, svgpath, pngpath, width))
    concurrent.futures.wait(futures)

def check_download_all():
    files = ["ne_10m_admin_0_map_units.zip",
             "ne_10m_admin_1_states_provinces.zip",
             "ne_10m_populated_places.zip",
             "ne_10m_admin_0_countries.zip"]
    if not all([os.path.exists(file) for file in files]):
        download_all(files)

def perform_highlight(parser, args):
    from .SVGRestyle import highlight_svg
    svgglob = os.path.join(args.directory, "SVG", args.country, "Country", "*.states.svg")
    svgglob_result = glob.glob(svgglob)
    if not svgglob_result:
        raise ValueError("Can't find SVG file '{}'".format(svgglob))
    highlight_svg(svgglob_result[0], args.outfile, args.coldefs)

def download_all(files):
    from .Download import download_file
    urlprefix = "http://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/"
    print(blue("Downloading Natural Earth files...", bold=True))
    for file in files:
        download_file(file, urlprefix + file)

def mapzmaker_cli():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', default="output", help='Input & output directory')
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
    # Highlight
    highlight = subparsers.add_parser("highlight-states")
    highlight.add_argument('country', help='The country (ISO 3166 alpha 2 code, e.g. "DE", "US") to highlight from. Auto-selects the correct SVG file')
    highlight.add_argument('outfile', help='Output SVG file')
    highlight.add_argument('-c', '--color',  nargs='+', dest="coldefs", help='[state:color] - Highlight a state with a SVG color. State is automatically slugified')
    highlight.set_defaults(func=perform_highlight)

    args = parser.parse_args()
    if args.func is None:
        print("No command given (try using render)")
        parser.print_help()
        sys.exit(0)
    args.func(parser, args)
