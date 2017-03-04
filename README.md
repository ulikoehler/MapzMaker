# MapzMaker
[![Made with Natural Earth data](https://github.com/ulikoehler/MapzMaker/blob/master/doc/NEV-Logo-Black.png)](http://www.naturalearthdata.com/)

MapzMaker is a set of scripts to render
  - Country contours
  - States
  - Cities
and other geographic overview data to SVG graphics and PNG images.

Its purpose is to provide 100% public-domain country images accessible to anyone, anywhere, anytime!

# Installation

You can use `mapzmaker` directly from the repository, no installation required! Best of all: You don't even need to download any data, mapzmaker will do that for you!

```
git clone https://github.com/ulikoehler/MapzMaker.git
cd MapzMaker
sudo pip3 install -r requirements.txt
```

Let's render Germany and France!

```
./mapzmaker render DE FR
```

and make PNGs with width 1000
```
./mapzmaker rasterize
```

The first time you use it, a few megabytes of country contours will be downloaded. mapzmaker will then render each country contour, and every state contour separately, telling you the files it is rendering to.

Now we have some SVGs (you can have a look at them in your browser), but we can also create PNGs, assuming you have [`inkscape`](https://inkscape.org/) installed

Output example:

`output/SVG/DE/Country/Germany.svg`: TODO
