#!/usr/bin/env python

import sys
import os
import json
import argparse
import zmq
import time

import colorama

import core.graph.memory
import core.engine
import core.token
import core.encoder

def print_line():
    print(colorama.Style.DIM + "-" * 80 + colorama.Style.RESET_ALL)

def print_item(item_type, message):
    print(
        colorama.Style.DIM + "["
        + colorama.Style.RESET_ALL + "{0}".format(item_type)
        + colorama.Style.DIM + "] " + colorama.Style.RESET_ALL + "{0}".format(message)
    )

def generator_from_element(element):
    yield element

def generator_from_file(filename, element_type):
    with open(filename, "rU") as infile:
        for line in infile:
            split = line.strip().split()
            if len(split) == 0 or len(split[0]) == 0 or split[0][0] == "#":
                continue
            yield { 'id' : split[0], 'type' : element_type }

def generator_from_json(filename):
    with open(filename, "rU") as json_file:
        for line in json_file:
            try:
                strip = line.strip()
                if len(strip) == 0:
                    continue
                yield json.loads(line.strip())
            except Exception as e:
                print("Invalid JSON task, skipped.")
                print("{}".format(e))

def generator_from_query(graph, query):
    try:
        json_query = json.loads(query)
    except:
        print(colorama.Fore.YELLOW + "Invalid graph vertex query!" + colorama.Fore.RESET)

    for vertex in graph.query_vertices(json_query):
        vertex['depth'] = 0
        yield vertex

def generator_from_zmq_pull(context, host):
    socket = context.socket(zmq.PULL)
    # TODO: Configure socket with clean properties to avoid message overload.
    if host.endswith('/'):
        host = host[:-1]
    print_item("+", "Binding ZMQ pull socket : " + colorama.Fore.CYAN + "{0}".format(host) + colorama.Style.RESET_ALL)
    socket.bind(host)

    while True:
        try:
            message = socket.recv(flags=zmq.NOBLOCK)
        except zmq.Again as e:
            message = None
        if message is None:
            yield None # NOTE: We have to make the generator non blocking.
        else:
            task = json.loads(message)
            yield task
 
