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

	def addVertex( self, graphVertex ):
		id_ = self._allocateId()
		graphVertex.setId( id_ )
		self.vertices[ id_ ] = graphVertex
		return id_

	def addEdge( self, graphEdge ):
		fromVertexId, toVertexId = graphEdge.fromTo()
		assert fromVertexId in self.vertices
		assert toVertexId in self.vertices

		id_ = self._allocateId()
		graphEdge.setId( id_ )
		self.vertices[ fromVertexId ].addOutgoingEdge( id_ )
		self.vertices[ toVertexId ].addIncomingEdge( id_ )
		self.edges[ id_ ] = graphEdge
		return id_

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
		return self.vertices.values()

	def E( self ):
		return self.edges.values()

	def _allocateId( self ):
		id_ = self.nextObjectId
		self.nextObjectId += 1
		return id_

	def __repr__( self ):
		return 'graph @{} vertices: {} edges: {}'.format( id( self ), len( self.vertices ), len( self.edges ) )

if __name__ == '__main__':
	unittest.main()