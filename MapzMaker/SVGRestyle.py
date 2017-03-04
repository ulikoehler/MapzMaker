#!/usr/bin/env python3
"""
Routines to highlight specific elements of a SVG
"""
from bs4 import BeautifulSoup
import numpy as np
from UliEngineering.Math.Coordinates import *
from slugify import slugify

def soup_from_svg(filename):
    with open(filename) as infile:
        return BeautifulSoup(infile, "xml")

def soup_to_svg(soup, filename):
    with open(filename, "wb") as outfile:
        outfile.write(soup.prettify("utf-8"))

def parse_poly(attr):
    return np.asarray([[float(s2) for s2 in s.split(",")] for s in attr.split(" ")])

def parse_attrmap(attrdefs):
    attrmap = {}
    for attrdef in attrdefs:
        name, _, attr = attrdef.rpartition(":")
        attrmap[slugify(name)] = attr
    return attrmap

def highlight_svg(infile, outfile, coldefs):
    soup = soup_from_svg(infile)
    colormap = parse_attrmap(coldefs)
    # Process all polygons
    for poly in soup.svg.childGenerator():
        if poly.name not in ["polygon", "polyline"]:
            continue
        cls = poly.attrs["class"]
        clstype, _, name = cls.partition("-")
        if name in colormap:
            poly.attrs["fill"] = colormap[name]
        # Process polygon
        #poly = parse_poly(poly.attrs["points"])
    soup = soup_to_svg(soup, outfile)
