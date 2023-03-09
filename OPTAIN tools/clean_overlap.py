# -*- coding: utf-8 -*-

"""
***************************************************************************
    clean_operlap.py
    ---------------------
    Date                 : September 2022
    Copyright         : (C) 2022 by Enrico A. Chiaradia
    Email                : enrico.chiaradia@unimi.it
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
Credits:
freely inspired by:
https://gis.stackexchange.com/questions/95573/finding-the-common-borders-between-polygons-in-the-same-shapefile
"""

__author__ = 'Enrico A. Chiaradia'
__date__ = 'September 2022'
__copyright__ = '(C) 2022, Enrico A. Chiaradia'

import os

from PyQt5.QtCore import QCoreApplication
from qgis import processing
from qgis.PyQt.QtGui import QIcon

from qgis.core import (QgsApplication,
                       QgsFeatureRequest,
                       QgsFeature,
                       QgsFeatureSink,
                       QgsGeometry,
                       QgsProcessingAlgorithm,
                       QgsProcessingException,
                       QgsProcessingUtils,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterEnum,
                       QgsProcessing,
                       QgsProcessingParameterFeatureSink, QgsVectorLayer, QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsWkbTypes)

pluginPath = os.path.split(os.path.split(os.path.dirname(__file__))[0])[0]


class CleanOverlap(QgsProcessingAlgorithm):
    LAYER1 = 'LAYER1'
    LAYER2 = 'LAYER2'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return CleanOverlap()

    def icon(self):
        return QgsApplication.getThemeIcon("/algorithms/mAlgorithmDissolve.svg")

    def svgIconPath(self):
        return QgsApplication.iconPath("/algorithms/mAlgorithmDissolve.svg")

    def group(self):
        return self.tr('Optain tools')

    def groupId(self):
        return 'optaintools'

    def __init__(self):
        super().__init__()

    def flags(self):
        return super().flags() | QgsProcessingAlgorithm.FlagNoThreading | QgsProcessingAlgorithm.FlagNotAvailableInStandaloneTool

    def initAlgorithm(self, config=None):

        self.addParameter(QgsProcessingParameterVectorLayer(self.LAYER1,
                                                            self.tr('Layer with overlap'), [QgsProcessing.TypeVectorPolygon]))


        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('Cleared'), QgsProcessing.TypeVectorLine))

    def name(self):
        return 'cleanoverlap'

    def displayName(self):
        return self.tr('Clear operlapping features')

    def processAlgorithm(self, parameters, context, feedback):
        layer1 = self.parameterAsVectorLayer(parameters, self.LAYER1, context)
        # populate temporarily layer to use spatial selection
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                               layer1.fields(), QgsWkbTypes.MultiPolygon, layer1.sourceCrs())

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        feedback.pushInfo('poly1;poly2;geom;area')

        nFeat = layer1.featureCount()
        processCount = 0
        # loop in layer 2
        justProcessed = []
        for poly1 in layer1.getFeatures():

            if feedback.isCanceled():
                break

            processCount += 1
            feedback.setProgress(100 * float(processCount) / nFeat)

            justProcessed.append(poly1.id())
            geom1 = poly1.geometry()
            newGeom1 = QgsGeometry(geom1)

            bbox = geom1.boundingBox()
            fit = layer1.getFeatures(
                QgsFeatureRequest().setFilterRect(bbox))

            # use prepared geometries for faster intersection tests
            engine = QgsGeometry.createGeometryEngine(geom1.constGet())
            engine.prepareGeometry()

            # for each polygon in layer 2, get touching polygons in layer 1
            for poly2 in fit:
                if (poly2.id() != poly1.id()) and\
                        (poly2.id() not in justProcessed):

                    geom2 = poly2.geometry()
                    # calculate intersection
                    if engine.intersects(geom2.constGet()):

                        # calculate intersection
                        iGeom = geom1.intersection(geom2)

                        if iGeom.area()>0:
                            feedback.pushInfo('%s;%s;%s;%s' % (poly1.id(), poly2.id(),iGeom.centroid().asWkt(3),iGeom.area()))

                        if not iGeom:
                            continue

                        # cut current geometry with intersection
                        newGeom1 = newGeom1.difference(geom2)

            # save processed feature in sink
            newFeat = QgsFeature(poly1)
            newFeat.setGeometry(newGeom1)
            # add to sink
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)

        del sink

        return {self.OUTPUT: dest_id}
