#!/usr/bin/env python3
"""
Rasterize SVGs using inkscape
"""
import subprocess
import os

def rasterize_svg(svg, png, width):
    subprocess.check_output(["inkscape", "-z", "-e", png, "-w", str(width), svg])
    return svg, png