class Profile(object):
    def __init__(self, data):
        self.profile = data

    def get_vertex_property_rule(self, vertex_type, property_name):
        try:
            return bool(self.profile[vertex_type]['properties'][property_name])
        except:
            # NOTE: Default is set to true if property rule is not defined
            return True

    def get_vertex_neighbor_rule(self, vertex_type, edge_type):
        try:
            rule = self.profile[vertex_type]['neighbors'][edge_type]
            if rule['select'].lower() == "none":
                return None
            return rule
        except:
            return None # NOTE: Default is set to None if neighbor rule is not defined