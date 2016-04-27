# -*- coding: utf-8 -*-
"""
Created on Wed Apr 27 19:32:17 2016

@author: pk0300
"""
from powervariation_sim import *
from numpy import *


def testProportionalControlAlgorithm(a, b, iRange, jRange,
                     width, length, xSpace, ySpace, 
                     n, isStandard, numIterations, mcIterations, maxPower, powerCost):
    
    
    numNetworksToPlot = (iRange[1] + 1 - iRange[0]) * (jRange[1] + 1 - jRange[0])
    sumThroughputTss = zeros([numNetworksToPlot, numIterations])
    for i in range(mcIterations):
        print("Running iteration " + str(i+1) + "/" + str(mcIterations))
        networks = createNetworks(a, b, width, length, xSpace, ySpace, n, isStandard)        
        recordings = runPowerVariationAlgorithmControl(networks, numIterations, maxPower, powerCost)
        recordingsToPlot = filter(lambda r: inRange(r.index[0], iRange) and inRange(r.index[1], jRange), recordings)
        labels = map(lambda r: 'Network' + str(r.index), recordingsToPlot)
        throughputTss = array(map(lambda r: multiply(r.dataRate, r.normalisedThroughput), recordingsToPlot)) 
        sumThroughputTss = add(sumThroughputTss, throughputTss)
        
    avgThroughputTss = sumThroughputTss / mcIterations
    title = 'Throughput - P control'
    plotName = title + ' cellDim=' + str((a,b)) + ' networkDim=' + str((width, length)) \
                + ' spacing=' + str((xSpace, ySpace)) + ' nodes=' + str(n) \
                + ' iter=' + str(numIterations) + ' mcIter' + str(mcIterations)
    plotTimeseries(avgThroughputTss, labels, 'Normalised Throughput', 'figures/' + plotName)
    
testProportionalControlAlgorithm(a = 5, b = 4, iRange = [1,3], jRange = [1,2],
             width = 7, length = 7, xSpace = 7, ySpace = 7,
             n = 6, isStandard = False, numIterations = 10, mcIterations = 2, maxPower=0.5, powerCost=0.3)