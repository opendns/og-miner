import fnmatch

class Plugin(object):
    def __init__(self, configuration):
        self.configuration = configuration

        self.filename = configuration['filename']

        with open(self.filename, "rU") as blacklist:
            self.blacklist = [ line.strip() for line in blacklist.readlines() ]
            print("        Loaded '{0}', {1} lines detected.".format(self.filename, len(self.blacklist)))

    def process(self, profile, state, vertex):
        for pattern in self.blacklist:
            if fnmatch.fnmatch(vertex['id'], pattern):
                state.message("Matched pattern '{0}'.".format(pattern))
                state.stop()
                return { "properties" : { "match" : pattern } }
                
