from numpy import *
import inspect
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

SINR_FLOOR = 3
WHITE_NOISE = 4e-11

       
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
def sinr(transmitter, receiver, interferingAp, whiteNoise):  
  signalVolume = transmitter.p * pathLoss(distance(transmitter, receiver))
  if isCochannelInterference(interferingAp, receiver, whiteNoise):
      return signalVolume / whiteNoise
  else:      
      interferenceVolume = interferingAp.p * pathLoss(distance(interferingAp, receiver))
      return signalVolume / (interferenceVolume + whiteNoise)
  
def networkCapacity (network, interferingAp, tauR, tauM):
    return 1

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

def main():
    network1 = createNetwork(0, 0, 10)
    network2 = createNetwork(16, 0, 10)
    plotNetworks(network1, network2)
    
    mssWithCcIntf = stationsWithCochannelInterference(network1, network2.accessPoint)    
    mssWithIcIntf = stationsWithInterchannelInterference(network1, network2.accessPoint)
    isRouterCochannel = isCochannelInterference(network2.accessPoint, network1.accessPoint, WHITE_NOISE)
    plotInterference(mssWithCcIntf, mssWithIcIntf, isRouterCochannel, network1.accessPoint)


main()




