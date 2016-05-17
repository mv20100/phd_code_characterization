import sys, time, msvcrt

def readInput( caption, default, timeout = 5):
	start_time = time.time()
	sys.stdout.write('%s(%s):'%(caption, default));
	input = ''
	while True:
		if msvcrt.kbhit():
			chr = msvcrt.getche()
			if ord(chr) == 13: # enter_key
				break
			elif ord(chr) >= 32: #space_char
				input += chr
		if len(input) == 0 and (time.time() - start_time) > timeout:
			break

	print ''  # needed to move to next line
	if len(input) > 0:
		return input
	else:
		return default

def escapableSleep(timeout,verbose=True):
	start_time = time.time()
	if verbose: sys.stdout.write("Waiting %d s (press Q to cancel)"%(timeout))
	userStop = False
	while True:
		if msvcrt.kbhit():
			chr = msvcrt.getche()
			if ord(chr) == 113: # q_key
				userStop = True
				break
		if (time.time() - start_time) > timeout:
			break
	print ''  # needed to move to next line
	return userStop
