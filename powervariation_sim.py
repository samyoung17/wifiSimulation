from numpy import *
import matplotlib.pyplot as plt
import random

class Station:
    def __init__(self, x, y, p, q, gr):
        self.x = x
        self.y = y
        self.p = p
        self.q = q
        self.gr = gr
        
class Network:
    def __init__(self, index, xOffset, yOffset, width, length, numStations):
        self.index = index
        self.xOffset = xOffset
        self.yOffset = yOffset
        apX = self.xOffset + random.random() * width
        apY = self.yOffset + random.random() * length
        self.accessPoint = Station(apX, apY, AP_INITIAL_POWER, AP_PROBABILITY_OF_NONEMPTY_BUFFER, UNITY_GAIN)
        self.mobileStations = []
        self.addRandomMobileStations(numStations)
    
    def addRandomMobileStations(self, numStations):
        for i in range(numStations):
            x = self.xOffset + random.random() * FLAT_WIDTH
            y = self.yOffset + random.random() * FLAT_LENGTH
            ms = Station(x,y,MS_INITIAL_POWER, MS_PROBABILITY_OF_NONEMPTY_BUFFER, UNITY_GAIN)
            self.mobileStations.append(ms)

class Recording:
    def __init__(self, index):
        self.index = index
        self.apPower = []
        self.apGain = []
        self.normalisedThroughput = []        
        self.dataRate = []
        
    def addDataPoint(self, p, gr, S, r):
        self.apPower.append(p)
        self.apGain.append(gr)
        self.normalisedThroughput.append(S)
        self.dataRate.append(r)
        


AP_INITIAL_POWER = 0.1
MS_INITIAL_POWER = 0.1
POWER_INCREMENT = 0.05

SINR_FLOOR = 3
WHITE_NOISE = 7.9e-11
UNITY_GAIN = 1

MS_PROBABILITY_OF_NONEMPTY_BUFFER=0.4
AP_PROBABILITY_OF_NONEMPTY_BUFFER=0.97
CW_MIN = 16

C=3e8
#taken from 802.11n spec for 2.4 gHz, times in s
SIFS = 10e-6
DIFS = 28e-6
SLOT_TIME = 9e-6   
#bytes/second
TRANSMISSION_SPEED=72.2e6/8
#theoretical 802.11n 20mHz transmission rate, very optimistic (ignores SNR, signal power etc)


#in bytes
RTS = 20
CTS = 14
ACK = 14
EXPECTED_PACKET_SIZE = 2500 #guesswork, typically needs to be >2347 for RTS/CTS
    
def distance(node1, node2):
  return sqrt((node1.x-node2.x)**2 + (node1.y-node2.y)**2)  

# path loss calculation acording to ITU model for indoor propagation
# ITU-R  P.1238-7
def pathLoss(d):
  dd = d
  if d < 1:
    dd = 1
  L = 20*log10(2400)+30*log10(dd) + 14 - 28
  return 1.0/(10.0**(L/10.0))

def isCochannelInterference(interferingNode, receiver, whiteNoise):
    receivedPower = interferingNode.p * pathLoss(distance(interferingNode, receiver))
    return receivedPower * receiver.gr > whiteNoise * SINR_FLOOR
    
def receivedInterferencePower(interferingNode, receiver, whiteNoise):
    receivedPower = interferingNode.p * pathLoss(distance(interferingNode, receiver))
    return receivedPower * receiver.gr
    
# function calculates SINR for station
def sinr(transmitter, receiver, interferingNodes, whiteNoise):  
    signalVolume = transmitter.p * pathLoss(distance(transmitter, receiver))
    interchannelInterferingNodes = filter(lambda node: not isCochannelInterference(node, receiver, whiteNoise), interferingNodes)
    interferenceVolume = sum(map(lambda node: node.p * pathLoss(distance(node, receiver)), interchannelInterferingNodes))
    return signalVolume * receiver.gr / (interferenceVolume * receiver.gr + whiteNoise)

def expectedPropagationDelay(network):
    delay=0
    for i in range(len(network.mobileStations)):
        d=distance(network.accessPoint, network.mobileStations[i])
        delay+=d/C
    return delay/len(network.mobileStations)

def normalisedTransmissionDelay(packet_size):
    dataRate = 65*1e6/8
    return packet_size/dataRate

def estimateTransmissionProbability(windowSize, q):
    tauSat = 2.0 / (windowSize + 1)
    return tauSat * q

def allStations(network):
    return network.mobileStations + [network.accessPoint]
    
def probabilityOfExactlyOneTransmission(network, interferingNodes):
    stations = allStations(network)
    pSuccessfulTransmissions = []
    numsCochannelStations = []
    for station in stations:
        tauI = estimateTransmissionProbability(CW_MIN, station.q)
        otherStationsOnTheSameNetwork = filter(lambda s: s!=station, stations)
        cochannelInterferingStations = filter(lambda s: isCochannelInterference(s, station, WHITE_NOISE), interferingNodes)
        numsCochannelStations.append(len(cochannelInterferingStations))
        allCochannelStations = otherStationsOnTheSameNetwork + cochannelInterferingStations
        tauJs = map(lambda s: estimateTransmissionProbability(CW_MIN, s.q), allCochannelStations)
        pSuccessfulTransmissionI = tauI * product(map(lambda tauJ: 1-tauJ, tauJs))
        pSuccessfulTransmissions.append(pSuccessfulTransmissionI)
        
    #print(numsCochannelStations)
    return sum(pSuccessfulTransmissions)
        
        
