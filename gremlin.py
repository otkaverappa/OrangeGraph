import unittest
import codecs

from graph import Graph
from graphtypes import GraphVertex, GraphEdge
from gremlinparser import GremlinParser, GremlinFunction, GremlinToken

import sample_graph

class GremlinGraph:
	def __init__( self ):
		self.graph = Graph()

	def addVertex( self, labels=None, props=None, id_=None ):
		graphVertex = GraphVertex( labels=labels, props=props )
		id_ = self.graph.addVertex( graphVertex, id_=id_ )
		return id_

	def addEdge( self, fromVertexId, toVertexId, edgeLabel, props=None, id_=None ):
		graphEdge = GraphEdge( fromVertexId=fromVertexId, toVertexId=toVertexId, edgeLabel=edgeLabel, props=props )
		id_ = self.graph.addEdge( graphEdge, id_=id_ )
		return id_

	def getGraphObjectReference( self, id_ ):
		return self.graph.getGraphObjectReference( id_ )

	def V( self ):
		return self.graph.V()

class GremlinTraverser:
	graphReference = None

	def __init__( self, objectId ):
		self.objectId = objectId

	def __repr__( self ):
		graphObjectReference = self.get()
		if graphObjectReference.objectType == 'VERTEX':
			objectDescription = 'v[{}]'.format( graphObjectReference.id )
		elif graphObjectReference.objectType == 'EDGE':
			fromVertex, toVertex = graphObjectReference.fromTo()
			edgeLabel = graphObjectReference.edgeLabel()
			objectDescription = 'e[{}][{}-{}->{}]'.format( graphObjectReference.id, fromVertex, toVertex, edgeLabel )
		return objectDescription

	@staticmethod
	def setGraphReference( graphReference ):
		GremlinTraverser.graphReference = graphReference

	def get( self ):
		return GremlinTraverser.graphReference.getGraphObjectReference( self.objectId )

class VertexNotPresentError( Exception ):
	pass

class GremlinTraversal:
	def __init__( self, graphReference ):
		self.graphReference = graphReference
		self.traverserList = list()

		self.terminalStepApplied = False
		self.terminalResultList = list()

		GremlinTraverser.setGraphReference( graphReference )

	def _toString( self ):
		if self.terminalStepApplied:
			return self.terminalResultList
		return [ repr( traverser ) for traverser in self.traverserList ]

	def V( self, * arguments ):
		if len( arguments ) == 0:
			self.traverserList = [ GremlinTraverser( vertexId ) for vertexId in self.graphReference.V() ]
		else:
			vertexId, * _ = arguments
			vertexId = int( vertexId )
			if vertexId in self.graphReference.V():
				self.traverserList = [ GremlinTraverser( vertexId ) ]
			else:
				raise VertexNotPresentError( 'Vertex with id={} not present'.format( vertexId ) )

	def addV( self, * labels ):
		id_ = self.graphReference.addVertex( labels=labels )

	def addE( self, edgeLabel ):
		pass

	def property( self, propertyName, propertyValue ):
		for traverser in self.traverserList:
			traverser.get().setProperty( propertyName, propertyValue )

	def hasLabel( self, * labels ):
		labels = set( labels )
		self.traverserList = filter( lambda traverser : len( set.intersection( labels, traverser.get().labels ) ) > 0,
			                         self.traverserList )

	def has( self, * arguments ):
		if len( arguments ) == 2:
			propertyName, propertyValue = arguments
			self.traverserList = filter( lambda traverser : traverser.get().props.get( propertyName ) == propertyValue,
				                         self.traverserList )

	def out( self, edgeLabel ):
		newTraverserList = list()
		for traverser in self.traverserList:
			for outgoingEdgeId in traverser.get().outgoingEdges:
				edgeObjectReference = self.graphReference.getGraphObjectReference( outgoingEdgeId )
				if edgeObjectReference.label == edgeLabel:
					fromVertex, toVertex = edgeObjectReference.fromTo()
					newTraverserList.append( GremlinTraverser( toVertex ) )
		self.traverserList = newTraverserList

	def values( self, propertyName ):
		for traverser in self.traverserList:
			propertyValue = traverser.get().props.get( propertyName )
			if propertyValue is None:
				continue
			self.terminalResultList.append( propertyValue )
		self.terminalStepApplied = True

class GremlinExecutionEngine:
	def __init__( self ):
		self.g = sample_graph.TinkerPopModernGraph.get()

	def exec( self, gremlinQuery ):
		traversal = GremlinTraversal( self.g )

		for gremlinToken in GremlinParser.parse( gremlinQuery ):
			if gremlinToken.tokenType == GremlinToken.GREMLIN_FUNCTION:
				functionName, argumentList = gremlinToken.functionName, gremlinToken.argumentList
				self.__executeStep( traversal, functionName, argumentList )
		for traversalState in traversal._toString():
			print( '==>{}'.format( traversalState ) )

	def __executeStep( self, traversal, functionName, argumentList ):
		try:
			function = getattr( traversal, functionName )
		except AttributeError:
			print( 'Gremlin step {} not implemented'.format( functionName ) )
			return
		literals = [ argument.literal for argument in argumentList ]
		function( * literals )

class GremlinConsole:
	def __init__( self ):
		self.commandHandlers = dict()
		self.terminateConsole = False

		self.commandHandlers[ 'exit' ] = self.handleExit
		self.commandHandlers[ 'quit' ] = self.handleExit
		self.commandHandlers[ 'load' ] = self.handleLoad

		self.gremlinExecutionEngine = GremlinExecutionEngine()

	def handleExit( self ):
		print( 'Stopping Gremlin console...' )
		self.terminateConsole = True

	def handleLoad( self ):
		print( 'Loading air-routes graph...' )
		loadAirRoutesGraph()
		print( 'Finished loading air-routes graph...' )

	def console( self ):
		print( 'Starting Gremlin console...' )
		while not self.terminateConsole:
			print( 'OrangeGremlin> ', end=str() )
			commandString = input()
			
			commandStringLowercase = commandString.lower()
			if commandStringLowercase in self.commandHandlers:
				self.commandHandlers[ commandStringLowercase ]()
				continue
			self.gremlinExecutionEngine.exec( commandString )

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

class GremlinTest( unittest.TestCase ):
	def test_Gremlin( self ):
		GremlinConsole().console()

if __name__ == '__main__':
	unittest.main()