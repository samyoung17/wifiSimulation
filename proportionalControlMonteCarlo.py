# -*- coding: utf-8 -*-
"""
Created on Wed Apr 27 19:32:17 2016

@author: pk0300
"""
import csv
from powervariation_sim import *
from numpy import *
import os

def testProportionalControlAlgorithm(a, b, iRange, jRange,
                     width, length, xSpace, ySpace, 
                     n, isStandard, numIterations, mcIterations, maxPower, powerCost):
    numNetworksToPlot = (iRange[1] + 1 - iRange[0]) * (jRange[1] + 1 - jRange[0])
    
    sumNormalisedThroughputTss = zeros([numNetworksToPlot, numIterations])
    sumDataRateTss = zeros([numNetworksToPlot, numIterations])
    sumApPowerTss = zeros([numNetworksToPlot, numIterations])
    sumThroughputTss = zeros([numNetworksToPlot, numIterations])
    sumUtilityTss = zeros([numNetworksToPlot, numIterations])
    maxPs = []
    avgPs = []
    for i in range(mcIterations):
        print("Running iteration " + str(i+1) + "/" + str(mcIterations))
        networks = createNetworks(a, b, width, length, xSpace, ySpace, n, isStandard)        
        recordings = runPowerVariationAlgorithmControl(networks, numIterations, maxPower, powerCost)
        recordingsToPlot = filter(lambda r: inRange(r.index[0], iRange) and inRange(r.index[1], jRange), recordings)
        
        labels = map(lambda r: 'Network' + str(r.index), recordingsToPlot)
        
        sumNormalisedThroughputTss += array(map(lambda r: r.normalisedThroughput, recordingsToPlot))
        sumDataRateTss += array(map(lambda r: r.dataRate, recordingsToPlot))
        sumApPowerTss += array(map(lambda r: r.apPower, recordingsToPlot))
        sumThroughputTss += array(map(lambda r: multiply(r.dataRate, r.normalisedThroughput), recordingsToPlot))
        maxPower = max (map(lambda r: r.apPower, recordingsToPlot))
        avgPower = mean(map(lambda r: r.apPower, recordingsToPlot))
        maxPowerThroughput=testThroughputUsingPresetPower(networks, maxPower, [1,3], [1,2])
        avgPowerThroughput=testThroughputUsingPresetPower(networks, maxPower, [1,3], [1,2])
        maxPs.append(maxPowerThroughput)
        avgPs.append(avgPowerThroughput)
    avgNormalisedThroughputTss = sumNormalisedThroughputTss / mcIterations
    avgDataRateTss = sumDataRateTss / mcIterations
    avgApPowerTss = sumApPowerTss / mcIterations
    avgThroughputTss = sumThroughputTss / mcIterations
    avgPs = mean(avgPs)
    maxPs = mean(maxPs)
    with open('staticpowerthroughput.csv', 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows('cost', powerCost, 'max power', maxPower, 'avgPthroughput', avgPs, 'maxPthroughput', maxPs)
    
    params = ' cellDim=' + str((a,b)) + ' networkDim=' + str((width, length)) \
                + ' spacing=' + str((xSpace, ySpace)) + ' nodes=' + str(n) \
                + ' iter=' + str(numIterations) + ' powerCost=' + str(powerCost) + ' maxPower=' + str(maxPower) + ' mcIter=' + str(mcIterations) + '.png'
    
    figDir = 'figures/ODE Algorithm'
    if not os.path.isdir(figDir):
        os.makedirs(figDir)
    
    plotTimeseries(avgNormalisedThroughputTss, labels, 'Normalised Throughput', figDir + '/Normalised Throughput' + params)
    plotTimeseries(avgDataRateTss, labels, 'Data Rate', figDir + '/Data Rate' + params)
    plotTimeseries(avgApPowerTss, labels, 'AP Power', figDir + '/AP Power' + params)
    plotTimeseries(avgThroughputTss, labels, 'Throughput', figDir + '/Throughput' + params)

def testProportionalControlParameters (maxPowerInitial, maxPowerFinal, maxPowerStep, powerCostInitial, powerCostFinal, powerCostStep, numIterations, mcIterations):
    maxPower=maxPowerInitial
    for i in range(int((maxPowerFinal-maxPowerInitial)/maxPowerStep)):
        powerCost = powerCostInitial
        for j in range (int((powerCostFinal-powerCostInitial)/powerCostStep)):
                testProportionalControlAlgorithm(a = 5, b = 4, iRange = [1,3], jRange = [1,2],
                                                     width = 7, length = 7, xSpace = 7, ySpace = 7,
                                                     n = 6, isStandard = False, numIterations=numIterations, mcIterations=mcIterations, maxPower=maxPower, powerCost=powerCost)
                powerCost = powerCost + powerCostStep
        maxPower = maxPower + maxPowerStep
 
testProportionalControlParameters(0.5, 0.8, 0.1, 0, 0.2, 0.1, 5, 2)       