# -*- coding: utf-8 -*-

"""
***************************************************************************
    find_common_edge.py
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


class FindCommonEdges(QgsProcessingAlgorithm):
    LAYER1 = 'LAYER1'
    LAYER2 = 'LAYER2'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return FindCommonEdges()

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
                                                            self.tr('First layer'), [QgsProcessing.TypeVectorPolygon]))

        self.addParameter(QgsProcessingParameterVectorLayer(self.LAYER2,
                                                            self.tr('Second layer'), [QgsProcessing.TypeVectorPolygon]))

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('Merged'), QgsProcessing.TypeVectorLine))

    def name(self):
        return 'findcommonedges'

    def displayName(self):
        return self.tr('Find common edges')

    def getCuttingLimits(self, poly1, poly2,addLength=20):
        # compute the rings
        #print(poly1.geometry().asMultiPolygon()[0][0])
        ring1 = QgsGeometry.fromPolylineXY(poly1.geometry().asMultiPolygon()[0][0])
        ring2 = QgsGeometry.fromPolylineXY(poly2.geometry().asMultiPolygon()[0][0])
        # predicate
        commonEdge = None
        if ring1.intersects(ring2):
            #commonEdge = ring1.intersection(ring2)
            commonEdge = ring1.difference(ring2)
            commonEdge = commonEdge.extendLine(addLength,addLength)


        return commonEdge

    def processAlgorithm(self, parameters, context, feedback):
        layer1 = self.parameterAsVectorLayer(parameters, self.LAYER1, context)
        layer2 = self.parameterAsVectorLayer(parameters, self.LAYER2, context)
        # populate temporarily layer to use spatial selection
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                               layer2.fields(), QgsWkbTypes.LineString, layer2.sourceCrs())

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        nFeat = layer2.featureCount()
        processCount = 0
        # loop in layer 2
        for poly2 in layer2.getFeatures():

            if feedback.isCanceled():
                break

            processCount += 1
            feedback.setProgress(100 * float(processCount) / nFeat)

            bbox = poly2.geometry().boundingBox()
            fit = layer1.getFeatures(
                QgsFeatureRequest().setFilterRect(bbox).setSubsetOfAttributes([]))

            # for each polygon in layer 2, get touching polygons in layer 1
            for poly1 in fit:
                # calculate common edge
                edgeGeom = self.getCuttingLimits(poly1, poly2)
                if edgeGeom:
                    edgeFeat = QgsFeature()
                    edgeFeat.setGeometry(edgeGeom)
                    # add to sink
                    sink.addFeature(edgeFeat, QgsFeatureSink.FastInsert)

        del sink

        return {self.OUTPUT: dest_id}
