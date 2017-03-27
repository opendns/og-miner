#!/usr/bin/env python

import sys
import argparse
import json
import time, datetime
import uuid
import urllib

import core.graph.memory
import core.graph.mongo

import core.token

import falcon
from wsgiref import simple_server

class Vertices(object):
    def __init__(self, parent):
        super(Vertices, self).__init__()
        self.parent = parent

    def on_get(self, request, response):

        query = dict()
        request.get_param('id', store=query)
        request.get_param('type', store=query)

        sorting = dict()
        request.get_param('sort_by', store=sorting)
        request.get_param_as_int('sort_order', store=sorting)

        request.get_param_as_int('page', store=query)
        page = query.pop('page', 0)
        
        kwargs = {
            'offset' : page * self.parent.page_size,
            'limit' : self.parent.page_size
        }
        try: kwargs['sort'] = (sorting['sort_by'], sorting['sort_order'])
        except: pass

        results = list(
            self.parent.graph.query_vertices(
                query,
                **kwargs
            )
        )
        response.body = json.dumps(results)
        response.status = falcon.HTTP_200
        
class Vertex(object):
    def __init__(self, parent):
        super(Vertex, self).__init__()
        self.parent = parent

    def on_get(self, request, response, vertex_id):
        try:
            results = self.parent.graph.query_vertices({ "id" : vertex_id })
            response.body = json.dumps(list(results)[0])
            response.status = falcon.HTTP_200 
        except:
            raise falcon.HTTPNotFound()

    def on_post(self, request, response, vertex_id):
        query = dict()
        try:
            raw_json = request.stream.read()
        except Exception as e:
            raise falcon.HTTPError(falcon.HTTP_400, 'Error', e.message)
 
        try:
            data = json.loads(raw_json, encoding='utf-8')
        except ValueError:
            raise falcon.HTTPError(falcon.HTTP_400, 'Malformed JSON')
 
        data["id"] = vertex_id
        try:
            query = list(graph.query_vertices({ "id" : vertex_id }))
        except Exception as e:
            raise falcon.HTTPError(falcon.HTTP_400, 'Error', e.message)

        if len(query) > 0:
            raise falcon.HTTPConflict('Vertex Creation', "Vertex already exists.")
        
        try:
            result = graph.update_vertex(**data)
        except Exception as e:
            raise falcon.HTTPError(falcon.HTTP_400, 'Error', e.message)

        response.status = falcon.HTTP_200
        response.body = json.dumps({ "created" : result }, encoding='utf-8')

class Edges(object):
    def __init__(self, parent):
        super(Edges, self).__init__()
        self.parent = parent

    def on_get(self, request, response):
        query = dict()
        request.get_param('src', store=query)
        request.get_param('dst', store=query)
        request.get_param_as_int('page', store=query, min=0)

        page = query.pop('page', 0)

        results = list(
            self.parent.graph.query_edges(query,
                offset=page * self.parent.page_size,
                limit=self.parent.page_size
            )
        )

        response.body = json.dumps(results)
        response.status = falcon.HTTP_200

class Tokens(object):
    def __init__(self, parent):
        super(Tokens, self).__init__()
        self.parent = parent

    def on_get(self, request, response):
        query = dict()
        request.get_param('id', store=query)
        request.get_param('vertex', store=query)
        request.get_param_as_int('start', store=query)
        request.get_param_as_int('stop', store=query)
        request.get_param_as_int('page', store=query, min=0)

        if "id" in query:
            query['id'] = core.token.Token(query['id']).value
        
        ts_filter = dict()
        if "start" in query:
            ts_filter['$gte'] = datetime.datetime.utcfromtimestamp(query['start'])
            del query['start']
        if "stop" in query:
            ts_filter['$lte'] = datetime.datetime.utcfromtimestamp(query['stop'])
            del query['stop']
        if ts_filter:
            query['ts'] = ts_filter

        page = query.pop('page', 0)

        results = list(
            self.parent.graph.query_tokens(query,
                { "id" : 1, "vertex" : 1, "ts" : 1 },
                offset=page * self.parent.page_size,
                limit=self.parent.page_size
            )
        )
        
        epoch = datetime.datetime(1970, 1, 1)
        response.body = json.dumps([
            {
                "id" : str(x['id']),
                "vertex" : x['vertex'],
                "ts"  : (x['ts'] - epoch).total_seconds()
            } for x in results
        ])
        response.status = falcon.HTTP_200

class GraphAPI(falcon.API):
    def __init__(self, graph, version="alpha"):
        super(GraphAPI, self).__init__()
        self.version = version
        self.graph = graph
        self.page_size = 25

        #self.add_route('/meta', Meta(self))
        #self.add_route('/properties', Properties(self))
        self.add_route('/vertices', Vertices(self))
        self.add_route('/vertices/{vertex_id}', Vertex(self)) # NOTE: Doesn't find route if urlencoded
        self.add_route('/edges', Edges(self))
        self.add_route('/tokens', Tokens(self))
        
    def add_route(self, route, resource):
        super(GraphAPI, self).add_route("/{}{}".format(self.version, route), resource)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--mongo', help='Define the mongo graph.')
    parser.add_argument('--json', help='Define the JSON graph.')
    args = parser.parse_args()

    if args.mongo is None and args.json is None:
        print("Please define a graph to connect to.")
        sys.exit(-1)
        
    if args.mongo is not None:
        host, port, db = args.mongo.split(':')
        graph = core.graph.mongo.Graph(host=host, port=int(port), db=db)
    elif args.json is not None:
        graph = core.graph.memory.Graph()
        graph.load_json(args.json)

    api = GraphAPI(graph)
    
    httpd = simple_server.make_server('127.0.0.1', 8000, api)
    httpd.serve_forever()
