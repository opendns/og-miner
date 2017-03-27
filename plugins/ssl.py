import ssl
import time

class Plugin(object):
    def __init__(self, configuration):
        self.ssl_port = 443

    def process(self, profile, state, vertex):
        if 'type' not in vertex:
            return { 'error' : "No vertex type defined!" }

        properties = dict()

        if vertex['type'] == "domain":
            try:
                begin = time.time()
                properties['content'] = ssl.get_server_certificate((vertex['id'], self.ssl_port))
                properties['time'] = time.time() - begin
            except Exception as e:
                properties['error'] = str(e)
 
        return { "properties": properties, "neighbors" : [] }
