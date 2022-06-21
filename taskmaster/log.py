class Log:
	cache='/tmp/taskmaster.log'

	def Info(*msg, end='\n'):
		log.print('\33[1;36m', '[*] ', msg, end, True)

	def Warning(*msg, end='\n'):
		log.print('\33[1;33m', '[!] ', msg, end, True)

	def RInfo(*msg, end='\n'):
		log.print('\33[1;36m', '[*] ', msg, end, False)

	def RWarning(*msg, end='\n'):
		log.print('\33[1;33m', '[!] ', msg, end, False)

	def Error(*msg, end='\n'):
		log.print('\33[1;31m', '[!] ', msg, end, False)

	def Join(msgs):
		fin = ''
		for msg in msgs:
			fin += str(msg)
		return fin

	def print(color, init, msgs, end, verbose_only):
		date = '[{}]'.format(strftime("%H:%M:%S", gmtime(time() - TRUN)))
		msg = log.Join(msgs)
		print(color, init, msg, "\033[00m", end=end, sep='')
		if log.cache != '':
			open(log.cache, 'a').write(date + init + str(msg) + '\n')