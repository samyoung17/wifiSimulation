from numpy import *
import matplotlib.pyplot as plt
import random


class AccessPoint:
    def __init__(self,x,y,p):
        self.x = x
        self.y = y
        self.p = p
        
class MobileStation:
    def __init__(self,x,y,p):
        self.x = x
        self.y = y
        self.p = p
        
class Network:
    def __init__(self, accessPoint, mobileStations):
        self.accessPoint = accessPoint
        self.mobileStations = mobileStations


NUMBER_OF_STATIONS = 10
FLAT_WIDTH = 8
FLAT_LENGTH = 8
AP_INITIAL_POWER = 0.1
MS_INITIAL_POWER = 0.1
POWER_INCREMENT = 0.01

SINR_FLOOR = 3
WHITE_NOISE = 7.9e-11

TAU_M=0.1
TAU_R1=0.7
TAU_R2=0.7
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
#Place an AP and n mobile stations at random positions in a 8x8 flat
def createNetwork(xOffset, yOffset, numStations):
    apX = xOffset + random.random() * FLAT_WIDTH
    apY = yOffset + random.random() * FLAT_LENGTH
    ap = AccessPoint(apX, apY, AP_INITIAL_POWER)
    stations = []
    for i in range(numStations):
        msX = xOffset + random.random() * FLAT_WIDTH
        msY = yOffset + random.random() * FLAT_LENGTH
        ms = MobileStation(msX, msY, MS_INITIAL_POWER)
        stations.append(ms)
    return Network(ap, stations)
    
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
    return receivedPower > whiteNoise * SINR_FLOOR

def stationsWithCochannelInterference(network, interferingAp):
    return filter(lambda ms: isCochannelInterference(interferingAp, ms, WHITE_NOISE), network.mobileStations)
    
def stationsWithInterchannelInterference(network, interferingAp):
    return filter(lambda ms: not isCochannelInterference(interferingAp, ms, WHITE_NOISE), network.mobileStations)
  
# function calculates SINR for station
def sinr(transmitter, receiver, interferingNodes, whiteNoise):  
  signalVolume = transmitter.p * pathLoss(distance(transmitter, receiver))
  interchannelInterferingNodes = filter(lambda node: not isCochannelInterference(node, receiver, whiteNoise), interferingNodes)
  interferenceVolume = sum(map(lambda node: node.p * pathLoss(distance(node, receiver)), interchannelInterferingNodes))
  return signalVolume / (interferenceVolume + whiteNoise)

def expectedPropagationDelay(network):
    delay=0
    for i in range(len(network.mobileStations)):
        d=distance(network.accessPoint, network.mobileStations[i])
        delay+=d/C
    return delay/len(network.mobileStations)
    
def averageTransmissionDelay(packet_size, network1, interferingAp):
    dataRate = getAverageDataRate20MHZ(network1, interferingAp)*1e6/8 #convert from mbits to bytes/s
    return packet_size/dataRate
    
def probabilityOfExactlyOneTransmission(k, n,tauM, tauR1, tauR2, isRouterCochannel):
    if isRouterCochannel:
        pRouterInterference = tauR2
    else:
        pRouterInterference = 0
    return k*tauM*power(1-tauM,n-1)*(1-tauR1)*(1-tauR2)  \
        + (n-k)*tauM*power(1-tauM,n-1)*(1-tauR1)    \
        + tauR1*power(1-tauM,n)*(1-pRouterInterference)
    
def networkCapacity (network, interferingAp, tauR1, tauM, tauR2, expectedPayload):
    k = len(stationsWithCochannelInterference(network, interferingAp))    
    n=len(network.mobileStations)
    #Assuming basic DCF with RTS/CTS with fixed packet sizes
    emptySlotTime = SLOT_TIME
    timeBusyCollision = expectedPropagationDelay(network)+DIFS+averageTransmissionDelay(RTS, network, interferingAp)
    timeBusySuccessful = averageTransmissionDelay(RTS, network, interferingAp)+averageTransmissionDelay(CTS, network, interferingAp)+averageTransmissionDelay(ACK, network, interferingAp)+averageTransmissionDelay(expectedPayload, network, interferingAp)+4*expectedPropagationDelay(network)+3*SIFS+DIFS
    isRouterCochannel = isCochannelInterference(interferingAp, network.accessPoint, WHITE_NOISE)
    pExactlyOneTransmission = probabilityOfExactlyOneTransmission(k,n,tauM,tauR1,tauR2, isRouterCochannel)
    pAtLeastOneTransmission = 1- (power(1-tauM,n)*(1-tauR1))
    pSuccessfulTransmission = pExactlyOneTransmission / pAtLeastOneTransmission
    #Capacity - probability of successful transmission * expected payload over slot time
    return pSuccessfulTransmission*pAtLeastOneTransmission*expectedPayload /    \
        ( (1-pAtLeastOneTransmission)*emptySlotTime + \
        pAtLeastOneTransmission*pSuccessfulTransmission*timeBusySuccessful+ \
        pAtLeastOneTransmission*(1-pSuccessfulTransmission)*timeBusyCollision)


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
    powList = []
    capList = []
    dataRateList = []

    for i in range (0,20):
       # print "Interfering AP power: ", network2.accessPoint.p
        powList.append(network2.accessPoint.p)
        capList.append(networkCapacity(network1, network2.accessPoint, TAU_R1, TAU_M, TAU_R2, EXPECTED_PACKET_SIZE))
        dataRateList.append(getAverageDataRate20MHZ(network1, network2.accessPoint))
        network2.accessPoint.p=network2.accessPoint.p + POWER_INCREMENT
    plt.plot(powList, dataRateList,'r')
    plt.show()
    
def newApPower(network, interferingAp):
    lowest_sinr = min(map(lambda ms: sinr(network.accessPoint, ms, [interferingAp], WHITE_NOISE)), network.mobileStations)
    if lowest_sinr < SINR_FLOOR:
        return network.accessPoint.p + POWER_INCREMENT
    elif isCochannelInterference(network.accessPoint, interferingAp) and lowest_sinr > SINR_FLOOR + POWER_INCREMENT:
        return network.accessPoint.p - POWER_INCREMENT
    else:
        return network.accessPoint.p

    
def main():
    network1 = createNetwork(0, 0, 10)
    network2 = createNetwork(16, 0, 10)
    plotNetworks(network1, network2)
    
    mssWithCcIntf = stationsWithCochannelInterference(network1, network2.accessPoint)    
    mssWithIcIntf = stationsWithInterchannelInterference(network1, network2.accessPoint)
    isRouterCochannel = isCochannelInterference(network2.accessPoint, network1.accessPoint, WHITE_NOISE)
    plotInterference(mssWithCcIntf, mssWithIcIntf, isRouterCochannel, network1.accessPoint)
    
    tempPowerIncrementing(network1, network2)

      
     
        
main()




