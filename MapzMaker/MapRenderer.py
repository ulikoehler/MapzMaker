#!/usr/bin/env python3
from collections import namedtuple
import concurrent.futures
from toolz import dicttoolz
import pyproj
import svgwrite
import functools
import os.path
import numpy as np
from UliEngineering.Math.Geometry import *
from UliEngineering.Math.Coordinates import *
from UliEngineering.Utils.NumPy import *
from UliEngineering.SignalProcessing.Selection import multiselect

from .ShapeTransform import *
from .Projections import *
from .ShapefileRecords import *
from .NaturalEarth import *

def exportMapAsSVG(name, shape, outfile, color="#000", proj="merc", objtype="country"):
    """
    Parameters
    ----------
    simpl_ppm : float
        The polyon simplification factor expressed in ppm
        of the bounding box size.
        Low quality: 100
        Medium quality: 20
        High quality: 5
        Ultra-high quality: 1
        Full quality: 0 (no simplificatio)
    """
    dwg = svgwrite.Drawing(outfile, profile='full')
    points = np.asarray(shape.points.copy())
    # Mirror by X axis
    # as lower latitude represent more southern coords (in contrast to SVG)
    points[:,1] *= -1
    points = project_array(points, dstp=proj)
    # Various coordinate normalization
    normalize_coordinates_svg(points)
    # Find only polygons that are larger than a certain fraction
    # of the total area (i.e. remove tiny islands)
    polys = filter_shapes_by_total_area_threshold(points, shape.parts[1:], 0.001)
    # Compute bbox only from remaining points
    bbox = BoundingBox(np.vstack(polys))
    # Compute actual simplification coefficient based on bbox
    # NOTE: bbox area is NOT actual area due to normalization
    #simpl_coefficient = simpl_ppm * bbox.area / 1e6
    # Set SVG viewbox to bounding box
    dwg.viewbox(width=bbox.width, height=bbox.height)
    # Draw all polygons
    for poly in polys:
        # Draw to SVG
        #if simpl_coefficient != 0:
        #    poly = iterative_merge_simplify(poly, simpl_coefficient)
        dwg.add(svgwrite.shapes.Polygon(poly, fill=color,
            class_="{}-{}".format(objtype,
                name.lower().replace(" ", "-").replace(".", "").replace("(","").replace(")",""))))
    dwg.save()


def _render_single(name, shape, outname, color, objtype="country"):
    try:
        # Create directory
        os.makedirs(os.path.dirname(outname), exist_ok=True)
        # Render
        exportMapAsSVG(name, shape, outname, color, objtype=objtype)
        print("Rendered {} to {}".format(name, outname))
        return True
    except Exception as e:
        print("{} failed: {}".format(name, e))
        return False

def render_all_countries(pool, countries, directory, color, only=[]):
    """
    Render country overviews
    """
    by_isoa2 = countries_by_isoa2(countries)
    # Apply only filter
    if only:
        by_isoa2 = dicttoolz.keyfilter(
            lambda k: k in only, by_isoa2)

    futures = []
    for isoa2, country in by_isoa2.items():
        name = country.name
        shape = countries.reader.shape(country.index)
        # Build outname & create directory
        outname = os.path.join(directory, isoa2, "Country", name + ".svg")
        # Run asynchronously
        futures.append(pool.submit(_render_single, name, shape, outname, color, "country"))
    return futures

def render_all_states(pool, countries, states, directory, color, only=[]):
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
        name = country.name
        try: name = country.name_long
        except: pass
        # Get states
        if isoa2 not in states_by_isoa2:
            continue
        for state in states_by_isoa2[isoa2]:
            shape = states.reader.shape(state.index)
            statename = state.woe_name or state.name
            if not statename:
                print(state)
                continue
            # Build outname & create directory
            outname = os.path.join(directory, isoa2, "States", statename + ".svg")
            # Run asynchronously
            futures.append(pool.submit(_render_single, statename, shape, outname, color, "state"))
        # TODO: Render country with state overlay
    return futures

def render_country(countries, directory, name):
    pool = multiprocessing.Pool(4)
    country = countries.by_name(name)[0]
    shape = _find_shape(countries, name)
    _render_single(name, shape, os.path.join(directory, name + ".svg"))
