import unittest
import tokenize
import io

class GremlinSyntaxError( Exception ):
	pass

class GremlinToken:
	GREMLIN_IDENTIFIER, GREMLIN_ASSIGN, GREMLIN_FUNCTION, GREMLIN_LITERAL = 'IDENTIFIER', 'ASSIGN', 'FUNCTION', 'LITERAL'
	
	def __init__( self, tokenType ):
		assert tokenType in (GremlinToken.GREMLIN_IDENTIFIER, GremlinToken.GREMLIN_ASSIGN, GremlinToken.GREMLIN_FUNCTION,
			                 GremlinToken.GREMLIN_LITERAL)
		self.tokenType = tokenType

class GremlinIdentifier( GremlinToken ):
	def __init__( self, identifierName ):
		self.identifierName = identifierName
		GremlinToken.__init__( self, GremlinToken.GREMLIN_IDENTIFIER )

	def __repr__( self ):
		return 'GremlinIdentifier @{} identifierName={}'.format( id( self ), self.identifierName )

class GremlinAssign( GremlinToken ):
	def __init__( self ):
		GremlinToken.__init__( self, GremlinToken.GREMLIN_ASSIGN )

	def __repr__( self ):
		return 'GremlinAssign @{}'.format( id( self ) )

class GremlinFunction( GremlinToken ):
	def __init__( self, functionName, argumentList=None ):
		self.functionName = functionName
		self.argumentList = argumentList or list()
		GremlinToken.__init__( self, GremlinToken.GREMLIN_FUNCTION )

	def addArgument( self, argument ):
		self.argumentList.append( argument )

	def __repr__( self ):
		return 'GremlinFunction @{} functionName={} argumentList={}'.format( id( self ), self.functionName, self.argumentList )

class GremlinLiteral( GremlinToken ):
	def __init__( self, literal ):
		self.literal = literal
		GremlinToken.__init__( self, GremlinToken.GREMLIN_LITERAL )

	def __repr__( self ):
		return 'GremlinLiteral @{} literal={}'.format( id( self ), self.literal )

class GremlinParser:
	@staticmethod
	def parse( commandString ):
		gremlinTokenList = list()

		tokenList = tokenize.tokenize( io.BytesIO( commandString.encode() ).readline )
		GremlinParser._process( tokenList, gremlinTokenList )

		return gremlinTokenList

	@staticmethod
	def _processFunction( tokenList, gremlinFunction ):
		while True:
			tokenType, tokenValue, * _ = next( tokenList )
			if tokenType == tokenize.OP and tokenValue == ')':
				break
			if tokenType == tokenize.STRING:
				literal = tokenValue[ 1 : -1 ] # tokenValue includes quotes and is of the form: 'Apple'. Remove quotes before adding to the argument list.
				gremlinFunction.addArgument( GremlinLiteral( literal ) )
			elif tokenType == tokenize.NUMBER:
				literal = tokenValue
				gremlinFunction.addArgument( GremlinLiteral( literal ) )
			elif tokenType == tokenize.NAME:
				nestedGremlinFunction = GremlinFunction( functionName=tokenValue )
				gremlinFunction.addArgument( nestedGremlinFunction )
				GremlinParser._processFunction( tokenList, nestedGremlinFunction )

	@staticmethod
	def _process( tokenList, gremlinTokenList ):
		while True:
			tokenType, tokenValue, * _ = next( tokenList )
			if tokenType == tokenize.NAME:
				break
			if tokenType == tokenize.ENDMARKER:
				return
		
		nextTokenType, nextTokenValue, * _ = next( tokenList )
		if nextTokenType == tokenize.OP and nextTokenValue == '(':
			gremlinFunction = GremlinFunction( functionName=tokenValue )
			gremlinTokenList.append( gremlinFunction )
			GremlinParser._processFunction( tokenList, gremlinFunction )
		elif nextTokenType == tokenize.OP and nextTokenValue in ('.', '='):
			gremlinTokenList.append( GremlinIdentifier( identifierName=tokenValue ) )
			if nextTokenValue == '=':
				gremlinTokenList.append( GremlinAssign() )
		
		GremlinParser._process( tokenList, gremlinTokenList )
		return gremlinTokenList

class GremlinParserTest( unittest.TestCase ):
	def test_GremlinParser( self ):
		gremlinQuery = "i = g.V().has( 'name', 'New York' ).out( 'connects' ).map( values( 'name' ) )"
		print( gremlinQuery )
		for gremlinToken in GremlinParser.parse( gremlinQuery ):
			print( gremlinToken )

if __name__ == '__main__':
	unittest.main()