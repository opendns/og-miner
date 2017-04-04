# OG-Miner

Data Crawling on Steroids

## Installation

```
git clone git@github.com:opendns/og-miner.git
cd og-miner
pip install -r requirements.txt
```

After this step, you will need to configure your API keys in *conf.json*

## Usage

```
$ ./miner.py --help
Miner Script (version 3.7)
usage: miner.py [-h] [--domain DOMAIN] [--domains DOMAINS] [--url URL]
                [--urls URLS] [--ip IP] [--ips IPS] [--asn ASN] [--asns ASNS]
                [--email EMAIL] [--emails EMAILS] [--hash HASH]
                [--hashes HASHES] [--regex REGEX] [--regexes REGEXES]
                [--query QUERY] [--json JSON] [--pull PULL] [--push PUSH]
                [--config CONFIG] [--profile PROFILE] [--token TOKEN]
                [--ttl TTL] [--title TITLE] [--explore EXPLORE]
                [--operate OPERATE] [--depth DEPTH] [--workers WORKERS]
                [--output OUTPUT] [--mongo MONGO] [--reset] [--no-output]
                [--stats]

optional arguments:
  -h, --help         show this help message and exit
  --domain DOMAIN    Mine from a domain.
  --domains DOMAINS  Mine from a list of domains in a file.
  --url URL          Mine from a URL.
  --urls URLS        Mine from a list of URLs in a file.
  --ip IP            Mine from an IP.
  --ips IPS          Mine from a list of IPs in a file.
  --asn ASN          Mine from an ASN.
  --asns ASNS        Mine from a list of ASNs in a file.
  --email EMAIL      Mine from an email address.
  --emails EMAILS    Mine from a list of emails in a file.
  --hash HASH        Mine from a hash.
  --hashes HASHES    Mine from a list of hashes in a file.
  --regex REGEX      Mine from a regex.
  --regexes REGEXES  Mine from a list of regexes in a file.
  --query QUERY      Mine from graph vertices matching the query
  --json JSON        Load custom tasks from a JSON file.
  --pull PULL        Pull entries to mine from a ZMQ stream.
  --push PUSH        Push mined results to a ZMQ stream.
  --config CONFIG    Select a configuration file.
  --profile PROFILE  Select a mining profile.
  --token TOKEN      Set the mining token.
  --ttl TTL          Set the mining token TTL (in seconds).
  --title TITLE      Set the dataset title.
  --explore EXPLORE  Set the list of explorers.
  --operate OPERATE  Set the list of operators.
  --depth DEPTH      Set the mining maximum depth.
  --workers WORKERS  Set the number of worker threads.
  --output OUTPUT    Set the output JSON filename.
  --mongo MONGO      Use MongoDB as a graph database.
  --reset            Reset graph.
  --no-output        No JSON output.
  --stats            Compute performance metrics.
```

## Documentation

The miner script is a powerful data mining tool that helps users discover and build relationships between various entry points in a graph oriented fashion. Multiple sources of data already are implemented using a modular plugin system. and can be easily integrated using a modular plugin system. 

Before digging too deep into the miner details, it is important to see the big picture. At OpenDNS, we build the "Security Graph". This security graph can be seen as a complex relational database representing Internet entities (Domains, IPs, ASNs, Whois ...) built on one hand from our DNS logs, on the other hand from external parties (Whois DB, MaxMind GeoIP, etc.). We connect those entites using several relationships (Co-occurrence, Related Domains, Domain-IP mapping, Registration etc.)

In other words, all this agglomerated data can be seen as a giant graph connecting dots of information. The miner script is a useful tool to extract parts of this graph ("subgraphs"). It digs inside the whole data network from given entry points using a certain mining profile. You can define as many entry points as you want from the command line and the mining profile is defined in a JSON file inside the "profiles" folder. If no profile is defined, it will fall back to the default one.

Once the miner has finished running, the output is a graph dataset stored in the JSON format. You can define the name of the resulting file with the --output argument and this file can be analyzed and loaded with various graph analysis softwares (ex: OpenGraphiti).

# Entry points

You can start from any domain, IP, email, ASN or binary hash. Use the --domain, --ip, --email, --asn and --hash arguments if you have only one (Or only one of each). You can use the arguments --domains, --ips, --emails, --asns and --hashes if you need to pass a list contained in a file. The file needs to have only one entry per line.

Examples:

Starts digging from test.com
```
$ ./miner.py --domain test.com
```

Starts digging from domain test.com, ip 8.8.8.8 and asn 1234.
```
$ ./miner.py --domain test.com --ip 8.8.8.8 --asn 1234
```

Starts digging from all domains located in 'domains.txt', saves the result in 'result.json' and sets the title of the dataset.
```
$ ./miner.py --domains domains.txt --output result.json --title "Infected Domains"
```

# Mining Profiles

In reality, the data mining process is nothing more than a customizable Breadth First Traversal.
Long story short, here is what it does :
- Start from a set of seed nodes.
- Parse all neighbors
- Parse the neighbors of the neighbors
- Parse the neighbors of the neighbors of the neighbors
- Repeats that until we can't find new neighbors or until a certain limit is reached or a certain condition is met (Depth, number of nodes, memory size ...).

The mining profiles help you customize a couple of things :
- The types of nodes and edges you want to parse
- The node and edges attributes you want to extract.
- The neighbor selection method.

Different mining profiles will give you different results. Usually, a certain profile corresponds to a certain use case. For example, the "default.json" profile parses every type of node, edges and attributes but select only a bunch of neighbors at every iteration and is limited to a small depth. This is only intended to give you a relatively small dataset for an overview of a certain node neighborhood and a quick understanding of the various types of data that we collect. 

Please take a look at "profiles/default.json" for concrete examples.
