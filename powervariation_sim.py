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

def plotTimeseries(timeseries, labels, title, fileName = None):
    time = range(len(timeseries[0]))
    for i in range(len(timeseries)):
        plt.plot(time, timeseries[i], label=labels[i])
    avg = mean(timeseries, axis = 0)
    plt.plot(avg, label='Average', c='black', ls='--', lw=2)
    plt.title(title)
    lgd = plt.legend(bbox_to_anchor=(1.05, 1), loc=2)
    if fileName != None:
        plt.savefig(fileName, bbox_extra_artists=(lgd,), bbox_inches='tight')
    else:
        plt.show()
    plt.clf()
    

def plotRecordings(recordings):
    normalisedThroughputTss = array(map(lambda r: r.normalisedThroughput, recordings))
    dataRateTss = array(map(lambda r: r.dataRate, recordings))
    apPowerTss = array(map(lambda r: r.apPower, recordings))
    throughputTss = array(map(lambda r: multiply(r.dataRate, r.normalisedThroughput), recordings))      
    utilityTss = array(map(lambda r: r.utility, recordings))
    labels = map(lambda r: 'Network' + str(r.index), recordings)  
    plotTimeseries(normalisedThroughputTss, labels, 'Normalised Throughput')
    plotTimeseries(dataRateTss, labels, 'Data Rate')
    plotTimeseries(apPowerTss, labels, 'AP Power')
    plotTimeseries(throughputTss, labels, 'Throughput')
    plotTimeseries(utilityTss, labels, 'Utility')

def setPowerLevelForAPs(networks, powerLevel):
    for j in range(len(networks)):
      networks[j].accessPoint.p = powerLevel
      networks[j].accessPoint.snrFloor = newApSnrFloor(powerLevel)

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

def runPowerVariationAlgorithm(networks, numIterations, c = 20):
    recordings = []
    for network in networks:
        recordings.append(Recording(network.index))
        
    for i in range(numIterations):        
        for j in range(len(networks)):
            otherNetworks = networks[:j] + networks[j+1:]
            stationsFromOtherNetworks = reduce(lambda x,y: x+y, map(allStations, otherNetworks))
            S = normalisedNetworkThroughput(networks[j], stationsFromOtherNetworks, EXPECTED_PACKET_SIZE)
            r = getAverageDataRate20MHZ(networks[j], stationsFromOtherNetworks)
            u = networks[j].accessPoint.memory.prevU
            recordings[j].addDataPoint(networks[j].accessPoint.p, networks[j].accessPoint.gr, S, r, u)
        for j in range(len(networks)):
            otherNetworks = networks[:j] + networks[j+1:]
            stationsFromOtherNetworks = reduce(lambda x,y: x+y, map(allStations, otherNetworks))
            networks[j].accessPoint.p = newApPower(networks[j], stationsFromOtherNetworks, c)
            networks[j].accessPoint.snrFloor = newApSnrFloor(networks[j].accessPoint.p)
            
    return recordings
    
def runPowerVariationAlgorithmControl(networks, numIterations, maxPower, powerCost):
    recordings = []
    for network in networks:
        recordings.append(Recording(network.index))
        
    for i in range(numIterations):        
        for j in range(len(networks)):
            otherNetworks = networks[:j] + networks[j+1:]
            stationsFromOtherNetworks = reduce(lambda x,y: x+y, map(allStations, otherNetworks))
            S = normalisedNetworkThroughput(networks[j], stationsFromOtherNetworks, EXPECTED_PACKET_SIZE)
            r = getAverageDataRate20MHZ(networks[j], stationsFromOtherNetworks)
            u = networks[j].accessPoint.memory.prevU
            recordings[j].addDataPoint(networks[j].accessPoint.p, networks[j].accessPoint.gr, S, r, u)
        for j in range(len(networks)):
            otherNetworks = networks[:j] + networks[j+1:]
            stationsFromOtherNetworks = reduce(lambda x,y: x+y, map(allStations, otherNetworks))
            networks[j].accessPoint.p = newApPowerControl(networks[j], stationsFromOtherNetworks, maxPower, powerCost)
            networks[j].accessPoint.snrFloor = newApSnrFloor(networks[j].accessPoint.p)
            
    return recordings  
    

