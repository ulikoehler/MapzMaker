#!/usr/bin/env python3
from collections import namedtuple
import concurrent.futures
from toolz import dicttoolz, itertoolz, functoolz
from slugify import slugify
import pyproj
import svgwrite
import functools
import os.path
import sys
import traceback
import numpy as np
from UliEngineering.Math.Geometry import *
from UliEngineering.Math.Coordinates import *
from UliEngineering.Utils.NumPy import *
from UliEngineering.SignalProcessing.Selection import multiselect

from .ShapeTransform import *
from .Projections import *
from .ShapefileRecords import *
from .NaturalEarth import *

def shape_to_polys(shape, ref_bbox=None, filter_area_thresh=.01, proj="merc"):
    points = np.asarray(shape.points.copy())
    # Mirror by X axis
    # as lower latitude represent more southern coords (in contrast to SVG)
    points[:,1] *= -1
    points = project_array(points, dstp=proj)
    # Compute reference bounding box if not using external reference
    if ref_bbox is None:
        ref_bbox = BoundingBox(points)
    # Various coordinate normalization
    normalize_coordinates_svg(points, bbox=ref_bbox)
    # Find only polygons that are larger than a certain fraction
    # of the total area (i.e. remove tiny islands)
    polys = filter_shapes_by_total_area_threshold(points, shape.parts[1:], filter_area_thresh)
    return polys, ref_bbox

def _set_viewbox(dwg, polys):
    """
    Set the viewbox from polygons
    """
    # Compute bbox only from remaining points
    bbox = BoundingBox(np.vstack(polys))
    # Set SVG viewbox to bounding box
    dwg.viewbox(width=bbox.width, height=bbox.height)

def __draw_to_svg(dwg, poly, name, stylemap, objtype):
    dwg.add(svgwrite.shapes.Polygon(poly,
        class_="{}-{}".format(objtype, slugify(name)),
        **stylemap))

def draw_single_map(dwg, name, polys, stylemap, objtype="country"):
    _set_viewbox(dwg, polys)
    # Draw all polygons
    for poly in polys:
        # Draw to SVG
        __draw_to_svg(dwg, poly, name, stylemap, objtype)

def draw_country_state_map(dwg, name, country_polys, state_polymap, stylemap1, stylemap2={"color": "#fff"}):
    # Draw the country
    for poly in country_polys:
        # Draw to SVG
        __draw_to_svg(dwg, poly, name, stylemap1, "country")
    # Draw the states
    for statename, state in state_polymap.items(): # Each state might have multiple polys
        for poly in state:
            # Draw to SVG
            __draw_to_svg(dwg, poly, statename, stylemap2, "state")



def _render_single(name, shape, outname, stylemap, objtype="country", proj="merc"):
    try:
        # Create directory
        os.makedirs(os.path.dirname(outname), exist_ok=True)
        # Create SVG
        dwg = svgwrite.Drawing(outname, profile='full')
        # Preprocess shape
        polys, _ = shape_to_polys(shape, proj=proj)
        # Render & save
        draw_single_map(dwg, name, polys, stylemap, objtype=objtype)
        dwg.save()
        # Log
        print("Rendered {} to {}".format(name, outname))
        return True
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("{} failed: {}".format(name, e))
        traceback.print_tb(exc_traceback)
        return False

def _render_state_overlay(name, country_shape, subshape_map, outname, stylemap, proj="merc"):
    try:
        # Create directory
        os.makedirs(os.path.dirname(outname), exist_ok=True)
        # Create SVG
        dwg = svgwrite.Drawing(outname, profile='full')
        # Preprocess shapes
        country_polys, bbox = shape_to_polys(country_shape, proj=proj)
        subpolymap = dicttoolz.valmap(
                lambda shape: shape_to_polys(
                    shape, proj=proj, ref_bbox=bbox)[0], subshape_map)
        # Render & save
        draw_country_state_map(dwg, name, country_polys, subpolymap, stylemap)
        # Set viewbox
        _set_viewbox(dwg, country_polys)
        dwg.save()
        # Log
        print("Rendered state overlay for {} to {}".format(name, outname))
        return True
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("{} failed: {}".format(name, e))
        traceback.print_tb(exc_traceback)
        return False

def render_all_states(pool, countries, states, directory, stylemap, only=[]):
    """
    Render states
    """
    # Build state map
    states_by_isoa2 = states_by_country(states)
    country_by_isoa2 = countries_by_isoa2(countries)
    # Apply only filter
    if only:
        country_by_isoa2 = dicttoolz.keyfilter(
            lambda k: k in only, country_by_isoa2)

    futures = []
    for isoa2, country in country_by_isoa2.items():
        #
        # Render country name
        #
        countryname = country.name
        try: countryname = country.name_long
        except: pass
        countryshape = countries.reader.shape(country.index)
        outname = os.path.join(directory, isoa2, "Country", countryname + ".svg")
        futures.append(pool.submit(_render_single, countryname, countryshape, outname, stylemap, "country"))
        # Get states
        if isoa2 not in states_by_isoa2:
            continue
        statemap = {}
        #
        # Render individual states
        #
        for state in states_by_isoa2[isoa2]:
            stateshape = states.reader.shape(state.index)
            statename = state.woe_name or state.name
            if not statename:
                print(state)
                continue
            # Add to statemap for later combined rendering
            statemap[statename] = stateshape
            # Build outname & create directory
            outname = os.path.join(directory, isoa2, "States", statename + ".svg")
            # Render state asynchronously
            futures.append(pool.submit(_render_single, statename, stateshape, outname, stylemap, "state"))
        #
        # Render country with state overlay
        #
        outname = os.path.join(directory, isoa2, "Country", countryname + ".states.svg")
        futures.append(pool.submit(_render_state_overlay,
            countryname, countryshape, statemap, outname, stylemap))
    return futures

def render_country(countries, directory, name):
    pool = multiprocessing.Pool(4)
    country = countries.by_name(name)[0]
    shape = _find_shape(countries, name)
    _render_single(name, shape, os.path.join(directory, name + ".svg"))
