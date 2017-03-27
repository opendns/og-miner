import dns.resolver

class Plugin(object):
    def __init__(self, configuration):
        self.resolver = dns.resolver.Resolver()

        if 'nameservers' in configuration:
            self.resolver.nameservers = configuration['nameservers']

    def process(self, profile, state, vertex):
        if 'type' not in vertex:
            return { 'error' : "No vertex type defined!" }

        properties = dict()
        neighbors = list()

        if vertex['type'] == "domain":
            try:
                domain = vertex['id']
                answer = self.resolver.query(domain)
                for item in answer:
                    neighbors.append((
                        { 'type' : 'ip', 'id' : str(item) },
                        { 'type' : 'a-record' }
                    ))
            except:pass

        return { "properties": properties, "neighbors" : neighbors }
