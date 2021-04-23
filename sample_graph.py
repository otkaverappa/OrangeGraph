from gremlin import GremlinGraph

class TinkerPopModernGraph:
	@staticmethod
	def get():
		g = GremlinGraph()
		
		vertexInfo = [
		(1, 'person', { 'name' : 'marko', 'age' : 29 } ),
		(2, 'person', { 'name' : 'vadas', 'age' : 27 } ),
		(3, 'software', { 'name' : 'lop', 'lang' : 'java' } ),
		(4, 'person', { 'name' : 'josh', 'age' : 32 } ),
		(5, 'software', { 'name' : 'ripple', 'lang' : 'java' } ),
		(6, 'person', { 'name' : 'peter', 'age' : 35 } ),
		]

		for id_, label, props in vertexInfo:
			g.addVertex( labels=[ label ], props=props, id_=id_ )

		edgeInfo = [
		( 7, (1, 2), 'knows', { 'weight' : 0.5 } ),
		( 8, (1, 4), 'knows', { 'weight' : 1.0 } ),
		( 9, (1, 3), 'created', { 'weight' : 0.4 } ),
		(10, (4, 5), 'created', { 'weight' : 1.0 } ),
		(11, (4, 3), 'created', { 'weight' : 0.4 } ),
		(12, (6, 3), 'created', { 'weight' : 0.2 } )
		]

		for id_, (fromVertex, toVertex), edgeLabel, props in edgeInfo:
			g.addEdge( fromVertex, toVertex, edgeLabel, props=props, id_=id_ )

		return g