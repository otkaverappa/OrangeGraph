import unittest
import codecs
import copy
import statistics

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

	@staticmethod
	def setGraphReference( graphReference ):
		GremlinTraverser.graphReference = graphReference

	@staticmethod
	def init( objectId, labelDict=None, pathList=None ):
		# GremlinTraverser object is a tuple - (objectId, labelDict, pathList)
		labelDict = labelDict or dict()
		pathList = pathList or list()
		return (objectId, labelDict, pathList)

	@staticmethod
	def clone( gremlinTraverser, newObjectId, newLabel=None ):
		_, labelDict, pathList = gremlinTraverser
		newLabelDict = copy.deepcopy( labelDict )
		newPathList = copy.deepcopy( pathList )
		if newLabel is not None:
			newLabelDict[ newLabel ] = newObjectId
		newPathList.append( newObjectId )
		return (newObjectId, newLabelDict, newPathList)

	@staticmethod
	def signature( gremlinTraverser ):
		objectId, labelDict, pathList = gremlinTraverser
		return (objectId, tuple( sorted( labelDict.items() ) ), tuple( pathList ) )

	@staticmethod
	def get( gremlinTraverser ):
		objectId, _, _ = gremlinTraverser
		return GremlinTraverser.graphReference.getGraphObjectReference( objectId )

	@staticmethod
	def applyLabel( gremlinTraverser, label ):
		objectId, labelDict, _ = gremlinTraverser
		labelDict[ label ] = objectId

	@staticmethod
	def applyLabels( gremlinTraverser, labels ):
		for label in labels:
			GremlinTraverser.applyLabel( gremlinTraverser, label )

	@staticmethod
	def addPath( gremlinTraverser, vertexId ):
		_, _, pathList = gremlinTraverser
		pathList.append( vertexId )

	@staticmethod
	def toString( gremlinTraverser ):
		graphObjectReference = GremlinTraverser.get( gremlinTraverser )
		if graphObjectReference.objectType == 'VERTEX':
			objectDescription = 'v[{}]'.format( graphObjectReference.id )
		elif graphObjectReference.objectType == 'EDGE':
			fromVertex, toVertex = graphObjectReference.fromTo()
			edgeLabel = graphObjectReference.edgeLabel()
			objectDescription = 'e[{}][{}-{}->{}]'.format( graphObjectReference.id, fromVertex, toVertex, edgeLabel )
		return objectDescription

class VertexNotPresentError( Exception ):
	pass