def probabilityOfAtLeastOneTransmission(network):
    stations = allStations(network)
    taus = map(lambda station: estimateTransmissionProbability(CW_MIN, station.q), stations)
    return 1 - product(map(lambda tau: 1-tau, taus))
    
def normalisedNetworkThroughput(network, interferingNodes, expectedPayload):
    #Assuming basic DCF with RTS/CTS with fixed packet sizes
    emptySlotTime = SLOT_TIME
    timeBusyCollision = expectedPropagationDelay(network)+DIFS+normalisedTransmissionDelay(RTS)
    timeBusySuccessful = normalisedTransmissionDelay(RTS)+normalisedTransmissionDelay(CTS)+normalisedTransmissionDelay(ACK)+normalisedTransmissionDelay(expectedPayload)+4*expectedPropagationDelay(network)+3*SIFS+DIFS
    pExactlyOneTransmission = probabilityOfExactlyOneTransmission(network, interferingNodes)
    pAtLeastOneTransmission = probabilityOfAtLeastOneTransmission(network)
    pSuccessfulTransmission = pExactlyOneTransmission / pAtLeastOneTransmission
    averageSlotTime = ( (1-pAtLeastOneTransmission)*emptySlotTime + \
        pAtLeastOneTransmission*pSuccessfulTransmission*timeBusySuccessful+ \
        pAtLeastOneTransmission*(1-pSuccessfulTransmission)*timeBusyCollision)
    #Capacity - probability of successful transmission * expected payload over slot time
    return pSuccessfulTransmission*pAtLeastOneTransmission*normalisedTransmissionDelay(expectedPayload) / averageSlotTime

    
def plotNetworks(networks, width, length):
    graphWidth = 10.0
    graphHeight = graphWidth * length / width
    plt.figure(figsize=(graphWidth, graphHeight))
    for network in networks:
        plt.plot(map(lambda ms: ms.x, network.mobileStations), map(lambda ms: ms.y, network.mobileStations), 'bo')
        plt.plot(network.accessPoint.x, network.accessPoint.y, 'rs')
    plt.axis([0, width, 0, length])
    plt.show()

def getAverageDataRate20MHZ(network, interferingNodes):
    dataRate=0
    MCSToDataRateSwitcher = {
        00: 0,
        0: 6.5,
        1: 13,
        2: 19.5,
        3: 26,
        4: 39,
        5: 52,
        6: 58.5,
        7: 65
    }
    for station in network.mobileStations:
        snr=sinr(network.accessPoint, station, interferingNodes, WHITE_NOISE)
        if snr<3:
            mcs=00;
        elif snr<5:
            mcs=0
        elif snr<9:
            mcs=1
        elif snr<11:
            mcs=2
        elif snr<15:
            mcs=3
        elif snr<18:
            mcs=4            
        elif snr<20:
            mcs=5
        elif snr<25:
            mcs=6            
        else:
            mcs=7
        dataRate+=MCSToDataRateSwitcher.get(mcs, 65)
    return dataRate/len(network.mobileStations)

def plotRecordings(recordings):
    time = range(len(recordings[0].apPower))
    for recording in recordings:
        plt.plot(time, recording.normalisedThroughput, label='N' + str(recording.index))
    plt.title('Normalised throughput')
    plt.legend(bbox_to_anchor=(1.05, 1), loc=2)
    plt.show()
    for recording in recordings:
        plt.plot(time, recording.dataRate, label='N' + str(recording.index))
    plt.title('Data rate')
    plt.legend(bbox_to_anchor=(1.05, 1), loc=2)
    plt.show()
    for recording in recordings:
        plt.plot(time, recording.apPower, label='N' + str(recording.index))
    plt.title('AP power')
    plt.legend(bbox_to_anchor=(1.05, 1), loc=2)
    plt.show()
    for recording in recordings:
        plt.plot(time, multiply(recording.dataRate, recording.normalisedThroughput), label='N' + str(recording.index))
    plt.title('Throughput')
    plt.legend(bbox_to_anchor=(1.05, 1), loc=2)
    plt.show()
    
def inRange(number, r):
    return number>= r[0] and number <= r[1]

def testPowerVariation(networks, iPlotRange, jPlotRange):
    #just a temporary function to see how changing interfering AP power affects the model
    recordings = []
    for network in networks:
        recordings.append(Recording(network.index))

    for i in range(80):        
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

def newApPower(network, interferingStations):
    return network.accessPoint.p + POWER_INCREMENT


def newApGain(newApPower, initialApPower):
    return newApPower / initialApPower
    
    
def powerVariationSim():
    a = 4
    b = 5
    width = 7
    length = 7
    xSpace = 7
    ySpace = 7
    n = 6
    
    networks = []
    for i in range(a):
        for j in range(b):
            xOffset = i * (width + xSpace)
            yOffset = j * (length + ySpace)
            network = Network((i,j), xOffset, yOffset, width, length, n)
            networks.append(network)
    plotNetworks(networks, (width + xSpace) * a, (length + ySpace) * b)

    testPowerVariation(networks, [1,2], [1,3])
    
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




