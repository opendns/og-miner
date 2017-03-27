import json
import lxml, lxml.etree
import datetime, time
import threading

import core.graph.interface

class Graph(core.graph.interface.Graph):

    def __init__(self, **kwargs):
        super(Graph, self).__init__(**kwargs)

        self.__meta = dict()
        self.__properties = dict()
        self.__vertices = dict()
        self.__edges = dict()

        self.__mutex = threading.Lock()
        self.__tokens = list()

    # ----- Count Methods -----

    def count_vertices(self):
        return len(self.__vertices)

    def count_edges(self):
        return len(self.__edges)

    def count_tokens(self):
        return len(self.__tokens)

    # -----  Update Methods -----

    def update_vertex(self, **kwargs):
        assert "id" in kwargs, "update_vertex: id not defined!"

        nid = kwargs.pop('id')

        with self.__mutex:
            if nid in self.__vertices:
                exists = True
                self.__vertices[nid].update(kwargs)
            else:
                exists = False
                self.__vertices[nid] = kwargs

        if exists:
            self.log(u"update_vertex: Updated vertex {0} already existed.".format(nid))

        return nid

    def update_edge(self, **kwargs):
        assert "src" in kwargs, "update_edge: src not defined!"
        assert "dst" in kwargs, "update_edge: dst not defined!"

        src = kwargs.pop('src')
        dst = kwargs.pop('dst')

        with self.__mutex:
            if (src, dst) in self.__edges:
                exists = True
                self.__edges[(src, dst)].update(kwargs)
            else:
                exists = False
                self.__edges[(src, dst)] = kwargs

        if exists:
            self.log(u"update_edge: Updated edge ({0}, {1}) already existed.".format(src, dst))

        return (src, dst)

    def update_index(self, **kwargs):
        # TODO: Indices not supported. This is currently no-op
        return

    def update_token(self, nid, token, **kwargs):
        token_data = kwargs
        token_data['id'] = token.value
        token_data['vertex'] = nid
        token_data['ts'] = datetime.datetime.utcnow()

        try: token_data['ttl'] = float(token_data['ttl'])
        except: pass

        with self.__mutex:
            result = None
            for token in self.__tokens:
                if token['id'] == token_data['id'] and token['vertex'] == nid:
                    result = token
                    break
            if result is None:
                self.__tokens.append(token_data)
            else:
                result.update(token_data)

    # ----- Remove Methods -----

    def clear(self):
        self.__meta = dict()
        self.__properties = dict()
        self.__vertices = dict()
        self.__edges = dict()

    def remove_vertex(self, nid):
        raise NotImplementedError # TODO

    def remove_edge(self, src, dst):
        raise NotImplementedError # TODO

    # ----- Query Methods -----

    def _match(self, element, query):
        for k, v in query.items():
            if isinstance(v, dict):
                raise NotImplementedError #TODO : Complex queries not supported
            if k not in element:
                return False
            if element[k] != v:
                return False
        return True

    def _vertex_iterator(self):
        for key, properties in self.__vertices.items():
            vertex = properties
            vertex["id"] = key
            yield vertex

    def _edge_iterator(self):
        for key, properties in self.__edges.items():
            edge = properties
            edge["src"] = key[0]
            edge["dst"] = key[1]
            yield edge

    def _query_collection(self, collection, query, projection, **kwargs):
        # TODO: Pagination (offset, limit)
        if projection:
            raise NotImplementedError

        for element in collection:
            if self._match(element, query):
                yield element

    def query_vertices(self, query={}, projection=None, **kwargs):
        return self._query_collection(self._vertex_iterator(), query, projection, **kwargs)

    def query_edges(self, query={}, projection=None, **kwargs):
        return self._query_collection(self._edge_iterator(), query, projection, **kwargs)

    def query_tokens(self, query={}, projection=None, **kwargs):
        return self._query_collection(self.__tokens, query, projection, **kwargs)

    # ----- Other Methods -----

    def extract(self):  # TODO : Should be an exporter plugin
        graph = {
            'meta' : self.__meta,
            'properties' : self.__properties
        }

        graph['nodes'] = list()
        for key in sorted(self.__vertices.keys()):
            vertex = self.__vertices[key]
            vertex.update({ 'id' : key })
            graph['nodes'].append(vertex)

        graph['edges'] = list()
        for key in sorted(self.__edges.keys()):
            edge = self.__edges[key]
            edge.update({ 'src' : key[0], 'dst' : key[1] })
            graph['edges'].append(edge)

        graph['tokens'] = list()
        for item in self.__tokens:
            token = item.copy()
            token['ts'] = time.mktime(token['ts'].timetuple())
            graph['tokens'].append(token)

        return graph