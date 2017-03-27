#!/usr/bin/env python

import argparse
import json
import uuid
import time
import threading

import zmq

import redis

import falcon
from wsgiref import simple_server

from pprint import pprint as pp

class MinerClient(threading.Thread):

    def __init__(self, push, pull, redis_conf):
        super(MinerClient, self).__init__()

        print("Connecting to Redis cache {} ...".format(redis_conf))
        redis_host, redis_port, redis_db = redis_conf.split(":")
        self.redis = redis.StrictRedis(host=redis_host, port=int(redis_port), db=int(redis_db))
        self.redis.setnx('transaction', 0)
        # NOTE: Expiration times for pending/processed tasks in seconds.
        self.transaction_expiration = 60 * 60
        self.result_expiration = 60 * 10

        context = zmq.Context()

        print("Connecting to push socket '{}' ...".format(push))
        self.push = context.socket(zmq.PUSH)
        self.push.connect(push)

        print("Binding to pull socket '{}' ...".format(pull))
        self.pull = context.socket(zmq.PULL)
        self.pull.bind(pull)

    def push_task(self, task):
        uid = self.redis.incr('transaction')
        self.redis.setex(
            uid,
            self.transaction_expiration,
            json.dumps({
                "created" : time.time(),
                "status" : "processing"
            })
        )

        task["transaction"] = uid
        self.push.send_json(task)
        return uid

    def get_task(self, transaction_id):
        return self.redis.get(transaction_id)

    def run(self):
        while True:
            try:
                message = self.pull.recv(flags=zmq.NOBLOCK)
            except zmq.Again as e:
                message = None
            if message is not None:
                task = json.loads(message)
                self.redis.setex(
                    task['transaction'],
                    self.result_expiration,
                    json.dumps(task['data'])
                )

class MinerResource(object):
    def __init__(self, client):
        self.client = client

    def on_get(self, request, response):
        query = dict()
        request.get_param_as_int('transaction', store=query)

        if "transaction" in query:
            task = self.client.get_task(query['transaction'])
            if task is None:
                raise falcon.HTTPNotFound()
            else:
                response.body = task
                response.status = falcon.HTTP_200
        else:
            response.body = json.dumps({}, encoding='utf-8')
            response.status = falcon.HTTP_200

    def on_post(self, request, response):
        query = dict()
        try:
            raw_json = request.stream.read()
        except Exception as e:
            raise falcon.HTTPError(falcon.HTTP_400, 'Error', e.message)
 
        try:
            data = json.loads(raw_json, encoding='utf-8')
        except ValueError:
            raise falcon.HTTPError(falcon.HTTP_400, 'Malformed JSON')

        if "id" not in data:
            raise falcon.HTTPConflict('Task creation', "ID is not specified.")
        if "type" not in data:
            raise falcon.HTTPConflict('Task creation', "Type is not specified.")

        transaction = self.client.push_task({ "task" : "vertex", "data" : data })

        response.body = json.dumps({ "transaction" : transaction })
        response.status = falcon.HTTP_202

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--push', required=True, help='Define the miner ZMQ push connector.')
    parser.add_argument('--pull', required=True, help='Define the miner ZMQ pull connector.')
    parser.add_argument('--port', required=True, help='Define REST API port.')
    parser.add_argument('--redis', required=True, help='Define Redis host.')
    args = parser.parse_args()

    api = falcon.API()
    
    miner_client = MinerClient(args.push, args.pull, args.redis)
    miner_client.start()

    miner_resource = MinerResource(miner_client)

    api.add_route('/', miner_resource)
   
    httpd = simple_server.make_server('0.0.0.0', int(args.port), api)
    httpd.serve_forever()
