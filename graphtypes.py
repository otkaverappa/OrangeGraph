import unittest

class GraphObject:
	def __init__( self, props=None ):
		self._id = None
		self._props = props or dict()

	def setProperty( self, propertyName, propertyValue ):
		self._props[ propertyName ] = propertyValue

	def props( self ):
		return self._props

	def setId( self, _id ):
		assert self._id is None
		self._id = _id

	def getId( self ):
		return self._id

class GraphEdge( GraphObject ):
	def __init__( self, fromVertexId, toVertexId, edgeLabel=None, props=None ):
		self.fromVertexId, self.toVertexId = fromVertexId, toVertexId
		self._edgeLabel = edgeLabel
		
		GraphObject.__init__( self, props )

	def setEdgeLabel( self, edgeLabel ):
		assert self._edgeLabel is None
		self._edgeLabel = edgeLabel

	def edgeLabel( self ):
		return self._edgeLabel

	def fromTo( self ):
		return self.fromVertexId, self.toVertexId

	def __repr__( self ):
		header = 'GraphEdge @{} edgeId={}'.format( id( self ), self._id )
		edgeInfo = 'edgeLabel : {} Direction : {} --> {}'.format( self._edgeLabel, self.fromVertexId, self.toVertexId )
		props  = 'props  : {}'.format( self._props )
		return '{} {} {}'.format( header, edgeInfo, props )

class GraphVertex( GraphObject ):
	def __init__( self, labels=None, props=None ):
		self._labels = set()
		if labels is not None:
			self._labels = set( labels )
		
		self.outgoingEdges = set()
		self.incomingEdges = set()

		GraphObject.__init__( self, props )

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
		self._labels.add( label )

	def labels( self ):
		return self._labels

	def __repr__( self ):
		header = 'GraphVertex @{} vertexId={}'.format( id( self ), self._id )
		labels = 'labels : {}'.format( self._labels )
		props  = 'props  : {}'.format( self._props )
		return '{} {} {}'.format( header, labels, props )

if __name__ == '__main__':
	unittest.main()