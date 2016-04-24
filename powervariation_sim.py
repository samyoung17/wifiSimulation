from numpy import *
import matplotlib.pyplot as plt
import random
class Memory:
    def __init__(self):
        self.maxCap=0
        self.prevCap = 0
        self.iteration=0
        self.prevState=0
class Station:
    def __init__(self, x, y, p, q, gr):
        self.x = x
        self.y = y
        self.p = p
        self.q = q
        self.gr = gr
        self.memory = Memory()
class Network:
    def __init__(self, xOffset, yOffset, numStations):
        self.xOffset = xOffset
        self.yOffset = yOffset
        apX = self.xOffset + random.random() * FLAT_WIDTH
        apY = self.yOffset + random.random() * FLAT_LENGTH
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
    def __init__(self):
        self.apPower = []
        self.apGain = []
        self.normalisedThroughput = []        
        self.dataRate = []
        
    def addDataPoint(self, p, gr, S, r):
        self.apPower.append(p)
        self.apGain.append(gr)
        self.normalisedThroughput.append(S)
        self.dataRate.append(r)
        


NUMBER_OF_STATIONS = 7
FLAT_WIDTH = 5
FLAT_LENGTH = 5
AP_INITIAL_POWER = 0.1
MS_INITIAL_POWER = 0.1
POWER_INCREMENT = 0.01

SINR_FLOOR = 3
WHITE_NOISE = 7.9e-11
UNITY_GAIN = 1

MS_PROBABILITY_OF_NONEMPTY_BUFFER=0.7
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
        plt.plot(time, recording.normalisedThroughput)
    plt.title('Normalised throughput')
    plt.show()
    for recording in recordings:
        plt.plot(time, recording.dataRate)
    plt.title('Data rate')
    plt.show()
    for recording in recordings:
        plt.plot(time, recording.apPower)
    plt.title('AP power')
    plt.show()

    for recording in recordings:
        plt.plot(time, multiply(recording.dataRate, recording.normalisedThroughput))
    plt.title('Throughput')
    plt.show()
    

def testPowerVariation(networks):
    #just a temporary function to see how changing interfering AP power affects the model
    recordings = []
    for j in range(len(networks)):
        recordings.append(Recording())

    for i in range(140):        
        for j in range(len(networks)):
            otherNetworks = networks[:j] + networks[j+1:]
            stationsFromOtherNetworks = reduce(lambda x,y: x+y, map(allStations, otherNetworks))
            S = normalisedNetworkThroughput(networks[j], stationsFromOtherNetworks, EXPECTED_PACKET_SIZE)
            r = getAverageDataRate20MHZ(networks[j], stationsFromOtherNetworks)
            recordings[j].addDataPoint(networks[j].accessPoint.p, networks[j].accessPoint.gr, S, r)
        for j in range(len(networks)):
            otherNetworks = networks[:j] + networks[j+1:]
            stationsFromOtherNetworks = reduce(lambda x,y: x+y, map(allStations, otherNetworks))
            networks[j].accessPoint.p = altNewApPower(networks[j], stationsFromOtherNetworks)
            networks[j].accessPoint.gr = newApGain(networks[j].accessPoint.p, AP_INITIAL_POWER)
        
    plotRecordings(recordings)

def newApPower(network, interferingStations):
    sinrs = map(lambda ms: sinr(network.accessPoint, ms, interferingStations, WHITE_NOISE), network.mobileStations)
    lowest_sinr = min(sinrs)
    if lowest_sinr < SINR_FLOOR:
        return network.accessPoint.p + POWER_INCREMENT
    else:
        return network.accessPoint.p

def altNewApPower(network, interferingStations):
 #   return network.accessPoint.p + POWER_INCREMENT
    #parameters
    powerExponent = 0.3 #the larger this value the larger focus on minimizng power
    capRatio = 2 # the lower this number, the more likely power increment, reducing this below 2 requires a large power exponent, otherwise power will keep increasing
    S = normalisedNetworkThroughput(network, interferingStations, EXPECTED_PACKET_SIZE)
    r = getAverageDataRate20MHZ(network, interferingStations)
    cap=S*r
#    cap=S*r
    #first iteration of the algorithm
    if network.accessPoint.memory.prevCap == 0:
         network.accessPoint.memory.prevCap = cap
         network.accessPoint.memory.maxCap = 50
         network.accessPoint.memory.iterations = 1
         return network.accessPoint.p + POWER_INCREMENT
     #subsequent iterations
    #update maximum capacity
    if cap>network.accessPoint.memory.maxCap:
        network.accessPoint.memory.maxCap = cap
    #update number of iterations and power increment value (to ensure decay)
    powerInc = POWER_INCREMENT * power(0.9, network.accessPoint.memory.iterations)
    network.accessPoint.memory.iterations = network.accessPoint.memory.iterations +1
#    if cap<((network.accessPoint.memory.prevCap+network.accessPoint.memory.maxCap)/capRatio or cap < network.accessPoint.memory.prevCap):
    if cap<(network.accessPoint.memory.maxCap):
        network.accessPoint.memory.maxCap= 0.97 * network.accessPoint.memory.maxCap
        #capacity reduced
        newApPower = network.accessPoint.p+powerInc
        currentState=1
    elif cap>network.accessPoint.memory.prevCap:
        #capacity increased
        newApPower = network.accessPoint.p-powerInc
        currentState=-1
    else:
        newApPower = network.accessPoint.p-powerInc
        currentState=-1
  #      capacity unchanged
    if currentState != network.accessPoint.memory.prevState and network.accessPoint.memory.iterations>40:
        network.accessPoint.memory.prevState=currentState
        network.accessPoint.memory.iterations=2
    if newApPower>0.5:
        newApPower = 0.5
    elif newApPower<=0:
        newApPower = 0.1
                    
    return newApPower
    
    
def newApGain(newApPower, initialApPower):
    return newApPower / initialApPower
    
    
def powerVariationSim():
    networks = [
        Network(0, 0, NUMBER_OF_STATIONS),
        Network(16, 0, NUMBER_OF_STATIONS),
        Network(32, 0, NUMBER_OF_STATIONS),
        Network(0, 16, NUMBER_OF_STATIONS),
        Network(16, 16, NUMBER_OF_STATIONS),
        Network(32, 16, NUMBER_OF_STATIONS)
    ]
    plotNetworks(networks, FLAT_WIDTH * 5, FLAT_LENGTH * 3)

    testPowerVariation(networks)
    
def congestionPlot():
    probList = []
    xaxis = []
    network1 = Network(0, 0, 0)
    network2 = Network(16, 0, 0)
    for i in range(40):
        network1.addRandomMobileStations(2)
        network2.addRandomMobileStations(2)
        probList.append(probabilityOfExactlyOneTransmission(network1, allStations(network2)))
        xaxis.append(i*2)
    plt.plot(xaxis, probList)
    plt.show()
        
congestionPlot()
powerVariationSim()




