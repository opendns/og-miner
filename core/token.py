import uuid

#TODO: TTL logic should probably be implemented inside the Token class

class Token(object):

	def __init__(self, value=None):
		if value is None:
			self.value = uuid.uuid4() # NOTE: Random UUID
		else:
			self.value = uuid.UUID(value)

	def __str__(self):
		return str(self.value)