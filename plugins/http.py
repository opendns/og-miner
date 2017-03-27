import requests
import time

class Plugin(object):
    def __init__(self, configuration):
        self.connect_timeout = 1
        self.read_timeout = 5

        self.session = requests.Session()
        self.adapter = requests.adapters.HTTPAdapter(max_retries=0)
        self.session.mount("http://", self.adapter)
        self.session.mount("https://", self.adapter)

    def process(self, profile, state, vertex):
        if 'type' not in vertex:
            return { 'error' : "No vertex type defined!" }

        properties = dict()

        if vertex['type'] == "domain" or vertex['type'] == "url" or vertex['type'] == "ip":

            try:                
                url = vertex['id']
                if not url.startswith("http://") and not url.startswith('https://'):
                    url = "http://{0}".format(url)

                begin = time.time()
                properties['content'] = requests.get(url, verify=False, timeout=(self.connect_timeout, self.read_timeout)).text
                properties['time'] = time.time() - begin

            except Exception as e:
                properties['error'] = type(e).__name__

        return { "properties": properties, "neighbors" : [] }
