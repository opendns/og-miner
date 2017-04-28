import investigate
import urllib
import re

class Plugin(object):
    def __init__(self, configuration):
        self.api = investigate.Investigate(configuration['api_key'])

        self.regexes = {
            'domain' : r"(([a-z0-9-]{,63}\.)+([a-z]{2,63})\.?)",
            'url' : r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            'ip' : r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}" # IPv4
            #'ipv6' : r"(?:(?:[0-9A-Fa-f]{1,4}:){6}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|::(?:[0-9A-Fa-f]{1,4}:){5}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){4}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){3}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,2}[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){2}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,3}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}:(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,4}[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,5}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}|(?:(?:[0-9A-Fa-f]{1,4}:){,6}[0-9A-Fa-f]{1,4})?::)"
        }

    def process(self, profile, state, vertex):
        if 'type' not in vertex:
            return { 'error' : "No vertex type defined!" }

        if vertex['type'] == "domain":
            return self.explore_domain(vertex, profile)
        elif vertex['type'] == "url":
            return self.explore_url(vertex, profile)
        elif vertex['type'] == "ip":
            return self.explore_ip(vertex, profile)
        elif vertex['type'] == "asn":
            return self.explore_asn(vertex, profile)
        elif vertex['type'] == "email":
            return self.explore_email(vertex, profile)
        elif vertex['type'] == "regex":
            return self.explore_regex(vertex, profile)
        elif vertex['type'] == 'hash':
            return self.explore_hash(vertex, profile)

        return { "properties": {}, "neighbors" : [] }

    def sanitize_domain(self, domain):
        if domain.endswith('.'):
            return domain[:-1]
        return domain

    def explore_domain(self, vertex, profile):
        name = str(vertex['id'])
        properties = dict()
        neighbors = list()

        if profile.get_vertex_property_rule('domain', 'categorization'):
            try: properties['categorization'] = self.api.categorization(name)[name] #NOTE:  This could take several domains
            except: pass

        if profile.get_vertex_property_rule('domain', 'security'):
            try: properties['security'] = self.api.security(name)
            except: pass

        if profile.get_vertex_property_rule('domain', 'tags'):
            try: properties['tags'] = self.api.domain_tags(name)
            except: pass

        try:
            if profile.get_vertex_property_rule('domain', 'domain_whois') or \
                profile.get_vertex_neighbor_rule('domain', 'whois:ns') is not None or \
                profile.get_vertex_neighbor_rule('domain', 'whois:registrant') is not None:

                domain_whois = self.api.domain_whois(name)
                if profile.get_vertex_property_rule('domain', 'domain_whois'):
                    properties['domain_whois'] = domain_whois

                if profile.get_vertex_neighbor_rule('domain', 'whois:registrant') is not None:
                    if 'registrantEmail' in domain_whois and \
                        domain_whois['registrantEmail'] is not None and \
                        len(domain_whois['registrantEmail']) > 0:
                        # TODO: Email extraction from registrant field. Data is manually entered and sometimes needs some formatting.
                        neighbors.append((
                            { 'type' : 'email', 'id' : domain_whois['registrantEmail'] },
                            { 'type' : 'whois:registrant' }
                        ))

                if profile.get_vertex_neighbor_rule('domain', 'whois:ns') is not None:
                    if 'nameServers' in domain_whois:
                        for ns in domain_whois['nameServers']:
                            neighbors.append((
                                { 'type' : 'domain', 'id' : self.sanitize_domain(ns) },
                                { 'type' : 'whois:ns' }
                            ))
        except: pass

        lookup_table = [
            { "query_type" : "A",       "neighbor_type" : "ip" },
            { "query_type" : "CNAME",   "neighbor_type" : "domain" },
            { "query_type" : "NS",      "neighbor_type" : "ip" },
            { "query_type" : "MX",      "neighbor_type" : "domain" }
            # { "query_type" : "TXT",     "neighbor_type" : "text" } # TODO: TXT text/blob node? 
        ]
        for lookup_item in lookup_table:
            query_type = lookup_item['query_type']
            property_name = 'rr:{}'.format(query_type.lower())

            if profile.get_vertex_property_rule('domain', property_name) or \
                profile.get_vertex_neighbor_rule('domain', property_name) is not None:
            
                rr_history = self.api.rr_history(name, query_type=query_type)

                if profile.get_vertex_property_rule('domain', property_name) and "features" in rr_history:
                    properties[property_name] = rr_history['features']

                if profile.get_vertex_neighbor_rule('domain', property_name) is not None:
                    try:
                        for rr_tf in rr_history['rrs_tf']:
                            first_seen = rr_tf['first_seen']
                            last_seen = rr_tf['last_seen']
                            for rr in rr_tf['rrs']:
                                if rr['type'] == query_type: 

                                    neighbor_vertex = { 'type' : lookup_item['neighbor_type'], 'id' : rr['rr'] }
                                    if lookup_item['neighbor_type'] == "domain":
                                        neighbor_vertex['id'] = self.sanitize_domain(neighbor_vertex['id'])

                                    neighbors.append((
                                        neighbor_vertex,
                                        {
                                            'type' : "rr:{0}".format(query_type.lower()),
                                            'ttl' : rr['ttl'],
                                            'class' : rr['class'],
                                            'first_seen' : first_seen,
                                            'last_seen' : last_seen
                                        }
                                    ))
                            # TODO : We can handle several RR timeframes by removing the break statement
                            # Here we just keep the most recent one
                            break
                    except: pass

        if profile.get_vertex_neighbor_rule('domain', 'co-occurrence') is not None:
            try:
                for item in self.api.cooccurrences(name)['pfs2']:
                    neighbors.append((
                        { 'type' : 'domain', 'id' : self.sanitize_domain(item[0]) },
                        { 'type' : 'co-occurrence', 'score' : item[1] }
                    ))
            except: pass

        if profile.get_vertex_neighbor_rule('domain', 'related') is not None:
            try:
                for item in self.api.related(name)['tb1']:
                    neighbors.append((
                        { 'type' : 'domain', 'id' : self.sanitize_domain(item[0]) },
                        { 'type' : 'related', 'score' : item[1] }
                    ))
            except: pass

        if profile.get_vertex_neighbor_rule('domain', 'samples') is not None:
            try:
                for item in self.api.samples(name, sortby="first-seen")['samples']:
                    neighbor_id = item['sha256']
                    for key in [ 'behaviors', 'md5', 'sha1', 'sha256', 'threatScore', 'magicType', 'avresults', 'visible', 'size' ]:
                        if key in item:
                            del item[key]
                    edge_data = item
                    edge_data['type'] = "samples" 
                    neighbors.append(({ 'type' : 'hash', 'id' : neighbor_id }, item))
            except: pass

        return { "properties" : properties, "neighbors" : neighbors }

    def explore_url(self, vertex, profile):
        url = vertex['id']
        properties = dict()
        neighbors = list()

        if profile.get_vertex_neighbor_rule('url', 'samples'):
            try:
                for item in self.api.samples(urllib.quote_plus(url), sortby="first-seen")['samples']:
                    neighbor_id = item['sha256']
                    for key in [ 'behaviors', 'md5', 'sha1', 'sha256', 'threatScore', 'magicType', 'avresults', 'visible', 'size' ]:
                        if key in item:
                            del item[key]
                    edge_data = item
                    edge_data['type'] = "samples" 
                    neighbors.append(({ 'type' : 'hash', 'id' : neighbor_id }, item))
            except: pass

        return { "properties" : properties, "neighbors" : neighbors }

    def explore_ip(self, vertex, profile):
        ip = vertex['id']
        properties = dict()
        neighbors = list()

        lookup_table = [
            { "query_type" : "A",  "neighbor_type" : "domain" },
            { "query_type" : "NS", "neighbor_type" : "domain" }
        ]


        for lookup_item in lookup_table:
            query_type = lookup_item['query_type']
            property_name = 'rr:{}'.format(query_type.lower())

            try:
                rr_history = self.api.rr_history(ip, query_type=query_type)
            except:
                continue

            if profile.get_vertex_property_rule('ip', property_name) and 'features' in rr_history:
                properties[property_name] = rr_history['features']

            if profile.get_vertex_neighbor_rule('ip', property_name):
                try:
                    for rr in rr_history['rrs']:
                        if rr['type'] == query_type:
                            neighbor_vertex = { 'type' : lookup_item['neighbor_type'], 'id' : rr['rr'] }
                            if lookup_item['neighbor_type'] == "domain":
                                neighbor_vertex['id'] = self.sanitize_domain(neighbor_vertex['id'])

                            neighbors.append((
                                neighbor_vertex,
                                { 'type' : "rr:{0}".format(query_type.lower()), 'ttl' : rr['ttl'], 'class' : rr['class'] }
                            ))  
                except: pass

        if profile.get_vertex_neighbor_rule('ip', "ip -> asn"):
            try:
                for item in self.api.as_for_ip(ip):
                    neighbors.append((
                        {
                            "id": str(item['asn']),
                            "type": "asn",
                            "description": item['description'].strip()
                        },
                        {
                            "type" : "ip -> asn"
                        }
                    ))
            except: pass

        if profile.get_vertex_neighbor_rule('ip', "samples"):
            try:
                for item in self.api.samples(ip, sortby="first-seen")['samples']:
                    neighbor_id = item['sha256']
                    for key in [ 'behaviors', 'md5', 'sha1', 'sha256', 'threatScore', 'magicType', 'avresults', 'visible', 'size' ]:
                        if key in item:
                            del item[key]
                    edge_data = item
                    edge_data['type'] = "samples" 
                    neighbors.append(({ 'type' : 'hash', 'id' : neighbor_id }, item))
            except: pass
        

        return { "properties" : properties, "neighbors" : neighbors }

    def explore_asn(self, vertex, profile):
        asn = vertex['id']
        properties = dict()
        neighbors = list()

        if profile.get_vertex_neighbor_rule("asn", "asn -> prefix"):
            try:
                for item in self.api.prefixes_for_asn(asn):
                    neighbors.append((
                        { "type" : "prefix", "id" : item['cidr'], "geo" : item['geo'] },
                        { "type" : "asn -> prefix" }
                    ))
            except: pass
            
        return { "properties" : properties, "neighbors" : neighbors }

    def explore_email(self, vertex, profile):
        email = vertex['id']
        properties = dict()
        neighbors = list()

        if profile.get_vertex_neighbor_rule('email', "whois"):
            try:
                data = self.api.email_whois(email)
                for item in data[email]['domains']:
                    if item['current']:
                        neighbors.append((
                            { 'type' : 'domain', 'id' : self.sanitize_domain(item['domain']) },
                            { 'type' : 'whois' }
                        ))
            except: pass
      
        return { "properties" : properties, "neighbors" : neighbors }

    def explore_regex(self, vertex, profile):
        regex = vertex['id']
        properties = dict()
        neighbors = list()

        if profile.get_vertex_neighbor_rule('regex', "regex:match"):
            try:
                data = self.api.search(regex)
                for match in data['matches']:
                    neighbors.append((
                        { 'type' : 'domain', 'id' : self.sanitize_domain(match['name']) },
                        { 'type' : 'regex:match' }
                    ))
            except: pass

        return { "properties" : properties, "neighbors" : neighbors } 


    def explore_hash(self, vertex, profile):
        properties = dict()
        neighbors = list()

        if profile.get_vertex_property_rule('hash', 'threatgrid') or    \
            profile.get_vertex_neighbor_rule('hash', 'connections') or  \
            profile.get_vertex_neighbor_rule('hash', 'samples') or      \
            profile.get_vertex_neighbor_rule('hash', 'hash:group'):

            data = self.api.sample(vertex['id'])

            if "error" in data:
                return { "properties" : properties, "neighbors" : neighbors }

            if profile.get_vertex_property_rule('hash', 'threatgrid'): #TODO: We could be a bit more granular here.
                for key in [ 'avresults', 'threatScore', 'magicType', "firstSeen", "lastSeen", "size", "behaviors" ]:
                    if key in data:
                        properties[key] = data[key]

            if profile.get_vertex_property_rule('hash', 'connections'):
                for item in data['connections']['connections']: #TODO: Pagination to retrieve more than 10 results
                    
                    neighbor_type = None
                    for key in [ 'url', 'ip', 'domain' ]:
                        if re.match(self.regexes[key], item['name']):
                            neighbor_type = key
                    
                    if neighbor_type is None:
                        print("\tUnable to detect type for neighbor: {0}".format(item['name']))
                        continue
                    if neighbor_type == "domain":
                        item['name'] = self.sanitize_domain(item['name'])

                    neighbors.append((
                        { 'type' : neighbor_type, 'id' : item['name'] },
                        { 'type' : 'connections' }
                    ))

            if profile.get_vertex_property_rule('hash', 'samples'):
                for item in data['samples']['samples']: #TODO: Pagination to retrieve more than 10 results
                    neighbors.append((
                        { 'type' : 'hash', 'id' : item['sha256'] },
                        { 'type' : 'samples' }
                    ))

            ''' TODO: Error: "item referenced before assignment"
            if profile.get_vertex_property_rule('hash', 'hash:group'):
                for key in [ 'md5', 'sha1', 'sha256']:
                    if key in item:
                        neighbors.append((
                            { 'type' : 'hash', 'id' : item[key] },
                            { 'type' : 'hash_group' }
                        ))
            '''
        return { "properties" : properties, "neighbors" : neighbors }

