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
                       QgsWkbTypes, QgsField, QgsSpatialIndex, QgsPointXY)

pluginPath = os.path.split(os.path.split(os.path.dirname(__file__))[0])[0]


class FindCommonEdges(QgsProcessingAlgorithm):
    LULAYER = 'LULAYER'
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
        self.alg_dir = os.path.dirname(__file__)
        icon = QIcon(os.path.join(self.alg_dir, 'joinLinkLanduse.svg'))
        return icon

    def group(self):
        return self.tr('Optain tools')

    def groupId(self):
        return 'optaintools'

    def __init__(self):
        super().__init__()

    def flags(self):
        return super().flags() | QgsProcessingAlgorithm.FlagNoThreading | QgsProcessingAlgorithm.FlagNotAvailableInStandaloneTool

    def initAlgorithm(self, config=None):

        self.addParameter(QgsProcessingParameterVectorLayer(self.LULAYER,
                                                            self.tr('Land use layer'), [QgsProcessing.TypeVectorPolygon]))

        self.addParameter(QgsProcessingParameterVectorLayer(self.LINKLAYER,
                                                            self.tr('Link layer'), [QgsProcessing.TypeVectorLine]))

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('Joined'), QgsProcessing.TypeVectorPolygon))

    def name(self):
        return 'joinlinklanduse'

    def displayName(self):
        return self.tr('Join links to landuse')

    def shortHelpString(self):
        helpStr = """
    					The algorithm adds 'dest_id' field to the landuse map. 
    					<b>Parameters:</b>
    					Land use layer: the layer of the land use [LULAYER]
    					Link layer: the layer with the network [LINKLAYER]
    					<b>Note:</b>
    					none.  
    					"""

        return self.tr(helpStr)

    def lineStartsInPoly(self, line, poly, link_lay,err = 0.001):
        # compute the rings
        #print('poly', poly['id'])
        #print('line', line['id'])
        # get starting vertex
        start_vtx = line.geometry().vertexAt(0)
        #print('start_vtx', start_vtx)
        # check if inside the poly
        if not poly.geometry().contains(QgsGeometry().fromPointXY(QgsPointXY(start_vtx.x(),start_vtx.y()))):
            #print('Point not in poly')
            return False

        # check if  line is connect with some other_lines
        point_bbox = start_vtx.boundingBox().buffered(err)
        #print('point_bbox', point_bbox.asWktPolygon())
        other_lines = link_lay.getFeatures(
            QgsFeatureRequest().setFilterRect(point_bbox))  # .setSubsetOfAttributes(['id']))
        # count selected
        sel_lines = 0
        for other_line in other_lines:
            #print('other_line',other_line['id'])
            sel_lines+=1
            #if other_line.geometry().intersects(point_bbox):
            #    print('Other lines connection')
            #    return False

        # more than one line is connected to the point
        if sel_lines>1: return False

        return True

    def processAlgorithm(self, parameters, context, feedback):
        lu_lay = self.parameterAsVectorLayer(parameters, self.LULAYER, context)
        link_lay = self.parameterAsVectorLayer(parameters, self.LINKLAYER, context)
        #nameFld = self.parameterAsFields(parameters, self.NAME_FLD, context)[0]
        #buf_dist = self.parameterAsDouble(parameters, self.W_FACTOR, context)
        # populate temporarily layer to use spatial selection
        newField = QgsField('dest_cha',QVariant.Int)

        newFields = lu_lay.fields()
        newFields.append(newField)

        (sink, sink_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                               newFields, lu_lay.wkbType(), lu_lay.sourceCrs())

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        nLus = lu_lay.featureCount()
        processCount = 0

        for lu in lu_lay.getFeatures():
            if feedback.isCanceled():
                break

            processCount += 1
            feedback.setProgress(100 * float(processCount) / nLus)
            dest_id = None

            if lu['type'] in ['urml','urld']:
                bbox = lu.geometry().boundingBox()
                link_sel_list = link_lay.getFeatures(
                    QgsFeatureRequest().setFilterRect(bbox))  # .setSubsetOfAttributes(['id']))

                dest_id_list = []
                for link_sel in link_sel_list:
                    # check if link starts inside the polygon
                    if self.lineStartsInPoly(link_sel,lu,link_lay): dest_id_list.append(link_sel['gis_id'])

                if len(dest_id_list)>1:
                    feedback.pushInfo('More than one segments start inside the polygon %s'%(lu['gis_id']))
                elif len(dest_id_list)==1:
                    dest_id = dest_id_list[0]
                else:
                    dest_id = None


            newFeat = QgsFeature(newFields)
            newFeat.setGeometry(lu.geometry())
            newFeat.setAttributes(lu.attributes()+[dest_id])
            # add to sink
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)

        del sink

        return {self.OUTPUT: sink_id}
