from timeout import escapableSleep
import sys, threading, Queue, time
import numpy as np

log_separator = ","

class DataImu(object):
	def __init__(self,length,variables):
		self.queue = Queue.Queue()
		self.ptr = 0
		self.array = np.zeros((length,variables),dtype=np.float64)

	def get_data(self):
		return self.array[0:self.ptr,:]

class DataProducer(threading.Thread):
	queue = None

	def __init__(self,header,getters,delay=0.1):
		threading.Thread.__init__(self)
		self.daemon = True
		self.running = True
		self.header = header
		self.getters = getters
		self.delay = delay

	def stop(self):
		self.running = False

	def run(self):
		print("Data producer starting")
		while self.running:
			data = []
			for getter in self.getters:
				if type(getter) is tuple:
					data.append(getattr(*getter))
				else:
					data.append(getter())
			time.sleep(self.delay)
			self.queue.put(data)

class DataConsumer(threading.Thread):
	num_point_drawn = 1000

	def __init__(self,logfile=None, fileheader=None):
		threading.Thread.__init__(self)
		self.daemon = True
		self.running = True
		self.logfile = logfile
		self.logfile.write(log_separator.join(fileheader)+"\n")
		self.data = DataImu(self.num_point_drawn,len(fileheader))

	def is_full(self):
		return self.data.ptr >= self.num_point_drawn

	def run(self):
		print("DataConsumer waiting for data")
		while self.running:
			data = self.data.queue.get()
			if self.logfile:
				self.logfile.write(log_separator.join(["%.6f"%(item) for item in data])+"\n")
			if self.is_full():
				self.data.array = np.roll(self.data.array,-1,0)
				self.data.array[-1] = data
			else:
				self.data.array[self.data.ptr] = data
				self.data.ptr += 1

	def empty(self):
		self.data.ptr = 0

	def stop(self):
		self.logfile = None
		self.running = False