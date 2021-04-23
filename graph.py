import unittest

from graphtypes import GraphVertex, GraphEdge

class GraphObjectNotFound( Exception ):
	pass

class VertexDeletionError( Exception ):
	pass

class Graph:
	def __init__( self ):
		self.vertices = dict()
		self.edges = dict()

		self.nextObjectId = 0

	def addVertex( self, graphVertex, id_=None ):
		id_ = id_ or self._allocateId()
		graphVertex.setId( id_ )
		self.vertices[ id_ ] = graphVertex
		return id_

	def addEdge( self, graphEdge, id_=None ):
		fromVertexId, toVertexId = graphEdge.fromTo()
		assert fromVertexId in self.vertices
		assert toVertexId in self.vertices

		id_ = id_ or self._allocateId()
		graphEdge.setId( id_ )
		self.vertices[ fromVertexId ].addOutgoingEdge( id_ )
		self.vertices[ toVertexId ].addIncomingEdge( id_ )
		self.edges[ id_ ] = graphEdge
		return id_

	def getGraphObjectReference( self, id_ ):
		if id_ in self.vertices:
			return self.vertices[ id_ ]
		if id_ not in self.edges:
			raise GraphObjectNotFound( 'object with id = {} not present'.format( id_ ) )
		return self.edges[ id_ ]

	def deleteVertex( self, id_ ):
		if id_ not in self.vertices:
			raise GraphObjectNotFound( 'object with id = {} not present'.format( id_ ) )

		graphVertex = self.vertices[ id_ ]
		if graphVertex.inDegree() > 0 or graphVertex.outDegree() > 0:
			raise VertexDeletionError( 'object with id = {} cannot be deleted while in use'.format( id_ ) )

		del self.vertices[ id_ ]

	def detachAndDeleteVertex( self, id_ ):
		if id_ not in self.vertices:
			raise GraphObjectNotFound( 'object with id = {} not present'.format( id_ ) )

		graphVertex = self.vertices[ id_ ]
		for edgeId in set.union( graphVertex.incomingEdges(), graphVertex.outgoingEdges() ):
			self.deleteEdge( edgeId )
		self.deleteVertex( id_ )

	def deleteEdge( self, id_ ):
		if id_ not in self.edges:
			raise GraphObjectNotFound( 'object with id = {} not present'.format( id_ ) )

		fromVertexId, toVertexId = self.edges[ id_ ].fromTo()
		self.vertices[ fromVertexId ].removeOutgoingEdge( id_ )
		self.vertices[ toVertexId ].removeIncomingEdge( id_ )

		del self.edges[ id_ ]

	def V( self ):
		return self.vertices.keys()

	def E( self ):
		return self.edges.keys()

	def _allocateId( self ):
		while True:
			id_ = self.nextObjectId
			self.nextObjectId += 1
			if id_ in self.vertices or id_ in self.edges:
				continue
			break
		return id_

	def __repr__( self ):
		return 'graph @{} vertices: {} edges: {}'.format( id( self ), len( self.vertices ), len( self.edges ) )

if __name__ == '__main__':
	unittest.main()