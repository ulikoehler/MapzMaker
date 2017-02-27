#!/usr/bin/env python3
from collections import namedtuple
import concurrent.futures
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

def exportMapAsSVG(name, shape, outfile, color="#000", proj="merc"):
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
    #simpl_coefficient = simpl_ppm * bbox.area / 1e6
    # Set SVG viewbox to bounding box
    dwg.viewbox(width=bbox.width, height=bbox.height)
    # Draw all polygons
    for poly in polys:
        # Draw to SVG
        #if simpl_coefficient != 0:
        #    poly = iterative_merge_simplify(poly, simpl_coefficient)
        dwg.add(svgwrite.shapes.Polygon(poly, fill=color,
            class_="country-" + name.lower().replace(" ", "-").replace(".", "")))
    dwg.save()


def _render_country(name, shape, outname, color):
    try:
        exportMapAsSVG(name, shape, outname, color)
        print("Rendered {}...".format(name))
        return True
    except Exception as e:
        print("{} failed: {}".format(name, e))
        return False

def _find_shape(countries, name):
    country = countries.by_name(name)[0]
    return countries.reader.shape(country.index)

def render_all_countries(countries, directory, color, concurrency=4):
    pool = concurrent.futures.ProcessPoolExecutor(concurrency)
    futures = []
    for name in countries.names():
        shape = _find_shape(countries, name)
        outname = os.path.join(directory, name + ".svg")
        futures.append(pool.submit(_render_country, name, shape, outname, color))
    concurrent.futures.wait(futures)

def render_country(countries, directory, name):
    pool = multiprocessing.Pool(4)
    _render_country(name, _find_shape(countries, name), os.path.join(directory, name + ".svg"))
