import unittest
import codecs

from graph import Graph
from graphtypes import GraphVertex, GraphEdge

class GremlinGraph:
	def __init__( self ):
		self.graph = Graph()

	def addVertex( self, labels=None, props=None ):
		graphVertex = GraphVertex( labels=labels, props=props )
		id_ = self.graph.addVertex( graphVertex )
		return id_

	def addEdge( self, fromVertexId, toVertexId, edgeLabel, props=None ):
		graphEdge = GraphEdge( fromVertexId=fromVertexId, toVertexId=toVertexId, edgeLabel=edgeLabel, props=props )
		id_ = self.graph.addEdge( graphEdge )
		return id_

	def V( self ):
		return self.graph.V()

class Gremlin:
	def __init__( self ):
		self.g = GremlinGraph()

class GremlinConsole:
	@staticmethod
	def loadAirRoutesGraph():
		nodesFilePath = 'tests/gremlin/air-routes/air-routes-latest-nodes.csv'
		edgesFilePath = 'tests/gremlin/air-routes/air-routes-latest-edges.csv'

		graph = GremlinGraph()

		with codecs.open( nodesFilePath, encoding='utf-8' ) as nodesFile:
			headerList = nodesFile.readline().strip().split( ',' )
			_, _, * propsList = headerList

			# Ignore the line after the header.
			nodesFile.readline()
			
			idMap = dict()
			while True:
				csvLine = nodesFile.readline().strip()

				if len( csvLine ) == 0:
					break
				
				id_, label, * csvElementList = csvLine.split( ',' )
				props = dict()
				for propertyKey, propertyValue in zip( propsList, csvElementList ):
					if propertyValue == str():
						continue
					props[ propertyKey ] = propertyValue
				uid = graph.addVertex( labels=[ label ], props=props )
				idMap[ id_ ] = uid

		with codecs.open( edgesFilePath, encoding='utf-8' ) as edgesFile:
			headerList = edgesFile.readline().strip().split( ',' )

			propertyName = headerList[ -1 ]

			while True:
				csvLine = edgesFile.readline().strip()

				if len( csvLine ) == 0:
					break

				_, fromId, toId, label, propertyValue = csvLine.split( ',' )

				fromId, toId = idMap[ fromId ], idMap[ toId ]
				graph.addEdge( fromId, toId, label, { propertyName : propertyValue } )

		return graph

	@staticmethod
	def console():
		print( 'starting gremlin console...' )
		while True:
			print( 'graph> ', end=str() )
			commandString = input()
			if commandString.lower() in ('exit', 'quit'):
				print( 'stopping gremlin console...' )
				break
			elif commandString.lower() == 'load':
				print( 'loading air-routes graph...' )
				GremlinConsole.loadAirRoutesGraph()
				print( 'finished loading air-routes graph...' )

class GremlinTest( unittest.TestCase ):
	def test_Gremlin( self ):
		GremlinConsole.console()

if __name__ == '__main__':
	unittest.main()