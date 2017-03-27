import threading
import random
import datetime, time
import uuid

import colorama

import core.token
import core.profile
import core.state

class Worker(object):

    def __init__(self, master, worker_id):
        self.worker_id = worker_id
        self.master = master
        self.graph = master.graph
        self.thread = threading.Thread(target=self.run)
        self.event = threading.Event()
        self.alive = True

    def safe_unicode(self, obj, *args):
        """ return the unicode representation of obj """
        try:
            return unicode(obj, *args)
        except UnicodeDecodeError:
            ascii_text = str(obj).encode('string_escape')
            return unicode(ascii_text)

    def is_alive(self):
        return self.alive
    def stop(self):
        self.alive = False

    def run(self):
  
        self.event.set()

        while self.is_alive():

            #print("DEBUG WORKER ALIVE")

            task = self.master.input_queue.get()
            if task is None:
                continue

            #print("DEBUG WORKER NEW TASK")

            if task['task'] == 'vertex':
                try:
                    print("Task {c}{task_id}{r} {sep} Worker {c}{worker_id}{r} {sep} Depth {c}{depth}{r} {sep} Type {c}{type}{r} {sep} ID {c}{id}{r}".format(
                        sep=colorama.Style.DIM + "-" + colorama.Style.RESET_ALL,
                        c=colorama.Fore.CYAN,
                        r=colorama.Style.RESET_ALL,
                        task_id=self.master.input_queue.count(),
                        worker_id=self.worker_id,
                        depth=task['depth'],
                        type=self.safe_unicode(task['data']['type']).encode("utf-8"),
                        id=self.safe_unicode(task['data']['id']).encode("utf-8")
                    ))
                except Exception as e:
                    print("Printing Exception")
                    print(task['data']['id'])
                    print(e)

            # TODO: Do we want edge debug info? We already show neighbors.
            '''
            elif task['task'] == 'edge':
                print("Task {0} - Worker {1} - Depth {2} - Edge: {3} -> {4}".format(
                    self.master.count_tasks(),
                    self.worker_id,
                    task['data']['depth'],
                    task['data']['src'],
                    task['data']['dst']
                ))
            '''

            self.process_task(task)
            self.master.input_queue.pop()

        self.event.set()
    
    def compute_new_token(self, graph, **kwargs):
        old_token = None
        require_new_token = False
        reason = None

        token_conf = kwargs['token_conf']
        depth = kwargs['depth']
        vertex = kwargs['vertex']

        token_uuid = uuid.UUID(token_conf["uuid"])

        # Find existing token in graph
        if "vertex" in kwargs:
            for t in graph.query_tokens({ "vertex" : vertex['id'] }):
                if t['id'] != token_uuid:
                    continue
                old_token = t
                break
        # TODO : Find edge token

        if old_token is None:
            require_new_token = True
            reason = None # NOTE: Old token not found, just creating one.
        else:
            if "ttl" in old_token and old_token['ttl'] is not None:
                utc_now = datetime.datetime.utcnow()
                ts = old_token['ts']
                ttl = datetime.timedelta(seconds=float(old_token['ttl']))
                expiration_date = ts + ttl
                expired = expiration_date <= utc_now
                if not expired:
                    delta_time = (ts + ttl) - utc_now
                else:
                    delta_time = utc_now - (ts + ttl)
            else:
                # NOTE: We couldn't get TTL data, we assume no expiration.
                expired = False
                delta_time = None

            if not expired:
                require_new_token = False
                if delta_time is None:
                    reason = "Marked, skipping."
                else:
                    reason = "Marked, token expires in {}, skipping.".format(delta_time)
            else:
                require_new_token = True
                reason = "Token expired {} ago, reprocessing.".format(delta_time)

        if require_new_token:
            new_token = core.token.Token(token_conf['uuid'])
            new_token.data = { "depth" : depth, "ttl" : token_conf['ttl'] }
            if vertex['type'] in token_conf['rules']:
                new_token.data.update(token_conf['rules'][vertex['type']])
            return new_token, reason
        else:
            return None, reason


    def run_pipeline(self, configuration, plugins, pipeline, vertex):
        try:
            compute_stats = configuration['parameters']['stats']
        except:
            compute_stats = False

        state = core.state.State()
        pipeline_data = dict()
        stats = dict()
        neighbors = list()
        for plugin_name in pipeline:
            assert plugin_name in plugins, "Plugin {0} not loaded!".format(plugin_name)

            try:
                plugin_profile = core.profile.Profile(configuration[plugin_name])
            except:
                plugin_profile = core.profile.Profile(dict())

            if compute_stats:
                start_time = time.time()

            try:
                plugin_data = plugins[plugin_name].process(plugin_profile, state, vertex)
                if plugin_data is None:
                    plugin_data = dict()
            except Exception as e:
                plugin_data = { "exception" : "{0}".format(e) }
                print(colorama.Fore.RED + "Exception: {0}: {1}".format(plugin_name, e) + colorama.Style.RESET_ALL)

            if compute_stats:
                stats[plugin_name] = time.time() - start_time

            # ------------------------------

            if state.value['message'] is not None:
                print("    {dim}[{reset}{name}{dim}]{reset} {cyan}{id}{reset}{dim} : {reset}{magenta}{message}{reset}".format(
                    cyan=colorama.Fore.CYAN,
                    reset=colorama.Style.RESET_ALL,
                    magenta=colorama.Fore.MAGENTA,
                    dim=colorama.Style.DIM,
                    name=plugin_name,
                    id=self.safe_unicode(vertex['id']).encode("utf-8"),
                    message=state.value['message']
                ))
                state.reset('message')

            if state.value['abort']:
                break

            if state.value['include']:
                properties = dict()

                try: properties.update(plugin_data['properties'])
                except: pass
                try: properties['exception'] = plugin_data['exception']
                except: pass

                if len(properties) > 0:
                    vertex[plugin_name] = properties

                state.reset('include')

            if not state.value['continue']:
                break

            if "neighbors" in plugin_data:
                neighbors.append((
                    plugin_name,
                    self.sample_neighbors(
                        configuration,
                        vertex,
                        plugin_name,
                        plugin_data['neighbors']
                    )
                ))

        return state, stats, neighbors


    def process_task(self, task):
        graph = self.graph

        plugins = self.master.plugins
        pipeline = self.master.pipeline

        configuration = self.master.configuration
        parameters = configuration['parameters']
        tokens = parameters['tokens']

        if task['task'] == "vertex":

            vertex = task['data']
            depth = task['depth']

            # ----- Token logic -----

            token, reason = self.compute_new_token(graph, depth=depth, token_conf=tokens, vertex=vertex)
            if reason is not None:
                print("{}    . {}{}".format(colorama.Style.DIM, reason, colorama.Style.RESET_ALL))
            if token is None: # NOTE: Token is still up-to-date, no need to reprocess vertex.
                return
            graph.update_token(vertex['id'], token, **token.data)

            # ----- Modular vertex exploration ----

            state, stats, neighbors = self.run_pipeline(configuration, plugins, pipeline, vertex)
            if state.value['persist']:
                graph.update_vertex(**vertex)

            # NOTE: If computed, we store the exploration stats in token
            if stats is not None and stats:
                token.data['stats'] = stats
                graph.update_token(vertex['id'], token, **token.data)

            # NOTE: Notify master we are done with this task
            if state.value['notify']:
                task['data'] = vertex
                self.master.output_queue.push(task)

            # ----- Recursion ------

            if not self.keep_mining(configuration, plugins, vertex, token.data):
                return

            for neighbor_item in neighbors:
                plugin_name, plugin_neighbors = neighbor_item

                for neighbor in plugin_neighbors:

                    assert 'id' in neighbor[0], "Neighbor node must have an id!"
                    assert 'type' in neighbor[0], "Neighbor node must have a type!"
                    assert 'type' in neighbor[1], "Neighbor edge must have a type!"

                    print("    {dim}[{reset}{name}{dim}]{reset} {cyan}{type}{reset} {dim}:{reset} {cyan}{id}{reset}".format(
                        dim=colorama.Style.DIM,
                        reset=colorama.Style.RESET_ALL,
                        cyan=colorama.Fore.CYAN,
                        name=plugin_name,
                        type=self.safe_unicode(neighbor[1]['type']).encode("utf-8"),
                        id=self.safe_unicode(neighbor[0]['id']).encode("utf-8")
                    ))

                    # NOTE: Enqueue new neighbor vertex

                    self.master.input_queue.push({
                        "task" : "vertex",
                        "data" : neighbor[0],
                        "depth" : depth + 1
                    })

                    # NOTE: Enqueue new connecting edge only if current vertex is stored in db.
                    # Otherwise we end up with an edge connecting a non-existent source vertex.

                    if state.value['persist']:

                        new_edge = {
                            'src' : vertex['id'],
                            'dst' : neighbor[0]['id'],
                        }
                        new_edge[plugin_name] = neighbor[1]

                        self.master.input_queue.push(
                            {
                                "task" : "edge",
                                "data" : new_edge,
                                "depth" : depth + 0.5
                            })

        elif task['task'] == 'edge':
            # TODO: We need edge tokens. Edge data keeps accumulating
            # If edge already visited, we should drop neighbor.

            update_data = task['data']

            query = list(graph.query_edges({ "src": update_data['src'], "dst": update_data['dst'] }))
            if len(query) > 0:
                edge = query[0]
            else:
                edge = { "src": update_data['src'], "dst": update_data['dst'] }

            for prop, value in update_data.items():
                if prop == "src" or prop == "dst":
                    continue
                if prop not in edge:
                    edge[prop] = [ value ]
                else:
                    if isinstance(edge[prop], list):
                        edge[prop].append(value)
                    else:
                        edge[prop] = [ edge[prop], value ]

            graph.update_edge(**edge)

    def keep_mining(self, configuration, plugins, vertex, token):
        parameters = configuration['parameters']

        if 'depth' in parameters:
            if parameters['depth'] == "infinite":
                return True
            elif token['depth'] >= parameters['depth']:
               return False

        return True

    def sample_neighbors(self, configuration, vertex, plugin_name, neighbors):
        # NOTE: If no sampling rule is found, we keep everything.
        try:
            rules = configuration[plugin_name][vertex['type']]['neighbors']
        except:
            return neighbors

        sampled_neighbors = list()

        for neighbor_type, sampling in rules.items():
            neighbor_subset = [ n for n in neighbors if n[1]['type'] == neighbor_type ]

            if sampling['select'] == "all":
                pass
            elif sampling['select'] == "first":
                neighbor_subset = neighbor_subset[0 : sampling['size']]
            elif sampling['select'] == "last":
                neighbor_subset = neighbor_subset[-sampling['size']:]
            elif sampling['select'] == 'random':
                population_size = min(sampling['size'], len(neighbor_subset))
                neighbor_subset = [ neighbor_subset[i] for i in random.sample(xrange(len(neighbor_subset)), population_size) ]
            elif sampling['select'] == 'none':
                neighbor_subset = list()
            else:
                print("[Error] Unknown sampling selection method '{0}', discarding all.".format(sampling['select']))
                neighbor_subset = list()

            sampled_neighbors.extend(neighbor_subset)

        return sampled_neighbors