from powervariation_sim import *
from numpy import *
import os


def testOdeAlgorithm(a, b, iRange, jRange,
                     width, length, xSpace, ySpace, 
                     n, isStandard, numIterations, mcIterations):
    
    
    numNetworksToPlot = (iRange[1] + 1 - iRange[0]) * (jRange[1] + 1 - jRange[0])
    
    sumNormalisedThroughputTss = zeros([numNetworksToPlot, numIterations])
    sumDataRateTss = zeros([numNetworksToPlot, numIterations])
    sumApPowerTss = zeros([numNetworksToPlot, numIterations])
    sumThroughputTss = zeros([numNetworksToPlot, numIterations])
    sumUtilityTss = zeros([numNetworksToPlot, numIterations])
    
    for i in range(mcIterations):
        print("Running iteration " + str(i+1) + "/" + str(mcIterations))
        networks = createNetworks(a, b, width, length, xSpace, ySpace, n, isStandard)        
        recordings = runPowerVariationAlgorithm(networks, numIterations)
        recordingsToPlot = filter(lambda r: inRange(r.index[0], iRange) and inRange(r.index[1], jRange), recordings)
        
        labels = map(lambda r: 'Network' + str(r.index), recordingsToPlot)
        
        sumNormalisedThroughputTss += array(map(lambda r: r.normalisedThroughput, recordingsToPlot))
        sumDataRateTss += array(map(lambda r: r.dataRate, recordingsToPlot))
        sumApPowerTss += array(map(lambda r: r.apPower, recordingsToPlot))
        sumThroughputTss += array(map(lambda r: multiply(r.dataRate, r.normalisedThroughput), recordingsToPlot))
        sumUtilityTss += array(map(lambda r: r.utility, recordingsToPlot))

        
    avgNormalisedThroughputTss = sumNormalisedThroughputTss / mcIterations
    avgDataRateTss = sumDataRateTss / mcIterations
    avgApPowerTss = sumApPowerTss / mcIterations
    avgThroughputTss = sumThroughputTss / mcIterations
    avgUtilityTss = sumUtilityTss / mcIterations
    
    params = ' cellDim=' + str((a,b)) + ' networkDim=' + str((width, length)) \
                + ' spacing=' + str((xSpace, ySpace)) + ' nodes=' + str(n) \
                + ' iter=' + str(numIterations) + ' mcIter=' + str(mcIterations)
    
    figDir = 'figures/ODE Algorithm'
    if not os.path.isdir(figDir):
        os.makedirs(figDir)
    
    plotTimeseries(avgNormalisedThroughputTss, labels, 'Normalised Throughput', figDir + '/Normalised Throughput' + params)
    plotTimeseries(avgDataRateTss, labels, 'Data Rate', figDir + '/Data Rate' + params)
    plotTimeseries(avgApPowerTss, labels, 'AP Power', figDir + '/AP Power' + params)
    plotTimeseries(avgThroughputTss, labels, 'Throughput', figDir + '/Throughput' + params)
    plotTimeseries(avgUtilityTss, labels, 'Utility', figDir + '/Utility' + params)
        

testOdeAlgorithm(a = 5, b = 4, iRange = [1,3], jRange = [1,2],
                 width = 7, length = 7, xSpace = 7, ySpace = 7,
                 n = 6, isStandard = False, numIterations = 4, mcIterations = 2)

