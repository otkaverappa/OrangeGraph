from gremlin import GremlinGraph
import os
import xml.etree.ElementTree as ET

class AirRoutesGraph:
	@staticmethod
	def get():
		g = GremlinGraph()

		path = os.path.join( 'tests', 'gremlin', 'air-routes', 'air-routes-latest.graphml' )
		root = ET.parse( path ).getroot()

		i = len( root.tag )
		while root.tag[ i - 1 ] != '}':
			i = i - 1

		namespaceString = root.tag[ : i ]
		graphNodeTag = namespaceString + 'graph'
		vertexNodeTag = namespaceString + 'node'
		edgeNodeTag = namespaceString + 'edge'

		graphNode = root.find( graphNodeTag )
		for graphObject in graphNode:
			if graphObject.tag == vertexNodeTag:
				id_ = graphObject.attrib[ 'id' ]
				props = dict()
				for propertyNode in graphObject:
					propertyKey = propertyNode.attrib[ 'key' ]
					propertyValue = propertyNode.text
					props[ propertyKey ] = propertyValue
				g.addVertex( labels=[ props[ 'labelV' ] ], props=props, id_=int( id_ ) )
			elif graphObject.tag == edgeNodeTag:
				id_ = graphObject.attrib[ 'id' ]
				fromVertex, toVertex = graphObject.attrib[ 'source' ], graphObject.attrib[ 'target' ]
				for propertyNode in graphObject:
					propertyKey = propertyNode.attrib[ 'key' ]
					propertyValue = propertyNode.text
					props[ propertyKey ] = propertyValue
				g.addEdge( int( fromVertex ), int( toVertex ), props[ 'labelE' ], props=props, id_=int( id_ ) )

		return g

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