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

	def E( self ):
		return self.graph.E()

class DataTraverserExpected( Exception ):
	pass

class GremlinTraverser:
	graphReference = None
	COMPUTATION_OBJECT_ID, COMPUTATION_TAG = -1, 'compute'

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
	def initDataTraverser( data ):
		return GremlinTraverser.init( GremlinTraverser.COMPUTATION_OBJECT_ID,
			                          labelDict={ GremlinTraverser.COMPUTATION_TAG : data } )

	@staticmethod
	def isDataTraverser( gremlinTraverser ):
		objectId, labelDict, _ = gremlinTraverser
		if objectId == GremlinTraverser.COMPUTATION_OBJECT_ID:
			return True, labelDict[ GremlinTraverser.COMPUTATION_TAG ]
		return False, None

	@staticmethod
	def getDataFromTraverser( gremlinTraverser ):
		isDataTraverser, data = GremlinTraverser.isDataTraverser( gremlinTraverser )
		if not isDataTraverser:
			raise DataTraverserExpected()
		return data

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
	def toString( objectId ):
		graphObjectReference = GremlinTraverser.graphReference.getGraphObjectReference( objectId )
		return GremlinTraverser.__repr__( graphObjectReference )

	@staticmethod
	def repr( gremlinTraverser ):
		isDataTraverser, data = GremlinTraverser.isDataTraverser( gremlinTraverser )
		if isDataTraverser:
			return str( data )
		
		graphObjectReference = GremlinTraverser.get( gremlinTraverser )
		return GremlinTraverser.__repr__( graphObjectReference )

	@staticmethod
	def __repr__( graphObjectReference ):
		if graphObjectReference.objectType == 'VERTEX':
			objectDescription = 'v[{}]'.format( graphObjectReference.id )
		elif graphObjectReference.objectType == 'EDGE':
			fromVertex, toVertex = graphObjectReference.fromTo()
			edgeLabel = graphObjectReference.edgeLabel
			objectDescription = 'e[{}][{}-{}->{}]'.format( graphObjectReference.id, fromVertex, edgeLabel, toVertex )
		return objectDescription

class VertexNotPresentError( Exception ):
	pass

class EdgeNotPresentError( Exception ):
	pass

class GremlinPredicates:
	pass

class GremlinTraversal:
	def __init__( self, graphReference ):
		self.graphReference = graphReference
		self.traverserList = list()

		self.sideEffects = dict()

		GremlinTraverser.setGraphReference( graphReference )

		# Gremlin function names which are also Python keywords are added using setattr.
		setattr( self, 'as', self.__as )

	def materialize( self ):
		if isinstance( self.traverserList, filter ):
			self.traverserList = list( self.traverserList )

	def _toString( self ):
		return [ GremlinTraverser.repr( traverser ) for traverser in self.traverserList ]

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

	def E( self, * arguments ):
		if len( arguments ) == 0:
			self.traverserList = [ GremlinTraverser.init( edgeId , pathList=[ edgeId ] ) for edgeId in self.graphReference.E() ]
		else:
			edgeId, * _ = arguments
			edgeId = int( edgeId )
			if edgeId in self.graphReference.E():
				self.traverserList = [ GremlinTraverser.init( edgeId, pathList=[ edgeId ] ) ]
			else:
				raise EdgeNotPresentError( 'Edge with id={} not present'.format( edgeId ) )

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
		def matchProperty( traverser, propertyName, propertyValue ):
			return GremlinTraverser.get( traverser ).props.get( propertyName ) == propertyValue

		if len( arguments ) == 2:
			propertyName, propertyValue = arguments
			self.traverserList = filter( lambda traverser : matchProperty( traverser, propertyName, propertyValue ),
				                         self.traverserList )
		elif len( arguments ) == 1:
			propertyName, * _ = arguments
			self.traverserList = filter( lambda traverser : GremlinTraverser.get( traverser ).props.get( propertyName ) is not None,
				                         self.traverserList )
		elif len( arguments ) == 3:
			label, propertyName, propertyValue = arguments
			self.traverserList = filter( lambda traverser : label in GremlinTraverser.get( traverser ).labels and
				                         matchProperty( traverser, propertyName, propertyValue ),
				                         self.traverserList )

	def count( self ):
		self.materialize()
		self.traverserList = [ GremlinTraverser.initDataTraverser( len( self.traverserList ) ) ]

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

	def outE( self, edgeLabel=None ):
		pass

	def dedup( self ):
		dataList = [ GremlinTraverser.getDataFromTraverser( traverser ) for traverser in self.traverserList ]
		dedupDataList = list( set( dataList ) )
		self.traverserList = [ GremlinTraverser.initDataTraverser( data ) for data in dedupDataList ]

	def fold( self ):
		dataList = list()
		foldedObject = GremlinTraverser.initDataTraverser( dataList )
		for traverser in self.traverserList:
			dataList.append( GremlinTraverser.getDataFromTraverser( traverser ) )
		self.traverserList = [ foldedObject ]

	def path( self ):
		def traverserMapper( traverser ):
			_, _, pathList = traverser
			pathString = ','.join( [ GremlinTraverser.toString( objectId ) for objectId in pathList ] )
			pathDescription = '[' + pathString + ']'
			return GremlinTraverser.initDataTraverser( pathDescription )
		self.traverserList = map( traverserMapper, self.traverserList )

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

	def values( self, * propertyNames ):
		def traverserMapper( traverser ):
			props = GremlinTraverser.get( traverser ).props
			if len( propertyNames ) == 0:
				return props.values()
			else:
				return [ props[ propertyName ] for propertyName in propertyNames if props.get( propertyName ) is not None ]
		
		self.traverserList = [  GremlinTraverser.initDataTraverser( propertyValue )
		                        for traverser in self.traverserList
		                        for propertyValue in traverserMapper( traverser ) ]

	def max( self ):
		self.traverserList = [
		GremlinTraverser.initDataTraverser( max( map( lambda traverser : GremlinTraverser.getDataFromTraverser( traverser ),
			                                          self.traverserList ) ) )
		]

	def min( self ):
		self.traverserList = [
		GremlinTraverser.initDataTraverser( min( map( lambda traverser : GremlinTraverser.getDataFromTraverser( traverser ),
			                                          self.traverserList ) ) )
		]

	def mean( self ):
		self.traverserList = [
		GremlinTraverser.initDataTraverser( statistics.mean( map( lambda traverser : GremlinTraverser.getDataFromTraverser( traverser ),
			                                                      self.traverserList ) ) )
		]

	def sum( self ):
		self.traverserList = [
		GremlinTraverser.initDataTraverser( sum( map( lambda traverser : GremlinTraverser.getDataFromTraverser( traverser ),
			                                          self.traverserList ) ) )
		]

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

	def next( self ):
		self.materialize()

class GremlinExecutionEngine:
	def __init__( self ):
		self.g = sample_graph.TinkerPopModernGraph.get()
		self.stack = list()
		self.stackFrameIndex = 0

		self.controlSteps = {
		'repeat' : self.__repeat,
		'branch' : self.__branch,
		}

		self.variables = dict()

	def setGraph( self, graph ):
		self.g = graph

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
		self.gremlinExecutionEngine.setGraph( sample_graph.AirRoutesGraph.get() )
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

class GremlinTest( unittest.TestCase ):
	def test_Gremlin( self ):
		GremlinConsole().console()

if __name__ == '__main__':
	unittest.main()