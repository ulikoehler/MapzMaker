#!/usr/bin/env python3
import pyproj
import numpy as np

def project_array(coordinates, srcp='latlong', dstp='wintri'):
    """
    Project a numpy (n,2) array in projection srcp to projection dstp
    Returns a numpy (n,2) array.
    """
    p1 = pyproj.Proj(proj=srcp, datum='WGS84')
    p2 = pyproj.Proj(proj=dstp, datum='WGS84')
    fx, fy = pyproj.transform(p1, p2, coordinates[:,0], coordinates[:,1])
    # Re-create (n,2) coordinates
    return np.dstack([fx, fy])[0]