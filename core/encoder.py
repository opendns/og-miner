import json
import bson.json_util

class Encoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, set):
			return list(obj)
		return bson.json_util.default(obj)
