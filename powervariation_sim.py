from numpy import *
import matplotlib.pyplot as plt
from networkModel import *

    
def plotNetworks(networks, width, length):
    graphWidth = 10.0
    graphHeight = graphWidth * length / width
    plt.figure(figsize=(graphWidth, graphHeight))
    for network in networks:
        plt.plot(map(lambda ms: ms.x, network.mobileStations), map(lambda ms: ms.y, network.mobileStations), 'bo')
        plt.plot(network.accessPoint.x, network.accessPoint.y, 'rs')
    plt.axis([0, width, 0, length])
    plt.show()

def plotTimeseries(timeseries, labels, title):
    time = range(len(timeseries[0]))
    for i in range(len(timeseries)):
        plt.plot(time, timeseries[i], label=labels[i])
    avg = mean(timeseries, axis = 0)
    plt.plot(avg, label='Average', c='black', ls='--', lw=2)
    plt.title(title)
    plt.legend(bbox_to_anchor=(1.05, 1), loc=2)
    plt.show()  

def plotRecordings(recordings):
    normalisedThroughputTss = array(map(lambda r: r.normalisedThroughput, recordings))
    dataRateTss = array(map(lambda r: r.dataRate, recordings))
    apPowerTss = array(map(lambda r: r.apPower, recordings))
    throughputTss = array(map(lambda r: multiply(r.dataRate, r.normalisedThroughput), recordings))        
    labels = map(lambda r: 'Network' + str(r.index), recordings)    
    plotTimeseries(normalisedThroughputTss, labels, 'Normalised Throughput')
    plotTimeseries(dataRateTss, labels, 'Data Rate')
    plotTimeseries(apPowerTss, labels, 'AP Power')
    plotTimeseries(throughputTss, labels, 'Throughput')

def setPowerLevelForAPs(networks, powerLevel):
    for j in range(len(networks)):
      networks[j].accessPoint.p = powerLevel
      networks[j].accessPoint.gr = newApGain(networks[j].accessPoint.p, AP_INITIAL_POWER)

def findAverageThroughput(networks, iRange, jRange):
    networksInRange = filter(lambda n: inRange(n.index[0], iRange) and inRange(n.index[1], jRange), networks)
    throughputs = []
    for network in networksInRange:
        otherNetworks = filter(lambda n: n!= network, networks)
        stationsFromOtherNetworks = reduce(lambda x,y: x+y, map(allStations, otherNetworks))
        throughput = normalisedNetworkThroughput(network, stationsFromOtherNetworks, EXPECTED_PACKET_SIZE)   \
                        * getAverageDataRate20MHZ(network, stationsFromOtherNetworks)
        throughputs.append(throughput)
    return mean(throughputs)
    
def testThroughputUsingPresetPower(networks, powerLevel, iRange, jRange):
    setPowerLevelForAPs(networks, powerLevel)
    return findAverageThroughput(networks, iRange, jRange)   
    
def inRange(number, r):
    return number>= r[0] and number <= r[1]
    
def testAlternativeSchemes(networks, recordings, iRange, jRange):
    
    recordingsInRange = filter(lambda r: inRange(r.index[0], iRange) and inRange(r.index[1], jRange), recordings)
    averagePowerAtEnd = mean(map(lambda r: r.apPower, recordings))
    averageThroughputAtEnd = mean(map(lambda r: r.normalisedThroughput[-1] * r.dataRate[-1], recordingsInRange))
    maxPowerAtEnd = max(map(lambda r: r.apPower[-1], recordings))
    #Set all the APs to the average power value and test the average throughput at this point
    avgThroughputUsingAvgPower= testThroughputUsingPresetPower(networks, averagePowerAtEnd, iRange, jRange)
    avgThroughputUsingMaxPower = testThroughputUsingPresetPower(networks, maxPowerAtEnd, iRange, jRange)

    print "Average throughput (for the 6 central networks) using power mgmt algorithm:", averageThroughputAtEnd
    print "Average throughput (for the 6 central networks) with all the APs using the average power from the power mgmt algorithm(",     \
            averagePowerAtEnd,"):", avgThroughputUsingAvgPower
    print "Average throughput (for the 6 central networks) with all the APs using the maximum power from the power mgmt algorithm(",    \
            maxPowerAtEnd,"):", avgThroughputUsingMaxPower
    print "Need to double check that the average throughput using average and max power is calculated for the correct stations"\
            +", as the values seem somewhat too optimistic"
        
