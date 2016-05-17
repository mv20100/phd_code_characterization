import visa

class SMB100A(object):

	def __init__(self,gpibAdress=19,name=None):
		freqSynthID = "GPIB::"+str(gpibAdress)+"::INSTR"
		rm = visa.ResourceManager()
		self.name = name
		self.inst = rm.open_resource(freqSynthID,read_termination='\n')

	def getFmDev(self):
		self.inst.write("FM:DEV?")
		fmDev = float(self.inst.read())
		# print "FM Dev: "+str(fmDev)
		return fmDev

	def setFmDev(self,fmDev):
		self.inst.write("FM:DEV "+str(fmDev))
		return
		
	def getFrequency(self):
		self.inst.write("FREQ:CW?")
		freq = float(self.inst.read())
		# print "Frequency: "+str(freq)
		return freq
	
	def setFrequency(self,freq):
		self.inst.write("FREQ:CW "+str(freq))
		return

	def incFrequency(self,inc):
		freq = self.getFrequency()
		freq = freq + inc
		self.setFrequency(freq)
		return freq

	def setPowerAmplitude(self,pow):
		assert pow<=28
		self.inst.write("POW:AMPL "+str(pow))
		return
		
	def getPowerAmplitude(self):
		self.inst.write("POW:AMPL?")
		RFpow = float(self.inst.read())
		return RFpow
	
	def setRFState(self,state):
		stateStr = "OFF"
		if state: stateStr = "ON"
		self.inst.write("OUTP:STAT "+stateStr)
		return
	
	def getRFState(self):
		self.inst.write("OUTP:STAT?")
		state = self.inst.read()
		assert state in ["0","1"], "Unexpected reply: %s" % (state)
		return int(state)

	def setFMState(self,state):
		stateStr = "OFF"
		if state: stateStr = "ON"
		self.inst.write("FM:STAT "+stateStr)
		return
		
	def getFMState(self):
		self.inst.write("FM:STAT?")
		state = self.inst.read()
		assert state in ["0","1"], "Unexpected reply: %s" % (state)  
		return int(state)
		
	def setModState(self,state):
		stateStr = "OFF"
		if state: stateStr = "ON"
		self.inst.write("OUTP:MOD:STAT "+stateStr)
		return	

	def getModState(self):
		self.inst.write("OUTP:MOD:STAT?")
		state = self.inst.read()
		assert state in ["0","1"], "Unexpected reply: %s" % (state)  
		return int(state)

	def getFmExt1Coupl(self):
		self.inst.write("FM:EXT1:COUP?")
		return self.inst.read()		
	
	def getParams(self):
		params = dict()
		params.update({"RFstate":self.getRFState()})
		params.update({"FMstate":self.getFMState()})
		params.update({"Modstate":self.getModState()})
		params.update({"RFpow":self.getPowerAmplitude()})
		params.update({"fmDev":self.getFmDev()})
		params.update({"fmCoup":self.getFmExt1Coupl()})
		return {self.name:params}
		
if __name__=='__main__':
	freqSynth = SMB100A()