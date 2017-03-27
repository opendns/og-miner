import abc
import colorama
import json

class Graph(object):
    __metacass__ = abc.ABCMeta

    def __init__(self, **kwargs):
        self.verbose = False
        if "verbose" in kwargs:
            self.verbose = bool(kwargs['verbose'])

    def log(self, message):
        if not self.verbose:
            return
        print (
            colorama.Style.DIM + "["
            + colorama.Style.RESET_ALL + colorama.Fore.BLUE + "Graph" + colorama.Fore.RESET
            + colorama.Style.DIM + "] "
            + "{0}".format(message) + colorama.Style.RESET_ALL
        )

    def load_json(self, json_filename):
        with open(json_filename, "rU") as json_file:
            json_data = json.load(json_file)

            for vertex_field in [ 'nodes', 'vertices' ]:
                if vertex_field not in json_data:
                    continue
                for vertex in json_data[vertex_field]:
                    self.update_vertex(**vertex)

            for edge in json_data['edges']:
                self.update_edge(**edge)

    # -----

    @abc.abstractmethod
    def get_metadata(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_properties(self):
        raise NotImplementedError

    # ----- Count Methods -----

    @abc.abstractmethod
    def count_vertices(self):
        raise NotImplementedError

    @abc.abstractmethod
    def count_edges(self):
        raise NotImplementedError

    @abc.abstractmethod
    def count_tokens(self):
        raise NotImplementedError

    # ----- Update Methods -----

    @abc.abstractmethod
    def update_vertex(self, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def update_edge(self, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def update_token(self, nid, token, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def update_index(self, **kwargs):
        raise NotImplementedError

    # ----- Remove Methods -----

    @abc.abstractmethod
    def clear(self):
        raise NotImplementedError

    @abc.abstractmethod
    def remove_vertex(self, nid):
        raise NotImplementedError

    @abc.abstractmethod
    def remove_edge(self, src, dst):
        raise NotImplementedError

    # ----- Query Methods -----

    @abc.abstractmethod
    def query_vertices(self, query={}, projection=None, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def query_edges(self, query={}, projection=None, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def query_tokens(self, query={}, projection=None, **kwargs):
        raise NotImplementedError
