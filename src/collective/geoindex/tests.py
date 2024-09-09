# -*- coding: utf-8 -*-
from .index import GeospatialIndex
from OFS.Folder import Folder
from Products.ZCatalog.Catalog import Catalog

import doctest
import unittest


optionflags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS


class DummyItem(object):
    """some dummy with a start, delta and until to index"""

    def __init__(self, id=None, geolocation=None):
        self.id = id
        self.geolocation = geolocation


class DummyExtras(object):
    def __init__(self, leaf_capacity=20, dimension=2):
        self.leaf_capacity = leaf_capacity
        self.dimension = dimension


class TestIndex(unittest.TestCase):

    def setUp(self) -> None:
        self.index = GeospatialIndex(
            "geolocation",
            extra=DummyExtras(
                leaf_capacity=20,
            ),
        )
        self.cat = Catalog()
        self.cat.addIndex("geolocation", self.index)
        self.cat.addColumn("id")

        # catalog needs to be contained somewhere, otherwise
        # aquisition-wrapping of result brains doesn't work
        portal = Folder(id="portal")
        self.cat.__parent__ = portal

        self.berlin = DummyItem(id="berlin", geolocation=(13.24, 52.21, 13.24, 52.21))
        self.rome = DummyItem(id="rome", geolocation=(12.32, 41.53, 12.32, 41.53))
        self.bologna = DummyItem(id="bologna", geolocation=(11.20, 44.29, 11.20, 44.29))
        self.padua = DummyItem(id="padua", geolocation=(11.52, 45.24, 11.52, 45.24))

        self.italy = (6.62, 35.49, 18.52, 47.09)  # bbox around italy

        self.cat.catalogObject(self.berlin, "berlin")
        self.cat.catalogObject(self.rome, "rome")
        self.cat.catalogObject(self.bologna, "bologna")

    def test_index(self):
        self.assertEqual(self.index.indexSize(), 3)
        self.assertEqual(len(list(self.index.intersection(self.italy))), 2)

    def test_catalog_intersection(self):
        self.assertEqual(len(self.cat(geolocation=self.italy)), 2)
        self.assertEqual(
            len(
                self.cat(geolocation={"query": self.italy, "operator": "intersection"})
            ),
            2,
        )

    def test_catalog_nearest(self):
        res = self.cat(
            geolocation={
                "query": self.padua.geolocation,
                "operator": "nearest",
                "limit": 1,
            }
        )
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].id, "bologna")

        res = self.cat(
            geolocation={
                "query": self.padua.geolocation,
                "operator": "nearest",
                "limit": 2,
            }
        )
        self.assertEqual(len(res), 2)
        # TODO: at the moment sorting is not yet implemented
        # self.assertEqual(res[0].id, 'bologna')
        # self.assertEqual(res[1].id, 'rome')
        self.assertIn("bologna", [it.id for it in res])
        self.assertIn("rome", [it.id for it in res])

    def test_catalog_multiple(self):
        nordest = DummyItem(
            id="nordest", geolocation=(self.bologna.geolocation, self.padua.geolocation)
        )
        self.cat.catalogObject(nordest, "nordest")
        res = self.cat(geolocation=self.italy)
        self.assertEqual(len(res), 3)
        self.assertIn("bologna", [it.id for it in res])
        self.assertIn("rome", [it.id for it in res])
        self.assertIn("nordest", [it.id for it in res])

    # def test_catalog_sort(self):
