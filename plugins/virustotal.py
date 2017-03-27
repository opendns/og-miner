import requests

class Plugin(object):
    def __init__(self, configuration):
        self.api_key = configuration['api_key']

    # --- VirusTotal Helpers ---

    def query_domain_report(self, domain):
        params = { 'apikey': self.api_key, 'domain': domain }
        response = requests.get('https://www.virustotal.com/vtapi/v2/domain/report', params=params)
        return response.json()

    def query_url_report(self, url):
        params = { 'apikey': self.api_key, 'resource': url }
        response = requests.get('https://www.virustotal.com/vtapi/v2/url/report', params=params)
        return response.json()

    def query_ip_address_report(self, ip):
        params = { 'apikey': self.api_key, 'ip': ip }
        response = requests.get('https://www.virustotal.com/vtapi/v2/ip-address/report', params=params)
        return response.json()

    def query_file_report(self, hash):
        params = { 'apikey': self.api_key, 'resource': hash }
        response = requests.get('https://www.virustotal.com/vtapi/v2/file/report', params=params)
        return response.json()


    # --- Exploration ---

    def process(self, profile, state, vertex):
        if 'type' not in vertex:
            return { 'error' : "No vertex type defined!" }

        if vertex['type'] == "domain":
            return self.explore_domain(vertex)
        elif vertex['type'] == "url":
            return self.explore_url(vertex)
        elif vertex['type'] == "ip":
            return self.explore_ip(vertex)
        elif vertex['type'] == "hash":
            return self.explore_hash(vertex)

        return { "properties": {}, "neighbors" : [] }

    def explore_domain(self, vertex):
        properties = dict()
        neighbors = list()

        try:
            properties = self.query_domain_report(vertex['id'])

            try:
                for item in properties['detected_urls']:
                    neighbors.append((
                        { 'type' : 'url', 'id' : item['url'] },
                        { 'type' : 'detected_urls' }
                    ))
            except:
                pass

            try:
                for item in properties['detected_communicating_samples']:
                    neighbors.append((
                        { 'type' : 'hash', 'id' : item['sha256'] },
                        { 'type' : 'detected_communicating_samples' }
                    ))
            except:
                pass

            try:
                for item in properties['detected_downloaded_samples']:
                    neighbors.append((
                        { 'type' : 'hash', 'id' : item['sha256'] },
                        { 'type' : 'detected_downloaded_samples' }
                    ))
            except:
                pass


            try:
                for item in properties['subdomains']:
                    neighbors.append((
                        { 'type' : 'domain', 'id' : item },
                        { 'type' : 'subdomains' }
                    ))
            except:
                pass

        except:
            pass

        return { "properties": properties, "neighbors" : neighbors } 

    def explore_url(self, vertex):
        properties = dict()
        neighbors = list()

        try:
            properties = self.query_url_report(vertex['id'])
        except:
            pass

        return { "properties": properties, "neighbors" : neighbors } 

    def explore_ip(self, vertex):
        properties = dict()
        neighbors = list()

        try:
            properties = self.query_ip_address_report(vertex['id'])

            try:
                for item in properties['detected_urls']:
                    neighbors.append((
                        { 'type' : 'url', 'id' : item['url'] },
                        { 'type' : 'detected_urls' }
                    ))
            except:
                pass

            try:
                for item in properties['detected_communicating_samples']:
                    neighbors.append((
                        { 'type' : 'hash', 'id' : item['sha256'] },
                        { 'type' : 'detected_communicating_samples' }
                    ))
            except:
                pass

            try:
                for item in properties['detected_downloaded_samples']:
                    neighbors.append((
                        { 'type' : 'hash', 'id' : item['sha256'] },
                        { 'type' : 'detected_downloaded_samples' }
                    ))
            except:
                pass
        except:
            pass

        return { "properties": properties, "neighbors" : neighbors } 


    def explore_hash(self, vertex):
        properties = dict()
        neighbors = list()

        try:
            properties = self.query_file_report(vertex['id'])

            try:
                for item in ["sha1", "sha256", "md5"]:
                    if item in properties:
                        if properties[item] == vertex['id']:
                            continue
                        neighbors.append((
                            { 'type' : 'hash', 'id' : properties[item] },
                            { 'type' : 'hash_group' }
                        ))
            except:
                pass
        except:
            pass

        return { "properties": properties, "neighbors" : neighbors } 
