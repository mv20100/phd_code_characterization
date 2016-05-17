import numpy as np
import yaml, time, sys, pickle, cPickle
from collections import OrderedDict
from collections import deque

class Buffer(object):
	
	def __init__(self,size):
		self.size = size
		self.deque = deque([],size)
		self.array = np.zeros(size)
		self.ptr = -1

	def append(self,element):
		self.ptr = (self.ptr + 1) % self.size
		self.deque.append(self.ptr)
		self.array[self.ptr] = element

	def get_data(self):
		return self.array[self.deque]

	def get_last(self):
		return self.get_data()[-1]

	def get_average(self):
		return np.mean(self.get_data())

	def get_std(self):
		return np.std(self.get_data())

def printProgress(idx,list,item=None,message="",unit=""):
	progress = idx/float(len(list))
	sys.stdout.write("\r%s: %.0f %% (%s%s) %s" % (message,100*progress,str(item),unit,'#'*int(progress*16)+'-'*int(16-progress*16)))
	sys.stdout.flush()
def printDone():
	sys.stdout.write("[Done]\n")
	
def makeRandomColor():
	r = lambda: np.random.rand()	 #Make random color
	return (r(),r(),r())
	
def makeHeader(params):
	return "Notes:"+','.join([ '='.join([str(element) for element in tup]) for tup in params.items()])

def makeYamlHeader(params):
	return "YAML:\n"+yaml.dump(params)
	
def readHeader(filename):
	parameters = []
	with open(filename, 'r') as f:
		first_line = f.readline()
		if first_line.find("# Notes")>-1:
			parameters = first_line.replace('\n','').split(":")[1].split(",")
			parameters = dict([(param.split('=')[0],param.split('=')[1]) for param in parameters])
			return parameters
		if first_line.find("# YAML:")>-1:
			lines = []
			line = f.readline()
			while line[0]=="#":
				lines.append(line[2:])
				line = f.readline()
			return yaml.load(''.join(lines))
		else:
			print "No header found in this file"
	return parameters
	
def saveYaml(params,filename):
	with open(filename,'w') as f:
		yaml.dump(params,f,default_flow_style=False)
	return

def savePickle(params,filename):
	with open(filename, 'wb') as f:
		cPickle.dump(params, f, -1)
	return

def loadYaml(filename="params.yaml"):
	with open(filename,'r') as f:
		try:
			return yaml.load(f, Loader=yaml.CLoader)
		except:
			print "Unknown error while loading file"
			return None

def loadPickle(filename):
	with open(filename, 'rb') as f:
		return cPickle.load(f)

def getAllParams(equipments):
	params = OrderedDict()
	params.update(loadYaml("params.yaml"))
	params.update({"date": time.strftime("%d-%m-%y")})
	params.update({"time": time.strftime("%H%M")})
	for equipment in equipments:
		params.update(equipment.getParams())
	return params

def saveThisConfig(equipmentList,comment=None):
	params = getAllParams(equipmentList)
	if comment: params.update({"comment":comment})
	filename = "%s %s %s(Config).yaml"%(params["cell"],params["date"],params["time"])
	saveYaml(params,filename=filename)