class GremlinTraversal:
	def __init__( self, graphReference ):
		self.graphReference = graphReference
		self.traverserList = list()

		self.terminalStepApplied = False
		self.terminalResultList = list()

		self.sideEffects = dict()
		self.traversalLabels = dict()

		GremlinTraverser.setGraphReference( graphReference )

		# Gremlin function names which are also Python keywords are added using setattr.
		setattr( self, 'as', self.__as )

	def _toString( self ):
		if self.terminalStepApplied:
			return self.terminalResultList
		return [ GremlinTraverser.toString( traverser ) for traverser in self.traverserList ]

	def V( self, * arguments ):
		if len( arguments ) == 0:
			self.traverserList = [ GremlinTraverser.init( vertexId, pathList=[ vertexId ] ) for vertexId in self.graphReference.V() ]
		else:
			vertexId, * _ = arguments
			vertexId = int( vertexId )
			if vertexId in self.graphReference.V():
				self.traverserList = [ GremlinTraverser.init( vertexId, pathList=[ vertexId ] ) ]
			else:
				raise VertexNotPresentError( 'Vertex with id={} not present'.format( vertexId ) )

	def addV( self, * labels ):
		id_ = self.graphReference.addVertex( labels=labels )

	def addE( self, edgeLabel ):
		pass

	def property( self, propertyName, propertyValue ):
		for traverser in self.traverserList:
			GremlinTraverser.get( traverser ).setProperty( propertyName, propertyValue )

	def hasLabel( self, * labels ):
		labels = set( labels )
		self.traverserList = filter( lambda traverser : len( set.intersection( labels, GremlinTraverser.get( traverser ).labels ) ) > 0,
			                         self.traverserList )

	def has( self, * arguments ):
		if len( arguments ) == 2:
			propertyName, propertyValue = arguments
			self.traverserList = filter( lambda traverser : GremlinTraverser.get( traverser ).props.get( propertyName ) == propertyValue,
				                         self.traverserList )

	def out( self, edgeLabel=None ):
		newTraverserList = list()
		for traverser in self.traverserList:
			for outgoingEdgeId in GremlinTraverser.get( traverser ).outgoingEdges:
				edgeObjectReference = self.graphReference.getGraphObjectReference( outgoingEdgeId )
				if edgeLabel is None or edgeObjectReference.label == edgeLabel:
					fromVertex, toVertex = edgeObjectReference.fromTo()
					newGremlinTraverser = GremlinTraverser.clone( traverser, toVertex )
					newTraverserList.append( newGremlinTraverser )
		self.traverserList = newTraverserList

	def both( self, edgeLabel=None ):
		newTraverserList = list()
		for traverser in self.traverserList:
			for outgoingEdgeId in GremlinTraverser.get( traverser ).outgoingEdges:
				edgeObjectReference = self.graphReference.getGraphObjectReference( outgoingEdgeId )
				if edgeLabel is None or edgeObjectReference.label == edgeLabel:
					fromVertex, toVertex = edgeObjectReference.fromTo()
					newGremlinTraverser = GremlinTraverser.clone( traverser, toVertex )
					newTraverserList.append( newGremlinTraverser )
			for incomingEdgeId in GremlinTraverser.get( traverser ).incomingEdges:
				edgeObjectReference = self.graphReference.getGraphObjectReference( incomingEdgeId )
				if edgeLabel is None or edgeObjectReference.label == edgeLabel:
					fromVertex, toVertex = edgeObjectReference.fromTo()
					newGremlinTraverser = GremlinTraverser.clone( traverser, fromVertex )
					newTraverserList.append( newGremlinTraverser )
		self.traverserList = newTraverserList

	def values( self, propertyName ):
		for traverser in self.traverserList:
			propertyValue = GremlinTraverser.get( traverser ).props.get( propertyName )
			if propertyValue is None:
				continue
			self.terminalResultList.append( propertyValue )
		self.terminalStepApplied = True

	def max( self ):
		assert self.terminalStepApplied
		self.terminalResultList = [ max( self.terminalResultList ) ]

	def min( self ):
		assert self.terminalStepApplied
		self.terminalResultList = [ min( self.terminalResultList ) ]

	def mean( self ):
		assert self.terminalStepApplied
		self.terminalResultList = [ statistics.mean( self.terminalResultList ) ]

	def __as( self, * labels ):
		for traverser in self.traverserList:
			GremlinTraverser.applyLabels( traverser, labels )

	def select( self, * labels ):
		for traverser in self.traverserList:
			objectId, labelDict, _ = traverser
			
			objectIdList = list()
			for label in labels:
				objectIdList.append( labelDict.get( label ) )
			if all( objectIdList ):
				print( [ '{}:{}'.format( label, objectId ) for label, objectId in zip( labels, objectIdList ) ] )
		self.terminalStepApplied = True

	def times( self, numberOfTimesToRepeat ):
		remainingLoops = self.sideEffects.get( 'loops' ) or int( numberOfTimesToRepeat )
		remainingLoops -= 1
		
		self.sideEffects[ 'loops' ] = remainingLoops
		if remainingLoops == 0:
			del self.sideEffects[ 'loops' ]
			return None
		return -1

class GremlinExecutionEngine:
	def __init__( self ):
		self.g = sample_graph.TinkerPopModernGraph.get()
		self.stack = list()
		self.stackFrameIndex = 0

		self.controlSteps = {
		'repeat' : self.__repeat,
		'branch' : self.__branch,
		}

	def exec( self, gremlinQuery ):
		traversal = GremlinTraversal( self.g )
		gremlinTokenList = GremlinParser.parse( gremlinQuery )

		self.__exec( traversal, gremlinTokenList )

	def __exec( self, traversal, gremlinTokenList ):
		self.stack.append( self.stackFrameIndex )
		self.stackFrameIndex += 1
		
		pc = 0

		while pc < len( gremlinTokenList ):
			gremlinToken = gremlinTokenList[ pc ]

			if gremlinToken.tokenType == GremlinToken.GREMLIN_FUNCTION:
				functionName, argumentList = gremlinToken.functionName, gremlinToken.argumentList
				pc += self.__executeStep( traversal, functionName, argumentList ) or 1
			else:
				pc += 1

		self.stack.pop()
		
		if len( self.stack ) == 0:
			for traversalState in traversal._toString():
				print( '==>{}'.format( traversalState ) )

	def __repeat( self, traversal, functionName, argumentList ):
		gremlinTokenList = argumentList
		self.__exec( traversal, gremlinTokenList )

	def __branch( self, traversal, functionName, argumentList ):
		pass

	def __executeStep( self, traversal, functionName, argumentList ):
		if functionName in self.controlSteps:
			self.controlSteps[ functionName ] ( traversal, functionName, argumentList )
			return 
		
		try:
			function = getattr( traversal, functionName )
		except AttributeError:
			print( 'Gremlin step {} not implemented'.format( functionName ) )
			return
		literals = [ argument.literal for argument in argumentList ]
		return function( * literals )

class GremlinConsole:
	def __init__( self ):
		self.commandHandlers = dict()
		self.terminateConsole = False

		for command in ('exit', 'quit', 'q'):
			self.commandHandlers[ command ] = self.handleExit
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