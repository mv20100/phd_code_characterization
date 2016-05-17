import quantities as pq

class Parameter(str):
	def __new__(cls, value, *args, **kwargs):
		# explicitly only pass value to the str constructor
		return super(Parameter, cls).__new__(cls, value)

	def __init__(self,key,description,short=None,formater=None,unit=None,address=None):
		self.key = key
		self.description = description
		self.formater = formater
		self.short = short
		self.unit = unit
		self.address = address

	def writeUnit(self):
		resultStr = None
		if self.unit is not None:
			if hasattr(self.unit,'symbol'): resultStr = self.unit.symbol
			else: resultStr = self.unit
		return resultStr
	
	def writeValueUnit(self,value):
		resultStr = ""
		if self.formater is None: resultStr = "%s"%(value)
		else: resultStr = self.formater%(value)
		if self.unit is not None:
			resultStr = "%s %s"%(resultStr,self.writeUnit())
		return resultStr
		
	def writeShortLine(self,value):
		resultStr = self.writeValueUnit(value)
		resultStr = "%s: %s"%(self.short,resultStr)
		return resultStr
		
	def longAxisLabel(self):
		resultStr = self.description
		if self.unit is not None:
			resultStr = "%s (%s)"%(resultStr,self.writeUnit())
		return resultStr

	def shortAxisLabel(self):
		resultStr = self.short
		if self.unit is not None:
			resultStr = "%s (%s)"%(resultStr,self.writeUnit())
		return resultStr
		
	def getLongName(self):
		if self.address:
			return "_".join(self.address)+"_"+self
		else: return self

	def getValue(self,dictionary):
		curDict = dictionary.copy()
		if self.address:
			for key in self.address:
				if curDict.has_key(key):
					curDict = curDict[key]
				else:
					return None
		return curDict[self]
		
# User parameter keys
cell= 		Parameter("cell",	"Cell ID","Cell")
cellTemp= 	Parameter("cellTemp","Cell temperature","Tcell","%.1f",pq.degC)
content= 	Parameter("content","Cell content","Content")
gainPD= 	Parameter("gainPD",	"Photodiode gain","Gpd","%.1f","dB")
intLaser= 	Parameter("intLaser","Laser DC current","Ilas","%.1f",pq.mA)
intMagField=Parameter("intMagField","Coil current","Imag","%.2f",pq.mA)
time=		Parameter("time",	"Acquisition time","Time")
date =		Parameter("date",	"Acquisition date","Date")
cellTempCtrl_measCellTemp = Parameter("measCellTemp","Measured temperature","Tmeas","%.3f",pq.degC,address=["cellTempCtrl"])
eomBiasCtrl_biasDC = Parameter("biasDC","EOM DC bias","Veom","%.3f",pq.V,address=["eomBiasCtrl"])
powerController_opticalPower = Parameter("opticalPower","Optical power","Popt","%.3f","uW",address=["powerController"])
# Equipment parameter keys

#Others
floatTime = 	Parameter("floatTime","Timestamp","Tabs","%d",pq.s)
#Fit parameters keys
centerDoubled =	Parameter("centerDoubled","Center frequency","Freq","%.1f",pq.Hz,address=["fitParams","lorentzian"])
fwhmDoubled =	Parameter("fwhmDoubled","CPT FWHM","FWHM","%.1f",pq.Hz,address=["fitParams","lorentzian"])
background = 	Parameter("background","Background","Bg","%.3f",pq.V,address=["fitParams","lorentzian"])
contrast = 		Parameter("contrast","CPT contrast","Contrast","%.4f",address=["fitParams","lorentzian"])
shift = 		Parameter("shift","Shift from Cs hfs","Shift","%.1f",pq.Hz,address=["fitParams","lorentzian"])
p1_shift = 		Parameter("p1_shift","Shift from Cs hfs","Shift","%.1f",pq.Hz,address=["fitParams","doubleLorentzian"])
p2_shift = 		Parameter("p2_shift","Shift from Cs hfs","Shift","%.1f",pq.Hz,address=["fitParams","doubleLorentzian"])

# def getChildParam(longParam,params):
	# if type(longParam) is list:
		# paramHiera = longParam.split("_")
	# else: paramHiera = longParam
	# item = params
	# for key in paramHiera:
		# if key in item.keys():
			# item = item[key]
		# else:
			# return None
	# return item
	
def flattenParamDict(params):
	outDic = dict()
	for key in params:
		if type(params[key]) == dict:
			params[key] = flattenParamDict(params[key])
			for subparam in params[key]:
				outDic.update({key+"_"+subparam:params[key][subparam]})
		else: outDic.update({key:params[key]})
	return outDic

def formatParams(parameterNames,parametersDic):
	parametersDic = flattenParamDict(parametersDic)
	lines = []
	for parameterName in parameterNames:
		if parametersDic.has_key(parameterName):
			lines.append(parameterName.writeShortLine(parametersDic[parameterName]))
	return "\n".join(lines)