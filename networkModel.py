from numpy import *
import random

class Memory:
    def __init__(self):
        self.uRef=0
        self.prevUref = 0
        self.iteration=0
        self.prevState=0
        
class Station:
    def __init__(self, x, y, p, q, gr, snrFloor):
        self.x = x
        self.y = y
        self.p = p
        self.q = q
        self.gr = gr
        self.memory = Memory()
        self.snrFloor = snrFloor

class Network:
    def __init__(self, index, xOffset, yOffset, width, length, numStations, seed=None):
        if seed != None:
            self.rGen = random.Random(seed)
        else:
            self.rGen = random.Random()
        self.index = index
        self.xOffset = xOffset
        self.yOffset = yOffset
        apX = self.xOffset + self.rGen.random() * width
        apY = self.yOffset + self.rGen.random() * length
        self.accessPoint = Station(apX, apY, AP_INITIAL_POWER, AP_PROBABILITY_OF_NONEMPTY_BUFFER, AP_GAIN, AP_INITIAL_SNR_FLOOR)
        self.mobileStations = []
        self.width=width
        self.length=length
        self.addRandomMobileStations(numStations)
    
    def addRandomMobileStations(self, numStations):
        for i in range(numStations):
            x = self.xOffset + self.rGen.random() * self.width
            y = self.yOffset + self.rGen.random() * self.length
            ms = Station(x,y,MS_INITIAL_POWER, MS_PROBABILITY_OF_NONEMPTY_BUFFER, UNITY_GAIN, MS_INITIAL_SNR_FLOOR)
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

AP_INITIAL_SNR_FLOOR = 20.0
MS_INITIAL_SNR_FLOOR = 2.0
WHITE_NOISE = 7.9e-11
UNITY_GAIN = 1
AP_GAIN = 10

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
    return receivedPower * receiver.gr > whiteNoise * receiver.snrFloor
    
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

def delay(packet_size):
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
    timeBusyCollision = expectedPropagationDelay(network)+DIFS+delay(RTS)
    timeBusySuccessful = delay(RTS)+delay(CTS)+delay(ACK)+delay(expectedPayload)+4*expectedPropagationDelay(network)+3*SIFS+DIFS
    pExactlyOneTransmission = probabilityOfExactlyOneTransmission(network, interferingNodes)
    pAtLeastOneTransmission = probabilityOfAtLeastOneTransmission(network)
    pSuccessfulTransmission = pExactlyOneTransmission / pAtLeastOneTransmission
    averageSlotTime = ( (1-pAtLeastOneTransmission)*emptySlotTime + \
        pAtLeastOneTransmission*pSuccessfulTransmission*timeBusySuccessful+ \
        pAtLeastOneTransmission*(1-pSuccessfulTransmission)*timeBusyCollision)
    #Capacity - probability of successful transmission * expected payload over slot time
    return pSuccessfulTransmission*pAtLeastOneTransmission*delay(expectedPayload) / averageSlotTime
    
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