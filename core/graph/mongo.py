import json
import pprint as pp
import pymongo
import datetime, time

import core.graph.interface
import core.token

class Graph(core.graph.interface.Graph):
    def __init__(self, **kwargs):
        super(Graph, self).__init__(**kwargs)

        self.host = kwargs['host']
        self.port = kwargs['port']
        self.db = kwargs['db']
        self.client = pymongo.MongoClient(self.host, self.port)

        self.__meta = self.client[self.db].meta
        self.__properties = self.client[self.db].properties
        self.__vertices = self.client[self.db].vertices
        self.__edges = self.client[self.db].edges
        self.__tokens = self.client[self.db].tokens

        # NOTE: Create indexes to facilitate vertex/edge/token queries.
        self.update_index(type='vertex', key='id')
        self.update_index(type='edge', key='src')
        self.update_index(type='edge', key='dst')
        self.update_index(type='token', key='ts')
        self.update_index(type='token', key='vertex')

    # ----- Count Methods -----

    def count_vertices(self):
        return self.__vertices.count()

    def count_edges(self):
        return self.__edges.count()

    def count_tokens(self):
        return self.__tokens.count()

     # ----- Update Methods -----

    def update_vertex(self, **kwargs):
        assert "id" in kwargs, "update_vertex: id not defined!"

        nid = kwargs.pop('id')

        update = {
            "$setOnInsert" : { "id" : nid }
        }
        if kwargs:
            update["$set"] = kwargs

        result = self.__vertices.update_one({'id': nid}, update, upsert=True)

        if result.raw_result['updatedExisting']:
            self.log(u"update_vertex: Updated vertex {0} already existed.".format(nid))

        return nid

    def update_edge(self, **kwargs):
        assert "src" in kwargs, "update_edge: src not defined!"
        assert "dst" in kwargs, "update_edge: dst not defined!"

        src = kwargs.pop('src')
        dst = kwargs.pop('dst')

        update = {
            "$setOnInsert" : { "src": src, "dst": dst }
        }
        if kwargs:
            update["$set"] = kwargs

        result = self.__edges.update_one({ 'src': src, 'dst': dst }, update, upsert=True)

        if result.raw_result['updatedExisting']:
            self.log(u"update_edge: Updated edge ({0}, {1}) already existed.".format(src, dst))

        return (src, dst)

    def update_index(self, **kwargs):
        assert "key" in kwargs, "update_index: key not defined!"
        assert "type" in kwargs, "update_index: type not defined!"
        assert kwargs['type'] in ['vertex', 'edge', 'token'], "update_index: type needs to be vertex, edge or token!"

        if kwargs["type"] == "vertex":
            self.__vertices.create_index([ (kwargs['key'], pymongo.ASCENDING) ])
        elif kwargs["type"] == "edge":
            self.__edges.create_index([ (kwargs['key'], pymongo.ASCENDING) ])
        else:
            self.__tokens.create_index([ (kwargs['key'], pymongo.ASCENDING) ])

        return (kwargs['type'], kwargs['key'])

    def update_token(self, nid, token, **kwargs):
        token_data = kwargs
        token_data['id'] = token.value
        token_data['vertex'] = nid
        token_data['ts'] = datetime.datetime.utcnow()

        try: token_data['ttl'] = float(token_data['ttl'])
        except: pass

        result = self.__tokens.replace_one(
            {'id': token_data['id'], 'vertex': nid},
            token_data,
            upsert=True)

    # ----- Remove Methods -----

    def clear(self):
        self.__meta.remove()
        self.__properties.remove()

        self.__vertices.remove()
        self.__edges.remove()
        self.__tokens.remove()

    def remove_vertex(self, nid):
        raise NotImplementedError # TODO

    def remove_edge(self, src, dst):
        raise NotImplementedError # TODO

    # ----- Query Methods -----

    def _query_collection(self, collection, query, projection, **kwargs):

        if projection:
            iterator = collection.find(query, projection)
        else:
            iterator = collection.find(query)

        try:
            sort_key, sort_order = kwargs['sort']
            iterator = iterator.sort(sort_key, pymongo.ASCENDING if sort_order > 0 else pymongo.DESCENDING)
        except:
            pass

        try:
            offset = int(kwargs['offset'])
            iterator = iterator.skip(offset)
        except:
            pass

        try:
            limit = int(kwargs['limit'])
            iterator = iterator.limit(limit)
        except:
            pass

        for element in iterator:
            del element["_id"]
            yield element

    def query_vertices(self, query={}, projection=None, **kwargs):
        return self._query_collection(self.__vertices, query, projection, **kwargs)

    def query_edges(self, query={}, projection=None, **kwargs):
        return self._query_collection(self.__edges, query, projection, **kwargs)

    def query_tokens(self, query={}, projection=None, **kwargs):
        return self._query_collection(self.__tokens, query, projection, **kwargs)

    # ----- Other Methods -----

    def extract(self): # TODO : Should be an exporter plugin
        graph = {
            'meta': {},  # self.__meta,
            'properties': {}  # self.__properties
        }

        graph['nodes'] = list()
        for v in self.__vertices.find().sort('id', pymongo.ASCENDING):
            v.pop("_id")  # Remove MongoDB document ID
            graph['nodes'].append(v)

        graph['edges'] = list()
        for e in self.__edges.find().sort("src", pymongo.ASCENDING):
            e.pop("_id")  # Remove MongoDB document ID
            graph['edges'].append(e)

        graph['tokens'] = list();
        for t in self.__tokens.find().sort('id', pymongo.ASCENDING):
            t.pop("_id")  # Remove MongoDB document ID
            t['id'] = str(t['id'])
            t['ts'] = time.mktime(t['ts'].timetuple())
            graph['tokens'].append(t)

        return graph
