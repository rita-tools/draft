# -*- coding: utf-8 -*-

"""
***************************************************************************
    join_nodes_links.py
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

from PyQt5.QtCore import QCoreApplication, QVariant
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
                       QgsWkbTypes, QgsField)

pluginPath = os.path.split(os.path.split(os.path.dirname(__file__))[0])[0]


class FindCommonEdges(QgsProcessingAlgorithm):
    NODELAYER = 'NODELAYER'
    LINKLAYER = 'LINKLAYER'
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

        self.addParameter(QgsProcessingParameterVectorLayer(self.NODELAYER,
                                                            self.tr('First layer'), [QgsProcessing.TypeVectorPoint]))

        self.addParameter(QgsProcessingParameterVectorLayer(self.LINKLAYER,
                                                            self.tr('Second layer'), [QgsProcessing.TypeVectorLine]))

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('Joined'), QgsProcessing.TypeVectorPoint))

    def name(self):
        return 'joinnodeslinks'

    def displayName(self):
        return self.tr('Join nodes to links')

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
        node_lay = self.parameterAsVectorLayer(parameters, self.NODELAYER, context)
        link_lay = self.parameterAsVectorLayer(parameters, self.LINKLAYER, context)
        #nameFld = self.parameterAsFields(parameters, self.NAME_FLD, context)[0]
        #buf_dist = self.parameterAsDouble(parameters, self.W_FACTOR, context)
        # populate temporarily layer to use spatial selection
        newField = QgsField('link_id',QVariant.Int)

        buf_dist = 1000

        newFields = node_lay.fields()
        newFields.append(newField)

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                               newFields, node_lay.wkbType(), node_lay.sourceCrs())

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        nFeat = node_lay.featureCount()
        processCount = 0
        # loop in layer 2
        for node in node_lay.getFeatures():

            if feedback.isCanceled():
                break

            processCount += 1
            feedback.setProgress(100 * float(processCount) / nFeat)

            bbox = node.geometry().buffer(buf_dist,10).boundingBox()
            link_sel = link_lay.getFeatures(
                QgsFeatureRequest().setFilterRect(bbox))#.setSubsetOfAttributes(['id']))

            # for each polygon in layer 2, get touching polygons in layer 1
            max_dist = 2*buf_dist
            closestLinkId = None
            for l in link_sel:
                # calculate distance
                dist = node.geometry().distance(l.geometry())
                #print('dist',dist)
                if dist<max_dist:
                    max_dist = dist
                    closestLinkId = l['id']
                    #print('closestLinkId', closestLinkId)

            print('closestLinkId', closestLinkId, 'distance',max_dist)
            newFeat = QgsFeature(newFields)
            newFeat.setGeometry(node.geometry())
            newFeat.setAttributes(node.attributes()+[closestLinkId])
            # add to sink
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)

        del sink

        return {self.OUTPUT: dest_id}
