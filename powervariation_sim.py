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


NUMBER_OF_STATIONS = 15
FLAT_WIDTH = 8
FLAT_LENGTH = 8
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
    
def averageTransmissionDelay(packet_size, network1, interferingAp):
    dataRate = getAverageDataRate20MHZ(network1, interferingAp)*1e6/8 #convert from mbits to bytes/s
    return packet_size/dataRate
 
def normalisedTransmissionDelay(packet_size):
    dataRate = 65*1e6/8
    return packet_size/dataRate

def estimateTransmissionProbability(windowSize, q):
    tauSat = 2.0 / (windowSize + 1)
    return tauSat * q

def allStations(network):
    return network.mobileStations + [network.accessPoint]
    
def probabilityOfExactlyOneTransmission(network, interferingNetwork):
    stations = allStations(network)
    pSuccessfulTransmissions = []
    numsCochannelStations = []
    for station in stations:
        tauI = estimateTransmissionProbability(CW_MIN, station.q)
        otherStationsOnTheSameNetwork = filter(lambda s: s!=station, stations)
        cochannelInterferingStations = filter(lambda s: isCochannelInterference(s, station, WHITE_NOISE), allStations(interferingNetwork))
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
    
def normalisedNetworkThroughput(network, interferingNetwork, expectedPayload):
    #Assuming basic DCF with RTS/CTS with fixed packet sizes
    emptySlotTime = SLOT_TIME
    timeBusyCollision = expectedPropagationDelay(network)+DIFS+normalisedTransmissionDelay(RTS)
    timeBusySuccessful = normalisedTransmissionDelay(RTS)+normalisedTransmissionDelay(CTS)+normalisedTransmissionDelay(ACK)+normalisedTransmissionDelay(expectedPayload)+4*expectedPropagationDelay(network)+3*SIFS+DIFS
    pExactlyOneTransmission = probabilityOfExactlyOneTransmission(network, interferingNetwork)
    pAtLeastOneTransmission = probabilityOfAtLeastOneTransmission(network)
    pSuccessfulTransmission = pExactlyOneTransmission / pAtLeastOneTransmission
    averageSlotTime = ( (1-pAtLeastOneTransmission)*emptySlotTime + \
        pAtLeastOneTransmission*pSuccessfulTransmission*timeBusySuccessful+ \
        pAtLeastOneTransmission*(1-pSuccessfulTransmission)*timeBusyCollision)
    #Capacity - probability of successful transmission * expected payload over slot time
    return pSuccessfulTransmission*pAtLeastOneTransmission*normalisedTransmissionDelay(expectedPayload) / averageSlotTime
        


def plotNodes(nodes, colour):
    plt.plot(map(lambda ms: ms.x, nodes), map(lambda ms: ms.y, nodes), colour)
    
def plotNetworks(network1, network2):
    plt.figure(figsize=(9, 3))
    plotNodes(network1.mobileStations, 'ro')
    plotNodes(network2.mobileStations, 'bo')
    plotNodes([network1.accessPoint], 'gs')
    plotNodes([network2.accessPoint], 'gs')
    plt.axis([0, FLAT_WIDTH * 3, 0, FLAT_LENGTH])
    plt.show()

def plotInterference(mssWithCcIntf, mssWithIcIntf, isRouterCochannel, accessPoint):
    plt.figure(figsize=(9, 3))
    plotNodes(mssWithCcIntf, 'rs')
    plotNodes(mssWithIcIntf, 'ro')
    if isRouterCochannel:
        plotNodes([accessPoint], 'gs')
    else:
        plotNodes([accessPoint], 'go')
    plt.axis([0, FLAT_WIDTH * 3, 0, FLAT_LENGTH])
    plt.show()

def getAverageDataRate20MHZ(network, interferingAP):
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
    for i in range(len(network.mobileStations)):
        snr=sinr(network.accessPoint, network.mobileStations[i], [interferingAP], WHITE_NOISE)
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
    
