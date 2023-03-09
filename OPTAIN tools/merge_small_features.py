# -*- coding: utf-8 -*-

"""
***************************************************************************
    merge_small_features.py
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
freely inspired by EliminateSelection.py (C) 2017 by Bernhard Ströbl bernhard.stroebl@jena.de
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
                       QgsProcessingParameterNumber, QgsWkbTypes)

pluginPath = os.path.split(os.path.split(os.path.dirname(__file__))[0])[0]


class MergeSmallFeatures(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    NAME_FLD = 'NAME_FLD'
    GROUP_FLD = 'GROUP_FLD'
    PHI_FLD = 'PHI_FLD'
    AREA_LIM = 'AREA_LIM'
    W_FACTOR = 'W_FACTOR'
    TOLL = 'TOLL'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return MergeSmallFeatures()

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

        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT,
                                                            self.tr('Input layer'), [QgsProcessing.TypeVectorPolygon]))

        self.addParameter(
            QgsProcessingParameterNumber(self.AREA_LIM, self.tr('Area limits'), QgsProcessingParameterNumber.Double))

        self.addParameter(QgsProcessingParameterField(self.NAME_FLD, self.tr('Name field'), None, self.INPUT,
                                                      QgsProcessingParameterField.Any))

        self.addParameter(QgsProcessingParameterField(self.GROUP_FLD, self.tr('Group field'), None, self.INPUT,
                                                      QgsProcessingParameterField.Any))

        self.addParameter(QgsProcessingParameterField(self.PHI_FLD, self.tr('PHI field'), None, self.INPUT,
                                                      QgsProcessingParameterField.Numeric))

        self.addParameter(
            QgsProcessingParameterNumber(self.W_FACTOR, self.tr('Weight factor'), QgsProcessingParameterNumber.Double))

        #self.addParameter(
        #    QgsProcessingParameterNumber(self.TOLL, self.tr('Tollerance'), QgsProcessingParameterNumber.Double))

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('Merged'), QgsProcessing.TypeVectorPolygon))
        # self.addParameter(
        #     QgsProcessingParameterVectorLayer(self.OUTPUT, self.tr('Merged'), QgsProcessing.TypeVectorPolygon))

    def name(self):
        return 'mergesmallfeatures'

    def displayName(self):
        return self.tr('Merge small features')

    def getSmallest_OLD(self,  inLayer, limArea,unresolvedList=[]):
        minFeature = None
        minArea = limArea
        nOfMin = 0
        dummy=0
        dummy2=0
        for aFeat in inLayer.getFeatures():
            dummy+=1
            if aFeat.id() not in unresolvedList:
                dummy2+=1
                featArea = aFeat.geometry().area()
                #print('id:',aFeat.id(),'area:',featArea)
                if featArea < limArea:
                    nOfMin += 1

                if featArea < minArea:
                    minArea = featArea
                    minFeature = aFeat

        print('n. of feats',inLayer.featureCount(),'dummy',dummy,'dummy2',dummy2,'n.unres',len(unresolvedList),'nOfMin',nOfMin)
        return minFeature,nOfMin

    def getSmallest(self,  inLayer, limArea,unresolvedList=[]):
        minFeature = None
        request = QgsFeatureRequest().setFilterExpression('$area < %s '%limArea)
        clause = QgsFeatureRequest.OrderByClause('$area')
        orderby = QgsFeatureRequest.OrderBy([clause])
        request.setOrderBy(orderby)
        # get the first that is not in unresolvedList
        selFeatures = inLayer.getFeatures(request)
        #print('selFeatures', selFeatures)

        n=0
        for aFeat in selFeatures:
            n+=1
            #print('aFeat', aFeat.id())
            if aFeat.id() not in unresolvedList:
                featArea = aFeat.geometry().area()
                minFeature = aFeat
                break
                #print('featArea',featArea)
                #if featArea < minArea:
                #    minArea = featArea
                #    minFeature = aFeat

        #print('n. of feats',inLayer.featureCount(),'dummy',dummy,'dummy2',dummy2,'n.unres',len(unresolvedList),'nOfMin',nOfMin)
        nOfMin = len(list(selFeatures))+n
        #print('nOfMin', nOfMin)
        #selFeatures.rewind()

        return minFeature,nOfMin

    def cleanZeroRing(self, geom):
        if not geom.isMultipart():
            polygon = geom.asPolygon()
            filledGeometry = QgsGeometry.fromPolygonXY([polygon[0]])  # add first main ring polygon
            for p in polygon[1:]:
                if QgsGeometry.fromPolygonXY([p]).area()>0:
                    filledGeometry.addRing(p)
        else:
            multipolyg = geom.asMultiPolygon()
            filledGeometry = QgsGeometry()  # multipolygon
            for polygon in multipolyg:
                filledGeometry.addPartGeometry(self.cleanZeroRing(polygon))

        return filledGeometry

    def processAlgorithm(self, parameters, context, feedback):
        inLayer = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        nameFld = self.parameterAsFields(parameters, self.NAME_FLD, context)[0]
        groupFld = self.parameterAsFields(parameters, self.GROUP_FLD, context)[0]
        phiFld = self.parameterAsFields(parameters, self.PHI_FLD, context)[0]
        limArea = self.parameterAsDouble(parameters, self.AREA_LIM, context)
        wFactor = self.parameterAsDouble(parameters, self.W_FACTOR, context)
        #tollerance = self.parameterAsDouble(parameters, self.TOLL, context)

        # populate temporarily layer to use spatial selection
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                               inLayer.fields(), QgsWkbTypes.MultiPolygon, inLayer.sourceCrs())
        #inLayer.wkbType()
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))


        for aFeat in inLayer.getFeatures():
            sink.addFeature(aFeat, QgsFeatureSink.FastInsert)

        del sink

        unresolvedList = []
        processLayer = QgsProcessingUtils.mapLayerFromString(dest_id, context)

        minFeat, smallAreaCount = self.getSmallest(processLayer, limArea, unresolvedList)

        feedback.pushInfo(self.tr('Num. of small features to be processed: %s') % smallAreaCount)

        # while a feature with area lower then limit
        processCount=0
        while minFeat:
            if feedback.isCanceled():
                break

            processCount+=1
            if smallAreaCount>0:
                feedback.setProgress(100 * float(processCount) / smallAreaCount)
            else:
                print('minFeat',minFeat)
            #feedback.pushInfo(self.tr('Processing feature fid=%s with area %s')%(minFeat['fid'],minFeat.geometry().area()))
            # get surrounding features
            # Delete all features to eliminate in processLayer

            processLayer.startEditing()

            #feedback.pushInfo(self.tr('Data provider caps: %s')%processLayer.dataProvider().capabilitiesString())

            minPhi = minFeat[phiFld]

            minGeom = minFeat.geometry()
            bbox = minGeom.boundingBox()
            fit = processLayer.getFeatures(
                QgsFeatureRequest().setFilterRect(bbox).setSubsetOfAttributes([]))

            selFeat = QgsFeature()

            # use prepared geometries for faster intersection tests
            engine = QgsGeometry.createGeometryEngine(minGeom.constGet())
            engine.prepareGeometry()

            selValue = -1
            mergeWithFid = None

            while fit.nextFeature(selFeat):
                selGeom = selFeat.geometry()

                if engine.intersects(selGeom.constGet()):
                    # We have a candidate
                    iGeom = minGeom.intersection(selGeom)

                    if not iGeom:
                        continue

                    testValue = iGeom.length()
                    # if the two features belong to the same group, enhance the test value
                    if selFeat[groupFld]==minFeat[groupFld]:
                        testValue=testValue*wFactor

                    # if the merged feature has an area > (1+tollerance)*limarea
                    #newGeom = selGeom.combine(geom2Eliminate)

                    if (testValue>selValue)\
                        and (selFeat.id()!=minFeat.id()):
                        #and (newGeom.area()<=(1+tollerance)*limArea):

                        selValue = testValue
                        #feedback.pushInfo('selFeat attr: %s' % selFeat.attributes())
                        mergeWithFeat = QgsFeature(processLayer.getFeature(selFeat.id()))
                        mergeWithFid = selFeat.id()
                        mergeWithPhi = mergeWithFeat[phiFld]
                        mergeWithGeom = QgsGeometry(selGeom)


                    # if (-1 != selValue) and (selFeat.id()!=minFeat.id()):
                    #     useThis = True
                    #     if useThis:
                    #         mergeWithFid = selFeat.id()
                    #         mergeWithGeom = QgsGeometry(selGeom)

            # End while fit

            if mergeWithFid is not None:
                # A successful candidate
                newGeom = mergeWithGeom.combine(minGeom)
                #newGeom = self.cleanZeroRing(newGeom)
                if mergeWithGeom.lastError():
                    feedback.error(
                        self.tr('merge %s (smallest) with %s return error: %s') %
                                (minFeat[nameFld], mergeWithFeat[nameFld],mergeWithGeom.lastError()),
                        True)

                #feedback.pushInfo('mergeWithFeat attr: %s'%mergeWithFeat.attributes())

                #feedback.pushInfo(
                #    self.tr('merge %s (smallest) with %s') % (minFeat[nameFld], mergeWithFeat[nameFld]))

                #if minFeat.id() == mergeWithFid:
                #    break

                #feedback.pushInfo(
                #    self.tr('Old area %s replaced with new area %s') % (mergeWithGeom.area(), newGeom.area()))
                #feedback.pushInfo(self.tr('Merge with %s') % mergeWithFid)
                # get attributes from the largest feature
                if mergeWithGeom.area()>minGeom.area():
                    newFeat = QgsFeature(mergeWithFeat)
                else:
                    newFeat = QgsFeature(minFeat)

                # update geometry with the merge result
                newFeat.setGeometry(newGeom)

                # calculate new phi
                newPhi = (mergeWithPhi*mergeWithFeat.geometry().area()+minPhi*minFeat.geometry().area())/newGeom.area()

                newFeat[phiFld]=newPhi

                #feedback.pushInfo(
                #    self.tr('New feature with area %s') % (newFeat.geometry().area()))

                if not processLayer.deleteFeatures([minFeat.id(),mergeWithFid]):
                    feedback.error(
                        self.tr('Could not delete geometry of feature with name %s')%minFeat[nameFld])

                if not processLayer.addFeature(newFeat):
                    feedback.error(self.tr('Could not add new feature with name %s')%mergeWithFeat[nameFld])

                # if processLayer.changeGeometry(mergeWithFid, newGeom):
                #     feedback.pushInfo(self.tr('New geometry area is %s')%(processLayer.getFeature(mergeWithFid).geometry().area()))
                #     madeProgress = True
                # else:
                #     feedback.pushInfo(self.tr('Could not replace geometry of feature with id {0}').format(mergeWithFid))
            else:
                feedback.pushInfo(self.tr('Could not resolve feature with name %s')%minFeat[nameFld])
                unresolvedList.append(minFeat.id())

            # save changes
            if not processLayer.commitChanges():
                errList = processLayer.commitErrors()
                feedback.pushInfo('\n'.join(errList))
                #raise QgsProcessingException(self.tr('Could not commit changes'))

            # calculate new minFeat
            minFeat,smallAreaCount = self.getSmallest(processLayer, limArea,unresolvedList)
            #print('minfeat',minFeat,'n.smallareas',smallAreaCount,'process count',processCount)

        #
        # algResults = processing.run("native:deleteholes", {
        #                                     'INPUT': processLayer,
        #                                     'MIN_AREA': 0,
        #                                     'OUTPUT': 'TEMPORARY_OUTPUT'},
        #                             context=context, feedback=feedback, is_child_algorithm=True)
        #
        # algResults = processing.run("native:simplifygeometries", {
        #                                 'INPUT': algResults['OUTPUT'],
        #                                 'METHOD': 2, 'TOLERANCE': 1,
        #                                 'OUTPUT': 'TEMPORARY_OUTPUT'},
        #                             context=context, feedback=feedback, is_child_algorithm=True)
        #
        # dest_id = algResults['OUTPUT']

        return {self.OUTPUT: dest_id}
