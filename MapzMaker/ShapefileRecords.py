#!/usr/bin/env python3
import shapefile
import operator
from collections import namedtuple

FieldInfo = namedtuple("FieldInfo", ["name", "type", "length", "declength"])

def FieldInfos(reader):
    """
    Get a list of FieldInfo namedtuples for the reader
    """
    return [FieldInfo(*l) for l in reader.fields[1:]]

def FieldNamedtuple(reader):
    """
    Create a new namedtuple representing the fields of a reader
    """
    field_infos = FieldInfos(reader)
    return namedtuple("Record", ["index"] + [fi.name.lower() for fi in field_infos])

def record_namedtuples(reader):
    recordcls = FieldNamedtuple(reader)
    for i, record in enumerate(reader.iterRecords()):
        yield recordcls(i, *[field.decode("utf-8").strip() if isinstance(field, bytes) else field
                             for field in record])


class RecordSet(object):
    """
    An in-memory set of records from a shapefile.
    """
    def __init__(self, arg, reader=None):
        """
        Initialize, either with a reader or a list of records:
        """
        if isinstance(arg, shapefile.Reader):
            self.records = list(record_namedtuples(arg))
            self.reader = arg
        else: # Assume list of records
            self.records = arg
            self.reader = None
    def _by_attrgetter(self, getter, comp):
        """
        Filter records by applying a getter function to
        each record and comparing it to a comparison value
        """
        return RecordSet([r for r in self.records if getter(r) == comp])
    def by_datarank(self, dr):
        return self._by_attrgetter(operator.attrgetter("datarank"), dr)
    def by_scalerank(self, sr):
        return self._by_attrgetter(operator.attrgetter("scalerank"), sr)
    def by_name(self, name):
        return self._by_attrgetter(operator.attrgetter("name"), name)
    def by_index(self, idx):
        for rec in self.records:
            if rec.index == idx:
                return rec
        return None
    def names(self):
        return list(map(operator.attrgetter("name"), self.records))
    def __getitem__(self, key):
        return self.records.__getitem__(key)
    def __repr__(self):
        return "RecordSet({})".format(self.records)
