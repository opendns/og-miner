import whois

class Plugin(object):
    def __init__(self, configuration):
        pass

    def process(self, profile, state, vertex):
        if 'type' not in vertex:
            return { 'error' : "No vertex type defined!" }

        properties = dict()
        neighbors = list()

        if vertex['type'] == "domain":
            try:
                lookup = whois.query(vertex['id'])
                if lookup is not None:
                    for k, v in lookup.__dict__.items():
                        if isinstance(v, set):
                            properties[k] = list(v)
                        else:
                            properties[k] = v
            except Exception as e:
                print("Exception: {0}".format(e))

        return { "properties": properties, "neighbors" : neighbors }
