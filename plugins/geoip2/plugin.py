import geoip2.database
import os

class Plugin(object):
    def __init__(self, configuration):
        plugin_path = os.path.dirname(os.path.abspath(__file__))
        self.reader = geoip2.database.Reader(plugin_path + "/GeoLite2-City.mmdb")
        
    def process(self, profile, state, vertex):
        if 'type' not in vertex:
            return { 'error' : "No vertex type defined!" }

        properties = dict()
        neighbors = []

        if vertex['type'] != 'ip':
            return { "properties": properties, "neighbors" : neighbors }

        # Get GeoIP City data from database
        try: data = self.reader.city(vertex['id'])
        except: return { "properties": properties, "neighbors" : [] }

        # Geolocation
        try:
            properties['location'] = {
                'latitude' : data.location.latitude,
                'longitude' : data.location.longitude,
            }
        except: pass
        
        # City
        try: properties['city'] = data.city.names['en']
        except: pass

        # Country
        try:
            properties['country'] = {
                "iso_code" : data.country.iso_code,
                "name" : data.country.names['en']
            }
        except: pass

        # Registered Country
        try:
            properties['registered_country'] = {
                "iso_code" : data.registered_country.iso_code,
                "name" : data.registered_country.names['en']
            }
        except: pass

        # Subdivisions
        try:
            properties['subdivision'] = {
                "iso_code" : data.subdivisions.most_specific.iso_code,
                "name" : data.subdivisions.most_specific.name
            }
        except: pass

        # Postal Code
        try: properties['postal'] = data.postal.code
        except: pass

        # Continent
        try:
            properties['continent'] = {
                "code" : data.continent.code,
                "name" : data.continent.names['en'] 
            }
        except: pass

        #pp.pprint(properties)

        return { "properties": properties, "neighbors" : neighbors }

        