def tempPowerIncrementing(network1, network2):
    #just a temporary function to see how changing interfering AP power affects the model
    powList1 = []
    powList2 = []
    time = []
    normCapList = []
    dataRateList = []
    capList = []
    normCapList2 = []
    dataRateList2 = []
    capList2 = []
    totalCapList = []

    for i in range(80):
        time.append(i)
        cap=normalisedNetworkThroughput(network1, network2, EXPECTED_PACKET_SIZE)
        cap2=normalisedNetworkThroughput(network2, network1, EXPECTED_PACKET_SIZE)
        normCapList.append(cap)
        normCapList2.append(cap2)
        dr=getAverageDataRate20MHZ(network1, network2.accessPoint)
        dr2=getAverageDataRate20MHZ(network2, network1.accessPoint)
        dataRateList.append(dr)
        dataRateList2.append(dr2)
        capList.append(dr*cap)
        capList2.append(dr2*cap2)
        totalCapList.append((dr*cap+dr2*cap2)/2)
        powList1.append(network1.accessPoint.p)
        powList2.append(network2.accessPoint.p)
        network1.accessPoint.p = newApPower(network1, network2)
        network1.accessPoint.gr = newApGain(network1.accessPoint.p, AP_INITIAL_POWER)
        network2.accessPoint.p = newApPower(network2, network1)
        network2.accessPoint.gr = newApGain(network2.accessPoint.p, AP_INITIAL_POWER)
        

        
    plt.plot(time, normCapList,'r', time, normCapList2, 'b')
    plt.show()
    plt.plot(time, dataRateList,'r', time, dataRateList2, 'b')
    plt.show()
    plt.plot(time, powList1,'r', time, powList2, 'b')
    plt.show()
    plt.plot(time, capList,'r', time, capList2,'b', time, totalCapList,'g')
    plt.show()

def newApPower(network, interferingNetwork):
    sinrs = map(lambda ms: sinr(network.accessPoint, ms, allStations(interferingNetwork), WHITE_NOISE), network.mobileStations)
    lowest_sinr = min(sinrs)
    if lowest_sinr < SINR_FLOOR:
        return network.accessPoint.p + POWER_INCREMENT
    elif isCochannelInterference(network.accessPoint, interferingNetwork.accessPoint, WHITE_NOISE) and lowest_sinr > SINR_FLOOR + POWER_INCREMENT:
        return network.accessPoint.p - POWER_INCREMENT
    else:
        return network.accessPoint.p

def newApGain(newApPower, initialApPower):
    return newApPower / initialApPower
    
    
def powerVariationSim():
    network1 = Network(0, 0, NUMBER_OF_STATIONS)
    network2 = Network(16, 0, NUMBER_OF_STATIONS)
    plotNetworks(network1, network2)
    
    mssWithCcIntf = filter(lambda s: isCochannelInterference(network2.accessPoint, s, WHITE_NOISE), network1.mobileStations)
    mssWithIcIntf = filter(lambda s: not isCochannelInterference(network2.accessPoint, s, WHITE_NOISE), network1.mobileStations)
    isRouterCochannel = isCochannelInterference(network2.accessPoint, network1.accessPoint, WHITE_NOISE)
    plotInterference(mssWithCcIntf, mssWithIcIntf, isRouterCochannel, network1.accessPoint)
    tempPowerIncrementing(network1, network2)
    
def congestionPlot():
    probList = []
    xaxis = []
    network1 = Network(0, 0, 0)
    network2 = Network(16, 0, 0)
    for i in range(40):
        network1.addRandomMobileStations(2)
        network2.addRandomMobileStations(2)
        probList.append(probabilityOfExactlyOneTransmission(network1, network2))
        xaxis.append(i*2)
    plt.plot(xaxis, probList)
    plt.show
        
congestionPlot()
powerVariationSim()




