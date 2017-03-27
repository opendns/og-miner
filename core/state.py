class State(object):
	def __init__(self):
		#TODO : Set to custom initial state
		self.default = {
			"include" : True,
			"persist" : True,
			"notify" : True,
			"continue" : True,
			"message" : None,
			"abort" : False
		}
		self.value = None
		self.reset()

	def reset(self, key=None):
		''' Reset state field to default value. '''
		if key is None:
			self.value = self.default.copy()
		else:
			self.value[key] = self.default[key]

	def message(self, info):
		''' Prints a message after plugin execution. '''
		self.value['message'] = info

	def include(self, value):
		''' Define if plugin data is added to vertex. '''
		self.value['include'] = bool(value)

	def notify(self, value):
		''' Prevent notification to output stream. '''
		self.value['notify'] = bool(value)

	def persist(self, value):
		''' Define if pipeline result should be stored or not. Pipeline is not interrupted. '''
		self.value['persist'] = bool(value)

	def stop(self):
		''' Interrupt pipeline. Discard current neighbors.'''
		self.value['continue'] = False

	def discard(self):
		''' Interrupt pipeline, nothing is stored, no notification. '''
		self.value['abort'] = True
		self.value['continue'] = False
		self.value['persist'] = False
		self.value['notify'] = False
		self.value['include'] = False
