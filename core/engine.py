import os
import sys
import md5
import json
import random
import threading
import traceback
import imp

import colorama

import core.object
import core.token
import core.graph.mongo
import core.graph.memory
import core.worker
import core.queue

class Engine(core.object.Object):

    def __init__(self, configuration, graph, **kwargs):
        self.graph = graph
        self.configuration = configuration
        self.parameters = self.configuration['parameters']

        self.input_queue = core.queue.TaskQueue()
        # TODO: Send notifications to this queue when task is completed.
        self.output_queue = core.queue.TaskQueue()

        self.workers = list()
        self.order = None

        self.nworkers = int(kwargs['workers'])

        self.print_item("+", "Using " + colorama.Fore.CYAN + str(self.nworkers) + colorama.Style.RESET_ALL + " workers ...")

        self.plugins = dict()
        for plugin in configuration['plugins']:
            name = plugin['name']
            path = plugin['path']
            print(
                "    - " + colorama.Fore.CYAN + "{0}".format(name) + colorama.Style.RESET_ALL
                + colorama.Style.DIM + " -> " + colorama.Style.RESET_ALL
                + "{0}".format(path))

            plugin_module = self.load_module(path)
            plugin_class = getattr(plugin_module, 'Plugin')
            self.plugins[name] = plugin_class(plugin)

        self.print_item("+", "Activating pipeline ...")
        self.pipeline = self.parameters['pipeline']
        for element in self.pipeline:
            print(
                "    - "
                + colorama.Fore.CYAN + "{0}".format(element) + colorama.Fore.RESET
            )

        self.seeders = kwargs['seeders']
        self.output_socket = kwargs['output_socket']
        self.qlimit = kwargs['qlimit']

        try:
            indices = configuration['parameters']['indices']
            self.print_item("+", "Setting graph indices ...")
            for index_type in [ 'vertex', 'edge', 'token' ]:
                if index_type not in indices:
                    continue
                for index in indices[index_type]:
                    try:
                        print(("    - {}: " + colorama.Fore.CYAN + "{}" + colorama.Fore.RESET).format(index_type, index))
                        self.graph.update_index(type=index_type, key=index)
                    except Exception as e:
                        print(colorama.Fore.YELLOW + "Error while updating {} index: {}".format(index_type, e) + colorama.Fore.RESET)
        except:
            pass

    def load_module(self, code_path):
        try:
            try:
                code_dir = os.path.dirname(code_path)
                code_file = os.path.basename(code_path)
                fin = open(code_path, 'rb')
                return  imp.load_source(md5.new(code_path).hexdigest(), code_path, fin)
            finally:
                try: fin.close()
                except: pass
        except ImportError, x:
            traceback.print_exc(file = sys.stderr)
            raise
        except:
            traceback.print_exc(file = sys.stderr)
            raise


    def prepare_workers(self):
        self.print_item("+", "Preparing workers ...")

        self.workers = [ core.worker.Worker(self, i) for i in range(self.nworkers) ]
        [ worker.thread.start() for worker in self.workers ]

        for i in range(0, len(self.workers)):
            self.workers[i].event.wait()
            print("    - Worker {}{}{} is ready.".format(colorama.Fore.CYAN, i, colorama.Style.RESET_ALL))  
            self.workers[i].event.clear()   

    def stop_workers(self):
        self.print_item("+", "Stopping workers ...")
        [ worker.stop() for worker in self.workers ] 

        for i in range(0, len(self.workers)):
            self.workers[i].event.wait()
            print("    - Worker {}{}{} is stopped.".format(colorama.Fore.CYAN, i, colorama.Style.RESET_ALL))  
            self.workers[i].event.clear()   

    def start(self):

        while self.is_alive():

            #print("DEBUG ALIVE {} {}, {}".format(self.input_queue.count(), self.output_queue.count(), len(self.seeders)))

            for seeder in self.seeders:

                if self.qlimit is None or self.input_queue.count() < self.qlimit:

                    #print("DEBUG HERE")

                    try:
                        element = next(seeder)
                    except StopIteration:
                        self.seeders.remove(seeder)
                        continue
                    except Exception as e:
                        print(colorama.Fore.RED + "Seeder exception!" + colorama.Fore.RESET)
                        print(e)
                        self.seeders.remove(seeder)
                        continue

                    if element is None: # NOTE: Some generators may not have the data directly available. This avoids blocking.
                        continue

                    if "task" in element and "data" in element:
                        task = element
                    elif "id" in element and "type" in element:
                        task = { "task" : "vertex", "data" : element }

                    if "depth" not in task:
                        task['depth'] = 0

                    self.input_queue.push(task)

            # NOTE: Flush completed tasks
            completed_task = self.output_queue.get()
            if completed_task is not None:
                # TODO: Print some debug info here instead of inside the workers
                self.output_queue.pop()

                if self.output_socket is not None:
                    try:
                        self.output_socket.send_json(completed_task)
                    except Exception as e:
                        print(colorama.Fore.YELLOW + "Couldn't push vertex to JSON socket." + colorama.Fore.RESET)
                        print(completed_task)

    def stop(self):
        self.order = "stop"

    def is_alive(self):
        if self.order == "stop":
            return False
        else:
            return (self.input_queue.count() > 0) or (self.output_queue.count() > 0) or (len(self.seeders) > 0)