def testPowerVariation(networks, iPlotRange, jPlotRange, numIterations):
    #just a temporary function to see how changing interfering AP power affects the model
    recordings = []
    for network in networks:
        recordings.append(Recording(network.index))

    for i in range(numIterations):        
        for j in range(len(networks)):
            otherNetworks = networks[:j] + networks[j+1:]
            stationsFromOtherNetworks = reduce(lambda x,y: x+y, map(allStations, otherNetworks))
            S = normalisedNetworkThroughput(networks[j], stationsFromOtherNetworks, EXPECTED_PACKET_SIZE)
            r = getAverageDataRate20MHZ(networks[j], stationsFromOtherNetworks)
            recordings[j].addDataPoint(networks[j].accessPoint.p, networks[j].accessPoint.gr, S, r)
        for j in range(len(networks)):
            otherNetworks = networks[:j] + networks[j+1:]
            stationsFromOtherNetworks = reduce(lambda x,y: x+y, map(allStations, otherNetworks))
            networks[j].accessPoint.p = newApPower(networks[j], stationsFromOtherNetworks)
            networks[j].accessPoint.gr = newApGain(networks[j].accessPoint.p, AP_INITIAL_POWER)
    
    recordingsToPlot = filter(lambda r: inRange(r.index[0], iPlotRange) and inRange(r.index[1], jPlotRange), recordings)
    plotRecordings(recordingsToPlot)
    testAlternativeSchemes(networks, recordings, iPlotRange, jPlotRange)
    
def oldnewApPower(network, interferingStations):
    return network.accessPoint.p + POWER_INCREMENT
    
def newApPower(network, interferingStations):
    #parameters
    powerGain=0.15 #temporary gain factor to avoid modifying global variables for now
    powerExponent = 0.2 #the larger this value the larger focus on minimizng power
    referencePowerDecay = 0.78
    maxPower=1
    maxPowerBackoff=0.9
    referenceBackoffOnMaxPowerHit=0.8
    minPower=0.05
    S = normalisedNetworkThroughput(network, interferingStations, EXPECTED_PACKET_SIZE)
    r = getAverageDataRate20MHZ(network, interferingStations)
    cap=S*r/power(network.accessPoint.p,powerExponent)
#    cap=S*r
    #first iteration of the algorithm
    if network.accessPoint.memory.prevCap == 0:
         network.accessPoint.memory.prevCap = cap
         network.accessPoint.memory.maxCap = cap+15
         network.accessPoint.memory.iterations = 1
         return network.accessPoint.p + POWER_INCREMENT
     #subsequent iterations
    #update maximum capacity
    if cap>network.accessPoint.memory.maxCap:
        network.accessPoint.memory.maxCap = cap

#    if cap<((network.accessPoint.memory.prevCap+network.accessPoint.memory.maxCap)/capRatio or cap < network.accessPoint.memory.prevCap):
    if cap<(network.accessPoint.memory.maxCap):
        #reduce the reference power only if power has been increased for two consecutive cycles
        if network.accessPoint.memory.prevState==1:
            network.accessPoint.memory.maxCap= power( referencePowerDecay,  (network.accessPoint.memory.maxCap - cap)/ network.accessPoint.memory.maxCap ) * network.accessPoint.memory.maxCap
        network.accessPoint.memory.prevState=1
        powerInc = powerGain*abs((network.accessPoint.memory.maxCap-cap)/network.accessPoint.memory.maxCap)
        #capacity reduced
        newApPower = network.accessPoint.p+powerInc
    else:
        network.accessPoint.memory.iterations = network.accessPoint.memory.iterations +1
        powerInc = powerGain*power(0.7, network.accessPoint.memory.iterations)
        network.accessPoint.memory.prevState=-1
        newApPower = network.accessPoint.p-powerInc
#resetting maximum capacity every n cycles - currently unused
    if network.accessPoint.memory.iterations==20:
        network.accessPoint.memory.iterations=5
        network.accessPoint.memory.maxCap=cap*1.2
  #      capacity unchanged
    network.accessPoint.memory.prevCap=cap 
    if newApPower>maxPower:
        network.accessPoint.memory.prevState=0
        newApPower = maxPowerBackoff
        network.accessPoint.memory.maxCap=network.accessPoint.memory.maxCap*referenceBackoffOnMaxPowerHit
    elif newApPower<=0:
        newApPower = minPower                   
    return newApPower
    

def newApGain(newApPower, initialApPower):
    return newApPower / initialApPower
    
    
def powerVariationSim():
    a = 5
    b = 4
    width = 7
    length = 7
    xSpace = 7
    ySpace = 7
    n = 6
    isStandard = True
    numIterations = 60
    
    networks = []
    for i in range(a):
        for j in range(b):
            xOffset = i * (width + xSpace)
            yOffset = j * (length + ySpace)
            if isStandard:
                network = Network((i,j), xOffset, yOffset, width, length, n, seed = i*b + j)
            else:
                network = Network((i,j), xOffset, yOffset, width, length, n)
            networks.append(network)
    plotNetworks(networks, (width + xSpace) * a, (length + ySpace) * b)

    testPowerVariation(networks, [1,2], [1,3], numIterations)
    
def congestionPlot():
    probList = []
    xaxis = []
    network1 = Network((0,0), 0, 0, 8, 8, 0)
    network2 = Network((1,0), 16, 0, 8, 8, 0)
    for i in range(40):
        network1.addRandomMobileStations(2)
        network2.addRandomMobileStations(2)
        probList.append(probabilityOfExactlyOneTransmission(network1, allStations(network2)))
        xaxis.append(i*2)
    plt.plot(xaxis, probList)
    plt.show()
        
congestionPlot()
powerVariationSim()




