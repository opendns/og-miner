import core.graph.memory

# TODO: Rename this plugin to "union" or "merge" + Mongo support.

class Plugin(object):
    def __init__(self, configuration):
        self.filename = configuration['filename']
        self.graph = core.graph.memory.Graph()
        self.graph.load_json(self.filename)

    def process(self, profile, state, vertex):
        if 'type' not in vertex:
            return { 'error' : "No vertex type defined!" }

        properties = dict()
        neighbors = list()

        query = list(self.graph.query_vertices({ "id": vertex['id'] }))

        if len(query) > 0:
            properties = query[0].copy()
            properties.pop('id', None)
            properties.pop('type', None)

        for edge in self.graph.query_edges({ "src" : vertex['id'] }):
            n_vertex = list(self.graph.query_vertices({ "id": edge['dst'] }))[0] 
           
            neighbors.append((
                { 'type' : n_vertex['type'], 'id' : edge['dst'] },
                { 'type' : edge['type'] }
            ))

        return { "properties": properties, "neighbors" : neighbors }
