#!/usr/bin/env python3
from UliEngineering.SignalProcessing.Selection import multiselect
from UliEngineering.Utils.NumPy import *
from UliEngineering.Math.Geometry import *
from UliEngineering.Math.Coordinates import *
from scipy.spatial.distance import euclidean
import numpy as np

def filter_shapes_by_total_area_threshold(points, pivots, threshold=.005):
    """
    Split a given point list by a pivot list to obtain a list
    of polygons.
    then filter out polygons that have less than the given fraction of
    the total area.
    """
    parts = list(split_by_pivot(points, pivots))
    partareas = np.zeros(len(parts))
    # Compute all part areas
    for i, part in enumerate(parts):
        partareas[i] = polygon_area(part)
    total_area = np.sum(partareas)
    # Find areas below the threshold
    idxs = np.where(partareas > threshold * total_area)[0]
    # Select from parts list
    return multiselect(parts, idxs)


def node_pairwise_distance(poly):
    """
    return[i] = euclidean dist from poly[i] to poly[i],
    assuming poly is closed
    """
    dist = np.zeros(poly.shape[0])
    for i, ngram in enumerate(ngrams(poly, 2, closed=True)):
        dist[i] = euclidean(ngram[0], ngram[1])
    return dist

def compute_merge_direction(poly):
    """
    Computes a pairwise distance between any two nodes
    and computes score arrays indicating whether any node
    can be merged to the left or to the right.
    """
    pwdist = node_pairwise_distance(poly)
    merge_left = np.full(pwdist.shape[0], np.inf)
    merge_right = np.full(pwdist.shape[0], np.inf)
    for i in range(pwdist.shape[0]):
        merge_right[i] = pwdist[i]
        merge_left[(i + 1) % poly.shape[0]] = pwdist[i]
    return merge_left, merge_right


def pairwise_merge_points(poly):
    ret = np.zeros_like(poly)
    for i, ngram in enumerate(ngrams(poly, 2, closed=True)):
        ret[i] = (ngram[0] + ngram[1]) / 2.
    return ret

def compute_merge_area_differences(poly):
    """
    Compute the absolute difference of area for a given shape,
    when merging node i and i+1.
    
    Returns a numpy area of absolute differences in area.
    """
    areadiffs = np.ones(poly.shape[0])
    # Compute how much area is added or removed by removing the given point
    for i, ngram in enumerate(ngrams(poly, 4, closed=True)):
        # (i+1) and (i+2) will be merged
        mergepoint = (ngram[0] + ngram[1]) / 2.
        # Compute the area difference regarding the left side
        diff_left = polygon_area(np.asarray([ngram[0], ngram[1], mergepoint]))
        # Compute the area difference regarding the left side
        diff_right = polygon_area(np.asarray([mergepoint, ngram[2], ngram[3]]))
        # Compute total diff
        areadiffs[(i + 1) % poly.shape[0]] = diff_left + diff_right
    return areadiffs

def pairwise_merge_points(poly):
    ret = np.zeros_like(poly)
    for i, ngram in enumerate(ngrams(poly, 2, closed=True)):
        ret[i] = (ngram[0] + ngram[1]) / 2.
    return ret

def compute_delete_area_differences(poly):
    """
    Compute the absolute difference of area for a given shape,
    when removing node i, for every node i.
    
    Returns a numpy area of absolute differences in area.
    """
    areadiffs = np.ones(poly.shape[0])
    # Compute how much area is added or removed by removing the given point
    for i, ngram in enumerate(ngrams(poly, 3, closed=True)):
        # We're computing the diffarea of the middle point.
        # Therefore we can't just use i as idx
        areadiffs[(i + 1) % poly.shape[0]] = polygon_area(ngram)
    return areadiffs

def compute_merge_area_differences(poly):
    """
    Compute the absolute difference of area for a given shape,
    when merging node i and i+1.
    
    Returns a numpy area of absolute differences in area.
    """
    areadiffs = np.ones(poly.shape[0])
    # Compute how much area is added or removed by removing the given point
    for i, ngram in enumerate(ngrams(poly, 4, closed=True)):
        # (i+1) and (i+2) will be merged
        mergepoint = (ngram[1] + ngram[2]) / 2.
        # Compute the area difference regarding the left side
        diff_left = polygon_area(np.asarray([ngram[0], ngram[1], mergepoint]))
        # Compute the area difference regarding the left side
        diff_right = polygon_area(np.asarray([mergepoint, ngram[2], ngram[3]]))
        # Compute total diff
        areadiffs[(i + 1) % poly.shape[0]] = diff_left + diff_right
    return areadiffs


def merge_polygon_threshold(poly, threshold=1.):
    """
    Merge polygon nodes that are close together in a way
    that ensures only polygons are merged that
    do not significantly modify the shape.
    
    For optimum efficiency, this function needs to be called iteratively.
    Poly will be modified in-place.
    """
    areadiffs = compute_merge_area_differences(poly)
    merged = areadiffs < threshold
    valid = np.ones_like(merged) # Set to False if this point shall be ignroed 
    # Merge, replacing merged points with np.inf
    for i in range(areadiffs.shape[0]):
        if merged[i]:
            next_idx = (i + 1) % poly.shape[0]
            this = poly[i]
            other = poly[next_idx]
            # Compute & set merged point
            # Other must be set because this will be replaced by inf
            poly[next_idx] = (this + other) / 2
            # Invalidate this
            poly[i,:] = np.inf
            # do not merge next (because we set it to the merged point)
            # We need to recalculate the area diffs,
            #  which is handled by iterative calls of this function
            merged[next_idx] = False
            # Ignore the point from now on
            valid[i] = False
    # Filter out merged points 
    return poly[valid,:]


def iterative_merge_simplify(poly, threshold, nlimit=16, stopdiff=1):
    poly = poly.copy()
    lastsize = poly.shape[0]
    # Iterate until:
    #   a) nlimit is reached or 
    #   b) The difference between passes is < stoplimit
    for i in range(nlimit):
        poly = merge_polygon_threshold(poly, threshold)
        newsize = poly.shape[0]
        if (lastsize - newsize) < stopdiff:
            break
    return poly
            
def normalize_coordinates_svg(points, bbox):
    """
    Normalize coordinates to 0,0 origin & coordinate scale
    which is suitable for SVG rendering.
    Uses bbox as reference bounding box.
    Operates in-place.
    """
    # Substract bounding box (one bbox corner := (0,0))
    points[:,0] -= bbox.minx
    points[:,1] -= bbox.miny

    # Scale to avoid huuuuge coordinates
    # due to the projection mechanics of pyproj
    points *= 100. / bbox.max_dim