def oldnewApPower(network, interferingStations):
    return network.accessPoint.p + POWER_INCREMENT

def newApPowerControl(network, interferingStations, maxPower, powerExponent):
    #parameters
    powerGain=0.15 #temporary gain factor to avoid modifying global variables for now
    powerExponent = 0.3 #the larger this value the larger focus on minimizng power
    referenceDecay = 0.8
    maxPowerBackoff=0.95*maxPower
    referenceBackoffOnMaxPowerHit=0.9
    minPower=0.05
    maxCycles=20
    initialRef=65
    powerDecay=0.7
    S = normalisedNetworkThroughput(network, interferingStations, EXPECTED_PACKET_SIZE)
    r = getAverageDataRate20MHZ(network, interferingStations)
    U=S*r/power(network.accessPoint.p,powerExponent)
    
    ref = network.accessPoint.memory.uRef
    #first iteration of the algorithm
    if network.accessPoint.memory.prevUref == 0:
         network.accessPoint.memory.prevUref = U
         network.accessPoint.memory.uRef = initialRef
         network.accessPoint.memory.iterations = 1
     #subsequent iterations

    if U<ref:
        if network.accessPoint.memory.prevState==1:
            #reduce reference only if power has been increased for two consecutive cycles
            network.accessPoint.memory.uRef = power(referenceDecay, (ref-U)/ref) * ref
        network.accessPoint.memory.prevState=1
        powerInc = powerGain*(ref-U)/ref
        #capacity reduced
        newApPower = network.accessPoint.p+powerInc
    
    else:
        network.accessPoint.memory.iterations = network.accessPoint.memory.iterations +1
        powerInc = powerGain*power(powerDecay, network.accessPoint.memory.iterations)
        network.accessPoint.memory.prevState=-1
        newApPower = network.accessPoint.p-powerInc
        
    #resetting maximum capacity every n cycles
    if network.accessPoint.memory.iterations==maxCycles:
        network.accessPoint.memory.iterations=3
        network.accessPoint.memory.uRef=ref*1.1

    if newApPower>maxPower:
        newApPower = maxPowerBackoff
        network.accessPoint.memory.uRef=ref*referenceBackoffOnMaxPowerHit
        
    elif newApPower<=0:
        newApPower = minPower
             
    return newApPower
    
def newApPower(network, interferingStations, c):
    maxP = 1.0
    minP = 0.1
    p = network.accessPoint.p
    prevU = network.accessPoint.memory.prevU
    S = normalisedNetworkThroughput(network, interferingStations, EXPECTED_PACKET_SIZE)
    r = getAverageDataRate20MHZ(network, interferingStations)
    
    y = S * r        
    u = y - c * p
    du = (u - prevU)
    
    newP = p * (1 + du / u)
    network.accessPoint.memory.prevU = u
    
    return max(min(newP, maxP), minP)
    

def newApSnrFloor(newApPower):
    return AP_INITIAL_SNR_FLOOR * newApPower / AP_INITIAL_POWER
    

def createNetworks(a, b, width, length, xSpace, ySpace, n, isStandard):
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
    return networks

def powerVariationSim(a, b, width, length, xSpace, ySpace, n, isStandard, numIterations):
    networks = createNetworks(a, b, width, length, xSpace, ySpace, n, isStandard)
    plotNetworks(networks, (width + xSpace) * a, (length + ySpace) * b)
    recordings = runPowerVariationAlgorithm(networks, numIterations)    
    recordingsToPlot = filter(lambda r: inRange(r.index[0], [1,3]) and inRange(r.index[1], [1,2]), recordings)
    plotRecordings(recordingsToPlot)
    testAlternativeSchemes(networks, recordings, [1,3], [1,2])
    
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
        
#congestionPlot()
#powerVariationSim(a = 5, b = 4, width = 7, length = 7, xSpace = 7, ySpace = 7,
#                  n = 6, isStandard = True, numIterations = 5)




