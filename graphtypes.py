import unittest

class GraphObject:
	VERTEX, EDGE = 'VERTEX', 'EDGE'

	def __init__( self, objectType, props=None ):
		self.id = None
		assert objectType in (GraphObject.VERTEX, GraphObject.EDGE)
		self.objectType = objectType
		self.props = props or dict()	

	def setProperty( self, propertyName, propertyValue ):
		self.props[ propertyName ] = propertyValue

	def setId( self, id ):
		assert self.id is None
		self.id = id

class GraphEdge( GraphObject ):
	def __init__( self, fromVertexId, toVertexId, edgeLabel=None, props=None ):
		self.fromVertexId, self.toVertexId = fromVertexId, toVertexId
		self.edgeLabel = edgeLabel
		
		GraphObject.__init__( self, GraphObject.EDGE, props )

	def setEdgeLabel( self, edgeLabel ):
		assert self.edgeLabel is None
		self.edgeLabel = edgeLabel

	def fromTo( self ):
		return self.fromVertexId, self.toVertexId

	def __repr__( self ):
		header = 'GraphEdge @{} edgeId={}'.format( id( self ), self.id )
		edgeInfo = 'edgeLabel : {} Direction : {} --> {}'.format( self.edgeLabel, self.fromVertexId, self.toVertexId )
		props  = 'props  : {}'.format( self.props )
		return '{} {} {}'.format( header, edgeInfo, props )

	def __getattr__( self, attribute ):
		if attribute == 'labels':
			return [ self.edgeLabel ] if self.edgeLabel is not None else list()
		elif attribute == 'label':
			return self.edgeLabel
		return super().__getattribute__( attribute )

class GraphVertex( GraphObject ):
	def __init__( self, labels=None, props=None ):
		self._labels = set()
		if labels is not None:
			self.labels = set( labels )
		
		self.outgoingEdges = set()
		self.incomingEdges = set()

		GraphObject.__init__( self, GraphObject.VERTEX, props )

	def addOutgoingEdge( self, edgeId ):
		self.outgoingEdges.add( edgeId )

	def removeOutgoingEdge( self, edgeId ):
		self.outgoingEdges.remove( edgeId )

	def addIncomingEdge( self, edgeId ):
		self.incomingEdges.add( edgeId )

	def removeIncomingEdge( self, edgeId ):
		self.incomingEdges.remove( edgeId )

	def outDegree( self ):
		return len( self.outgoingEdges )

	def inDegree( self ):
		return len( self.incomingEdges )

	def addLabel( self, label ):
		self.labels.add( label )

	def __repr__( self ):
		header = 'GraphVertex @{} vertexId={}'.format( id( self ), self.id )
		labels = 'labels : {}'.format( self.labels )
		props  = 'props  : {}'.format( self.props )
		return '{} {} {}'.format( header, labels, props )

if __name__ == '__main__':
	unittest.main()