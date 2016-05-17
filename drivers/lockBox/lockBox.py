import time
import serial

class LockBox(object):
	def __init__(self,comPort='com13'):
		try:
			self.ser = ser = serial.Serial()
			ser.port = comPort
			ser.timeout = 5
			ser.setDTR(False)
			ser.open()
		except serial.serialutil.SerialException:
			#no serial connection
			self.ser = None
		else:
			pass

	def __del__(self):
		if self.ser:
			self.ser.close()

	def send(self, command):
		self.ser.write(command+"\r\n")

	def query(self, command):
		self.send(command)
		time.sleep(0.020)
		return self.ser.readline()[:-2]

	@property
	def lock(self):
		return bool(int(self.query("LOCK?")))

	@lock.setter
	def lock(self,state):
		if state:
			self.send("ON")
		else: self.send("OFF")
	
if __name__=='__main__':
	lockBox = LockBox()