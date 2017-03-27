import shodan
import sys

class Plugin(object):
    def __init__(self, configuration):
        self.api = shodan.Shodan(configuration['api_key'])

    def process(self, profile, state, vertex):
        if 'type' not in vertex:
            return { 'error' : "No vertex type defined!" }

        if vertex['type'] == "ip":
            return self.explore_ip(vertex, profile)

        return { "properties": {}, "neighbors" : [] }

    def explore_ip(self, vertex, profile):
        properties = dict()
        neighbors = list()

        ip = vertex['id']

        try:
            properties = self.api.host(ip)

            properties.pop('ip_str') # Redundant
            # NOTE: Removing 'data' field as it contains too much info for now and makes results explode.
            # Definitely interesting to use it in the future though
            properties.pop('data')

            for port in properties['ports']:
                neighbors.append((
                    { 'type' : 'port', 'id' : str(port) },
                    { 'type' : 'ip -> port' }
                ))
            properties.pop('ports')

            asn = str(properties['asn'])
            if asn.startswith("AS"):
                asn = asn[2:]
            neighbors.append((
                { 'type' : 'asn', 'id' : asn },
                { 'type' : 'ip -> asn'}
            ))
            properties.pop('asn')

        except:
           pass

        return { "properties" : properties, "neighbors" : neighbors }

