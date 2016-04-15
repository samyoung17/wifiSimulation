from numpy import *
import pylab as P




# Simple structures for transmitter and receiver
# The only visible difference is  - transmitter is characterized using
# additional parameter p - transmit power
class Transmitter:
  def __init__(self, x, y, p):
    self.x = x
    self.y = y
    self.p = p

class Receiver:
  def __init__(self, x, y):
    self.x = x
    self.y = y
    
# Randomly place transmitter in a 100x100 square.
# Receiver are places around transmitters in 40x40 square    
def allocateTransmitterAndReceiver():
  transPosX = random.rand()*100
  transPosY = random.rand()*100
  transPower = 0.1
  recPosX = transPosX + random.rand()*40
  recPosY = transPosY + random.rand()*40
  return (Transmitter(transPosX, transPosY, transPower), Receiver(recPosX, recPosY))

# Allocate a system of n transmitters and receivers    
def allocateSystem(n):
  transmitters = []
  receivers = []
  for i in range(n):
    tra, rec = allocateTransmitterAndReceiver()
    transmitters.append(tra)
    receivers.append(rec)
  return transmitters, receivers
  
def distance(node1, node2):
  return sqrt((node1.x-node2.x)**2 + (node1.y-node2.y)**2)  


####################################################################################################

# path loss calculation acording to ITU model for indoor propagation
# ITU-R  P.1238-7
def pathLoss(d):
  dd = d
  if d < 1:
    dd = 1
  L = 20*log10(2400)+30*log10(dd) + 14 - 28
  return 1.0/(10.0**(L/10.0))
  
# function calculates SINR for user number k
# transList - list of transmitters in a system
# recList - list of receivers in a system
# sigmaSquared - white noise power at receivers
def sinr(k, transList, recList, sigmaSquared):  
  interf = 0.0
  for j in range(len(transList)):
    if j != k:
      hjk = pathLoss(distance(transList[j], recList[k])) # kanalo perdavimo koeficientas is j-ojo k-tajam
      interf = interf + hjk*transList[j].p
  hkk = pathLoss(distance(transList[k], recList[k]))
  return hkk*transList[k].p/(interf + sigmaSquared)

# calculate averge system capacity (capacity per user)  
def systemCapacity(transList, recList, sigmaSquared):
  c = 0
  for i in range(len(transList)):
    c = c + log2(1+sinr(i, transList, recList, sigmaSquared))
  return c/(len(transList))

###################################################################################################

# This is somewhat simplified function for power changing for every user
# There is no any threashold of sensitivity, so it is assumed
# that every user changes its power sequentially
# as every change of power by any user results in changed SINR for any other user
# So users update there powers sequantially
# This is the most inportant function in all this simulation and
# it probably could be rewritten for other simulation scenarios
# At every step new powel configuration (new transmitters) are returned
# Names of parameters are self explaining 
def nextPowerConfigurationSequential(transList, recList, sigmaSquared, pMax, c):
  #pirma nukopijuokime sena transList i nauja
  newTransList = list(range(len(transList)))
  for i in range(len(transList)):
    newTransList[i] = transList[i]
  
  for i in range(len(newTransList)):
    newP = 1.0/c - 1.0/sinr(i, newTransList, recList, sigmaSquared)*newTransList[i].p
    if newP <= 0:
      newP = 1e-10   #This is somewhat a hack. I dont want power of any transmitter to be exacly zero
    if newP > pMax:
      newP = pMax
    newTransList[i] = Transmitter(transList[i].x, transList[i].y, newP)
  return newTransList
  

def averageSystemCapacity(pMax, c, numUsers):
  sigmaSq = 1e-12
  cap = 0.0
  numSimulation = 1000
  for i in range(numSimulation):
    tra, rec = allocateSystem(numUsers)
    for iter in range(10):
      tra = nextPowerConfigurationSequential(tra, rec, sigmaSq, pMax, c)
    cap = cap + systemCapacity(tra, rec, sigmaSq)
  return cap/numSimulation  

# Plot graphs of power allocation for every user
# This function is esefull to assure yourself that system is really converging :)
def testSystemConvergence(pMax, c, numUsers):
  sigmaSq = 1e-12
  iterToConvergence = 20
  powerData = zeros((numUsers, iterToConvergence+1))
  tra, rec = allocateSystem(numUsers)
  for i in range(numUsers):
    powerData[i][0] = tra[i].p
  print(systemCapacity(tra, rec, sigmaSq))
  for iterr in range(iterToConvergence):
    tra = nextPowerConfigurationSequential(tra, rec, sigmaSq, pMax, c)
    for i in range(numUsers):
      powerData[i][iterr+1] = tra[i].p
  print(systemCapacity(tra, rec, sigmaSq))
  P.figure()
  for i in range(numUsers):
    P.plot(powerData[i, :])
  P.show()

# change number of users and observe the change of full or average system capacity
def systemCapacityVsNumberOfUsers(c):
  users = arange(2, 21, 1)
  cap1 = []
  cap2 = []
  cap3 = []
  cap4 = []
  for u in users:
    cap1.append(averageSystemCapacity(0.1, c, u)*u)   #multiplication by u should be removes if we are interested in
    cap2.append(averageSystemCapacity(1.0, c, u)*u)   #averaged capacity for one user
    cap3.append(averageSystemCapacity(2.0, c, u)*u)
    cap4.append(averageSystemCapacity(4.0, c, u)*u)
    print(u)
    
  P.figure()
  P.plot(users, cap1, "k*-", label = "Pmax = 0.1 W")
  P.plot(users, cap2, "ko-", label = "Pmax = 1 W")
  P.plot(users, cap3, "k+-", label = "Pmax = 2 W")
  P.plot(users, cap4, "k.-", label = "Pmax = 4 W")
  P.legend(loc='upper left')
  P.xlabel("Number of users")
  P.ylabel("Full system capacity, bits/s/Hz")
  P.show()

testSystemConvergence(2, 0.5, 10)  
systemCapacityVsNumberOfUsers(0.25)