if __name__ == "__main__":

    colorama.init()

    print("Miner Script (version 3.8)")

    parser = argparse.ArgumentParser()

    parser.add_argument('--domain', help='Mine from a domain.')
    parser.add_argument('--domains', help='Mine from a list of domains in a file.')
    parser.add_argument('--url', help='Mine from a URL.')
    parser.add_argument('--urls', help='Mine from a list of URLs in a file.')
    parser.add_argument('--ip', help='Mine from an IP.')
    parser.add_argument('--ips', help='Mine from a list of IPs in a file.')
    parser.add_argument('--asn', help='Mine from an ASN.')
    parser.add_argument('--asns', help='Mine from a list of ASNs in a file.')
    parser.add_argument('--email', help='Mine from an email address.')
    parser.add_argument('--emails', help='Mine from a list of emails in a file.')
    parser.add_argument('--hash', help='Mine from a hash.')
    parser.add_argument('--hashes', help='Mine from a list of hashes in a file.')
    parser.add_argument('--regex', help="Mine from a regex.")
    parser.add_argument('--regexes', help="Mine from a list of regexes in a file.")
    parser.add_argument('--query', help="Mine from graph vertices matching the query")
    parser.add_argument('--json', help="Load custom tasks from a JSON file.")
    parser.add_argument('--pull', help="Pull entries to mine from a ZMQ stream.")
    parser.add_argument('--push', help='Push mined results to a ZMQ stream.')

    parser.add_argument('--config', default='conf.json', help='Select a configuration file.')
    parser.add_argument('--profile', default='default', help='Select a mining profile.')
    parser.add_argument('--token', default=None, help='Set the mining token.')
    parser.add_argument('--ttl', default=None, help="Set the mining token TTL (in seconds).")
    parser.add_argument('--title', help='Set the dataset title.')
    parser.add_argument('--pipeline', help="Set the list of active plugins.")
    parser.add_argument('--depth', help='Set the mining maximum depth.')
    parser.add_argument('--workers', default=4, help="Set the number of worker threads.")
    parser.add_argument('--qlimit', default=None, help="Set the queue size soft limit.")
    parser.add_argument('--output', default='result.json', help='Set the output JSON filename.')
    parser.add_argument('--mongo', default=None, help='Use MongoDB as a graph database.')
    parser.add_argument('--reset', action='store_const', const=True, default=False, help="Reset graph.")
    parser.add_argument('--no-output', action='store_const', const=True, default=False, help="No JSON output.")
    parser.add_argument('--stats', action='store_const', const=True, default=False, help="Compute performance metrics.")

    args = parser.parse_args()

    # --------------------------------------------------------------------

    configuration = dict()
    seeders = list()

    with open(args.config, "rU") as conf_file:
        try:
            configuration = json.load(conf_file)
        except Exception, e:
            print("[Error] Your configuration file seems corrupt!")
            print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)
            sys.exit(0)

        if args.profile is not None:
            profile_path = "{0}/profiles/{1}.json".format(os.path.dirname(os.path.realpath(args.config)), args.profile)
            with open(profile_path, "rU") as profile_file:
                profile = json.load(profile_file)
                configuration.update(profile)

    # ------------------------------------------------------------------------

    print_line()

    print_item("+", "Loading miner configuration ...")

    if args.mongo is not None:
        split = args.mongo.split(':')

        port = 27017
        db = "miner"

        if len(split) >= 0:
            host = split[0]
        if len(split) >= 2:
            port = int(split[1])
        if len(split) >= 3:
            db = split[2]

        print_item("+", "Connecting to graph mongo database ...")
        print("    - Host: " + colorama.Fore.CYAN + "{0}".format(host) + colorama.Style.RESET_ALL)
        print("    - Port: " + colorama.Fore.CYAN + "{0}".format(port) + colorama.Style.RESET_ALL)
        print("    - Database: " + colorama.Fore.CYAN + "{0}".format(db) + colorama.Style.RESET_ALL)
        graph = core.graph.mongo.Graph(host=host, port=int(port), db=db)

        if args.reset:
            print_item("+", "Resetting graph ...")
            graph.clear()
    else:
        print_item("+", "Creating graph in local memory ...")
        graph = core.graph.memory.Graph()

    # ------------------------------------------------------------------------

    if args.depth is not None:
        if args.depth == "infinite":
            configuration['parameters']['depth'] = "infinite"
        else:
            configuration['parameters']['depth'] = int(args.depth)
    elif 'depth' not in configuration['parameters']:
        configuration['parameters']['depth'] = 0

    if args.stats is not None:
        configuration['parameters']['stats'] = args.stats

    if args.pipeline is not None:
        configuration['parameters']['pipeline'] = args.pipeline.split(',')

    if args.domain is not None:
        seeders.append(generator_from_element({ 'type' : 'domain', 'id' : args.domain }))
    if args.domains is not None:
        seeders.append(generator_from_file(args.domains, 'domain'))

    if args.url is not None:
        seeders.append(generator_from_element({ 'type' : 'url', 'id' : args.url }))
    if args.urls is not None:
        seeders.append(generator_from_file(args.urls, 'url'))

    if args.ip is not None:
        seeders.append(generator_from_element({ 'type' : 'ip', 'id' : args.ip }))
    if args.ips is not None:
        seeders.append(generator_from_file(args.ips, 'ip'))

    if args.asn is not None:
        seeders.append(generator_from_element({ 'type' : 'asn', 'id' : args.asn }))
    if args.asns is not None:
        seeders.append(generator_from_file(args.emails, 'asn'))

    if args.email is not None:
        seeders.append(generator_from_element({ 'type' : 'email', 'id' : args.email }))
    if args.emails is not None:
        seeders.append(generator_from_file(args.emails, 'email'))

    if args.hash is not None:
        seeders.append(generator_from_element({ 'type' : 'hash', 'id' : args.hash }))
    if args.hashes is not None:
        seeders.append(generator_from_file(args.hashes, 'hash'))

    if args.regex is not None:
        seeders.append(generator_from_element({ 'type' : 'regex', 'id' : args.regex }))
    if args.regexes is not None:
        seeders.append(generator_from_file(args.regexes, 'regex'))

    if args.json is not None:
        seeders.append(generator_from_json(args.json))

    if args.query is not None:
        seeders.append(generator_from_query(graph, args.query))

    output_socket = None
    if args.pull is not None or args.push is not None:
        context = zmq.Context()

        if args.pull is not None:
            seeders.append(generator_from_zmq_pull(context, args.pull))

        if args.push is not None:
            output_socket = context.socket(zmq.PUSH)
            host = args.push
            if host.endswith('/'):
                host = host[:-1]
            print_item("+", "Connecting ZMQ push socket : " + colorama.Fore.CYAN + "{0}".format(host) + colorama.Style.RESET_ALL)
            output_socket.connect(host)

    # ------------ Token Configuration ---------------

    try: tokens = configuration['parameters']['tokens']
    except: configuration['parameters']['tokens'] = dict()

    try: token_uuid = configuration['parameters']['tokens']['uuid']
    except: configuration['parameters']['tokens']['uuid'] = str(core.token.Token())

    try: token_ttl = configuration['parameters']['tokens']['ttl']
    except: configuration['parameters']['tokens']['ttl'] = None

    try: rules = configuration['parameters']['tokens']['rules']
    except: configuration['parameters']['tokens']['rules'] = dict()

    if args.token is not None:
        try:
            configuration['parameters']['tokens']['uuid'] = str(core.token.Token(args.token))
        except:
            print(colorama.Fore.YELLOW + "Wrong token format! Exiting" + colorama.Fore.RESET)
            sys.exit(0)

    if args.ttl is not None:
        try:
            configuration['parameters']['tokens']['ttl'] = float(args.ttl)
        except:
            print(colorama.Fore.YELLOW + "Wrong TTL format! Exiting" + colorama.Fore.RESET)
            sys.exit(0)

    print_item("+", "Token configuration")
    print("    - {c}default{r} {sep} uuid:{c}{uuid}{r}, ttl:{c}{ttl}{r}".format(
        c=colorama.Fore.CYAN,
        r=colorama.Fore.RESET,
        sep=colorama.Style.DIM + "->" + colorama.Style.RESET_ALL,
        uuid=configuration['parameters']['tokens']['uuid'] + colorama.Fore.RESET,
        ttl=configuration['parameters']['tokens']['ttl']
    ))

    for vertex_type, token_data in configuration['parameters']['tokens']['rules'].items():
        print("    - {c}{vtype}{r} {sep} {vrule}".format(
            c=colorama.Fore.CYAN,
            r=colorama.Fore.RESET,
            vtype=vertex_type,
            sep=colorama.Style.DIM + "->" + colorama.Style.RESET_ALL,
            vrule=", ".join(
                [ "{}:{}{}{}".format(k, colorama.Fore.CYAN, v, colorama.Fore.RESET) for k, v in token_data.items() ]
            )
        ))

    # ------------------------------------------------------------------------

    try:
        qlimit = int(args.qlimit)
    except:
        qlimit = None

    engine = core.engine.Engine(
        configuration,
        graph,
        workers=args.workers,
        seeders=seeders,
        output_socket=output_socket,
        qlimit=qlimit
    )

    engine.prepare_workers()
    print_item("+", "Starting engine ...")
    print_line()
    engine.start()
    print_line()
    engine.stop_workers()
    
    # ------------------------------------------------------------------------

    if not args.no_output:

        data = engine.graph.extract()

        depths = dict()
        for token in data['tokens']:
            try: depth = token['depth']
            except: depth = None
            if depth not in depths:
                depths[depth] = 1
            else:
                depths[depth] += 1
        data['properties']['bfs_signature'] = depths
        print("BFS Signature: {0}".format(depths))

        if not configuration['parameters']['stats']:
            del data['tokens']

        if args.title is not None:
            data['meta']['title'] = args.title

        print("Writing graph to '{0}' ...".format(args.output))
        with open(args.output, "w") as outfile:
            json.dump(data, outfile, indent=4, cls=core.encoder.Encoder)
 
    print("Done.")
