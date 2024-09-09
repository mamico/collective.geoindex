# -*- coding: utf-8 -*-
from plone.testing import Layer
from plone.testing import z2


class DRILayer(Layer):

    defaultBases = (z2.STARTUP,)

    def setUp(self):
        with z2.zopeApp() as app:
            z2.installProduct(app, "collective.geoindex")

    def tearDown(self):
        with z2.zopeApp() as app:
            z2.uninstallProduct(app, "collective.geoindex")


DRI_FIXTURE = DRILayer()
