"""
Listen to serial, return most recent numeric values
Lots of help from here:
http://stackoverflow.com/questions/1093598/pyserial-how-to-read-last-line-sent-from-serial-device
"""

import time
import serial

class Stepper(object):
	def __init__(self,comPort='com15'):
		try:
			self.ser = serial.Serial(port=comPort,baudrate=19200,timeout=5)
			time.sleep(3)
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

	def freeRunL(self):
		self.send("L")
		return

	def freeRunR(self):
		self.send("R")
		return

	def oneStepL(self):
		self.send("+")
		return

	def oneStepR(self):
		self.send("-")
		return

	def stop(self):
		self.send("S")
		return

	@property
	def position(self):
		return int(self.query("P?"))
		
if __name__=='__main__':
	stepper = Stepper()