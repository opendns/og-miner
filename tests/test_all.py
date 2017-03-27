import pytest

import os, sys

print(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

import core.graph.memory
import core.graph.mongo

memory_graph = core.graph.memory.Graph()
mongo_graph = core.graph.mongo.Graph(host="localhost", port=27017, db="pytest-graph")

@pytest.mark.parametrize("graph", [memory_graph, mongo_graph])
def test_counters(graph):
	graph.clear()
	assert graph.count_vertices() == 0
	assert graph.count_edges() == 0

	graph.update_vertex(id='romeo', type='male')
	graph.update_vertex(id='juliet', type='female')
	graph.update_edge(src='romeo', dst='juliet', type='love')

	assert graph.count_vertices() == 2
	assert graph.count_edges() == 1

	graph.clear()
	assert graph.count_vertices() == 0
	assert graph.count_edges() == 0

@pytest.mark.parametrize("graph", [memory_graph, mongo_graph])
def test_updates(graph):
	graph.clear()
	
	graph.update_vertex(id='juliet')
	graph.update_vertex(id='juliet', type='person')
	graph.update_vertex(id='juliet', is_female=True)
	graph.update_vertex(id='juliet', age=13)
	vertex = list(graph.query_vertices())[0]
	
	assert(vertex['id'] == 'juliet')
	assert(vertex['type'] == 'person')
	assert(vertex['age'] == 13)
	assert(vertex['is_female'])

	graph.update_vertex(id='romeo')
	graph.update_edge(src='romeo', dst='juliet')
	graph.update_edge(src='romeo', dst='juliet', type='hate')
	graph.update_edge(src='romeo', dst='juliet', type='love')

	edge = list(graph.query_edges())[0]
	assert('type' in edge)
	assert(edge['type'] == "love")

@pytest.mark.parametrize("graph", [memory_graph, mongo_graph])
def test_queries(graph):
	graph.clear()
	graph.update_vertex(id='romeo', type='male')
	graph.update_vertex(id='juliet', type='female')
	graph.update_edge(src='romeo', dst='juliet', type='love')
	graph.update_edge(src='juliet', dst='romeo', type='love')

	query = list(graph.query_vertices({}))
	assert len(query) == 2

	query = list(graph.query_vertices({ "type" : "female" }))
	assert len(query) == 1
	assert query[0]['id'] == 'juliet'

	query = list(graph.query_edges({ "dst" : "juliet" }))
	assert len(query) == 1
	assert query[0]['type'] == 'love'