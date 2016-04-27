from powervariation_sim import *
from numpy import *


def testOdeAlgorithm():
    a = 5
    b = 4
    iRange = [1,3]
    jRange = [1,2]
    width = 7
    length = 7 
    xSpace = 7
    ySpace = 7
    n = 6
    isStandard = False
    numIterations = 10
    mcIterations = 2
    
    numNetworksToPlot = (iRange[1] + 1 - iRange[0]) * (jRange[1] + 1 - jRange[0])
    sumThroughputTss = zeros([numNetworksToPlot, numIterations])
    for i in range(mcIterations):
        print("Running iteration " + str(i+1) + "/" + str(mcIterations))
        networks = createNetworks(a, b, width, length, xSpace, ySpace, n, isStandard)        
        recordings = runPowerVariationAlgorithm(networks, numIterations)
        recordingsToPlot = filter(lambda r: inRange(r.index[0], iRange) and inRange(r.index[1], jRange), recordings)
        labels = map(lambda r: 'Network' + str(r.index), recordingsToPlot)
        throughputTss = array(map(lambda r: multiply(r.dataRate, r.normalisedThroughput), recordingsToPlot)) 
        sumThroughputTss = add(sumThroughputTss, throughputTss)
        
    avgThroughputTss = sumThroughputTss / mcIterations
    plotTimeseries(avgThroughputTss, labels, 'Normalised Throughput')
        

testOdeAlgorithm()