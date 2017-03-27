#!/usr/bin/env python

import sys
import json
import csv
import time
import datetime
import math

import pprint as pp

if __name__ == "__main__":

	if len(sys.argv) != 2:
		print("Usage: {0} <graph.json>".format(sys.argv[0]))
		sys.exit(0)

	with open(sys.argv[1], "rU") as infile:

		graph = json.load(infile)

		nodes_by_type = dict()
		for node in graph['nodes']:
			
			node_type = None
			if 'type' in node:
				node_type = node['type']
			
			if node_type not in nodes_by_type:
				nodes_by_type[node_type] = list()

			node_summary = {
				"#FQDN" : node['id']
			}

			if node_type == "domain":

				# Popularity
				try: node_summary['popularity'] = node['investigate']['security']['popularity']
				except: pass

				# Whois:age
				try:
					created = node['investigate']["domain_whois"][0]["created"]
					year, month, day= created.split("-")
					year = int(year)
					month = int(month)
					day = int(day)
					age =  datetime.date.today() - datetime.date(year, month, day)
					node_summary['age'] = math.log(age.days, 10)
				except:pass

				# Number of IPs, Prefixes, ASNs, Countries
				try: node_summary['ips'] = node['investigate']['rr_history']['rips']
				except:pass
				try: node_summary['prefixes'] = node['investigate']['rr_history']['prefixes_count']
				except:pass
				try: node_summary['asns'] = node['investigate']['rr_history']['asns_count']
				except:pass
				try: node_summary['countries'] = node['investigate']['rr_history']['country_count']
				except:pass

				# TTL min/max/stddev
				try: node_summary['ttl_min'] = node['investigate']['rr_history']['ttls_min']
				except:pass
				try: node_summary['ttl_max'] = node['investigate']['rr_history']['ttls_max']
				except:pass
				try: node_summary['ttl_stddev'] = node['investigate']['rr_history']['ttls_stddev']
				except:pass

				# Geodistance sum + mean
				try: node_summary['geo_sum'] = node['investigate']['rr_history']['geo_distance_sum']
				except:pass
				try: node_summary['geo_mean'] = node['investigate']['rr_history']['geo_distance_mean']
				except:pass

				# Entropy + Perplexity
				try: node_summary['entropy'] = node['investigate']['security']['entropy']
				except:pass
				try: node_summary['perplexity'] = node['investigate']['security']['perplexity']
				except:pass

				#try: node_summary['odns:age'] = node['investigate']['rr_history']['age']
				#except: pass
				#try: node_summary['odns:dga:score'] = node['investigate']['security']['dga_score']
				#except: pass

				# Infected score
				try: node_summary['status'] = node['investigate']['categorization']['status']
				except: pass

		        # VirusTotal summary
				max_positives = 0
				try:
					for item in node['virustotal']['detected_urls']:
						if item["positives"] > max_positives:
							max_positives = item['positives']
				except: pass
				node_summary['vt:positives'] = max_positives

			elif node_type == "ip":

				try: node_summary['city'] = node['geoip2']['city']
				except:pass

				try: node_summary['country'] = node['geoip2']['country']['name']
				except:pass

				try: node_summary['subdivision'] = node['geoip2']['subdivision']['name']
				except:pass

				try: node_summary['postal'] = node['geoip2']['postal']
				except:pass

				try: node_summary['continent'] = node['geoip2']['continent']['code']
				except:pass

				try:
					node_summary['latitude'] = node['geoip2']['location']['latitude']
					node_summary['longitude'] = node['geoip2']['location']['longitude']
				except:pass

				try: node_summary['isp'] = node['shodan']['isp']
				except:pass

				try: node_summary['org'] = node['shodan']['org']
				except: pass

				try:
					node_summary['vulns'] = 0
					node_summary['vulns'] = len(node['shodan']['vulns'])
				except: pass

				try:
					node_summary['last_scan'] = node['shodan']['last_update']
				except: pass

			nodes_by_type[node_type].append(node_summary)


		headers_by_type = {
			"domain" : [
				"#FQDN",
				"popularity", "age",
				"ips", "prefixes", "asns", "countries",
				"ttl_min", "ttl_max", "ttl_stddev",
				"geo_sum", "geo_mean",
				"entropy", "perplexity",
				"status", "vt:positives"
			],
			"ip" : [
				"#FQDN",
				"city", "country", "subdivision", "postal", "continent",
				"latitude", "longitude",
				"isp", "org",
				"vulns"
			],
			"url" : [ "#FQDN" ],
			"as" : [ "#FQDN" ],
			"email" : [ "#FQDN" ],
			"port" : [ "#FQDN" ],
			"hash" : [ "#FQDN" ]
		}

		for k, v in nodes_by_type.items():

			keys = list()
			for item in v:
				for k2 in item.keys():
					if k2 not in keys:
						keys.append(k2)

			header = headers_by_type[k]
			for h in header:
				if h in keys:
					keys.remove(h)

			csv_header = header + keys

			with open("./output/flat-" + k + ".csv", "w") as fp:
				writer = csv.writer(fp, delimiter=',')

				writer.writerow(csv_header)

				for item in v:
					row = list()
					for k1 in csv_header:
						if k1 in item:
							row.append(item[k1])
						else:
							row.append(None)

					try:
						writer.writerow(row)
					except:
						print("Error: Weird encoding. Skipping item. (TODO: Fix this asap)")
						continue
		#pp.pprint(nodes_by_type)