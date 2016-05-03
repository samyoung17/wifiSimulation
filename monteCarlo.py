from powervariation_sim import *
from numpy import *
import os
import sys

def testOdeAlgorithm(a, b, iRange, jRange,
                     width, length, xSpace, ySpace, 
                     c,
                     n, isStandard, numIterations, mcIterations):
    
    params = ' cellDim=' + str((a,b)) + ' networkDim=' + str((width, length)) \
                + ' spacing=' + str((xSpace, ySpace)) + ' nodes=' + str(n) \
                + ' iter=' + str(numIterations) + ' mcIter=' + str(mcIterations) \
                + ' c=' + str(c)
                
    print("Testing ODE Algorithm with parameters:" + params)
    
    numNetworksToPlot = (iRange[1] + 1 - iRange[0]) * (jRange[1] + 1 - jRange[0])
    
    sumNormalisedThroughputTss = zeros([numNetworksToPlot, numIterations])
    sumDataRateTss = zeros([numNetworksToPlot, numIterations])
    sumApPowerTss = zeros([numNetworksToPlot, numIterations])
    sumThroughputTss = zeros([numNetworksToPlot, numIterations])
    sumUtilityTss = zeros([numNetworksToPlot, numIterations])
    
    for i in range(mcIterations):
        print("Running iteration " + str(i+1) + "/" + str(mcIterations))
        networks = createNetworks(a, b, width, length, xSpace, ySpace, n, isStandard)        
        recordings = runPowerVariationAlgorithm(networks, numIterations, c)
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
    
    figDir = 'figures/ODE Algorithm/' + params
    os.makedirs(figDir)
    
    plotTimeseries(avgNormalisedThroughputTss, labels, 'Normalised Throughput', figDir + '/Normalised Throughput.png')
    plotTimeseries(avgDataRateTss, labels, 'Data Rate', figDir + '/Data Rate.png')
    plotTimeseries(avgApPowerTss, labels, 'AP Power', figDir + '/AP Power.png')
    plotTimeseries(avgThroughputTss, labels, 'Throughput', figDir + '/Throughput.png')
    plotTimeseries(avgUtilityTss, labels, 'Utility', figDir + '/Utility.png')
        

if __name__ == '__main__':
    if len(sys.argv) != 8:
        raise ValueError('Not enough arguments, expected [width, length, xSpace, ySpace, nodes, numIter, mcIter], got ' + str(sys.argv[1:]))
    width = float(sys.argv[1])
    length = float(sys.argv[2])
    xSpace = float(sys.argv[3])
    ySpace = float(sys.argv[4])
    n = int(sys.argv[5])
    numIter = int(sys.argv[6])
    mcIter = int(sys.argv[7])
    
    cValues = [20, 30, 25, 15, 35, 40]
    for c in cValues:
        testOdeAlgorithm(a = 5, b = 4, iRange = [1,3], jRange = [1,2],
                     width = width, length = length, xSpace = xSpace, ySpace = ySpace,
                     c = c,
                     n = n, isStandard = False, numIterations = numIter, mcIterations = mcIter)

