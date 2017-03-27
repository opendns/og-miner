import colorama

class Object(object):

	def print_line(self):
	    print(colorama.Style.DIM + "-" * 80 + colorama.Style.RESET_ALL)

	def print_item(self, item_type, message):
	    print(
	        colorama.Style.DIM + "["
	        + colorama.Style.RESET_ALL + "{0}".format(item_type)
	        + colorama.Style.DIM + "] " + colorama.Style.RESET_ALL + "{0}".format(message)
	    )