#!/usr/bin/env python3
from collections import namedtuple
import pyproj
import multiprocessing
import svgwrite
import functools
import os
import numpy as np
from UliEngineering.Math.Geometry import *
from UliEngineering.Math.Coordinates import *
from UliEngineering.Utils.NumPy import *
from UliEngineering.SignalProcessing.Selection import multiselect

from .ShapeTransform import *
from .Projections import *
from .ShapefileRecords import *
from .NaturalEarth import *

def exportMapAsSVG(shape, outfile, simpl_ppm=1., proj="merc"):
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
    polys = filter_shapes_by_total_area_threshold(points, shape.parts[1:], 0.005)
    # Compute bbox only from remaining points
    bbox = BoundingBox(np.vstack(polys))
    # Compute actual simplification coefficient based on bbox
    # NOTE: bbox area is NOT actual area due to normalization
    simpl_coefficient = simpl_ppm * bbox.area / 1e6
    # Set SVG viewbox to bounding box
    dwg.viewbox(width=bbox.width, height=bbox.height)
    # Draw all polygons
    for poly in polys:
        # Draw to SVG
        # Low quality: 1. Medium quality: .2  High quality: .05 Ultra-high: .01
        if simpl_coefficient != 0:
            poly = iterative_merge_simplify(poly, simpl_coefficient)
        dwg.add(svgwrite.shapes.Polygon(poly))
    dwg.save()


def _render_country(args):
    try:
        name, shape, outname = args
        exportMapAsSVG(shape, outname, 5)
        print("Rendered {}...".format(name))
        return True
    except Exception as e:
        print("{} failed: {}".format(name, e))
        return False

def _find_shape(countries, name):
    country = countries.by_name(name)[0]
    return countries.reader.shape(country.index)

def render_all_countries(countries, directory):
    os.makedirs(directory, exist_ok=True)
    pool = multiprocessing.Pool(4)
    args = [(name, _find_shape(countries, name), os.path.join(directory, name + ".svg"))
            for name in countries.names()]
    pool.map(_render_country, args)

def render_country(countries, name):
    pool = multiprocessing.Pool(4)
    _render_country(countries, countries.names())
