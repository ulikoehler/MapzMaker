#!/usr/bin/env python3
import shapefile
from UliEngineering.Utils.Files import *
from UliEngineering.Utils.ZIP import *
from toolz import itertoolz
import operator

def read_naturalearth_zip(filename):
    """
    Read a shapefile from a NaturalEarth ZIP, extracting it in-memory

    Returns
    -------
    A shapefile reader
    """
    # List files inside ZIP
    zipcontents = list(list_zip(filename))
    # Find one filename that is present with ".shp", ".dbf" and ".prj" extensions
    dataset_filenames = find_datasets_by_extension(zipcontents, (".shp", ".dbf", ".prj"))
    # Read the files (copy to memory)
    dataset = read_from_zip(filename, next(dataset_filenames))
    # Read shapefile format
    return shapefile.Reader(shp=dataset[0], dbf=dataset[1], prj=dataset[2])


def countries_by_isoa2(countries):
    """
    A map of country ISO 3166-1 alpha-2
    to the country record
    """
    return {
        country.iso_a2: country
        for country in countries.records
    }

def countries_by_isoa3(countries):
    """
    A map of country ISO 3166-1 alpha-3
    to the country record
    """
    return {
        country.iso_a3: country
        for country in countries.records
    }


def states_by_country(states):
    """
    A list of states by country ISO 3166-1 alpha-3 code
    """
    return itertoolz.groupby(operator.attrgetter("iso_a2"), states.records)
