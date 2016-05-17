import time
import serial

class LightCtrl(object):
	def __init__(self,comPort='com4'):
		try:
			self.ser = ser = serial.Serial(port=comPort,timeout=5)
		except serial.serialutil.SerialException:
			#no serial connection
			self.ser = None
		else:
			pass
	
	def write(self,command):
		self.ser.write(command+"\n")
		return
		
	def __del__(self):
		if self.ser:
			self.ser.close()

	def white(self,level):
		self.write("w:%d"%level)
		return
	
if __name__=='__main__':
	lightCtrl = LightCtrl()