import unittest
import tokenize
import io

class GremlinSyntaxError( Exception ):
	pass

class GremlinToken:
	GREMLIN_IDENTIFIER, GREMLIN_ASSIGN, GREMLIN_FUNCTION = 'IDENTIFIER', 'ASSIGN', 'FUNCTION'
	
	def __init__( self, tokenType ):
		assert tokenType in (GremlinToken.GREMLIN_IDENTIFIER, GremlinToken.GREMLIN_ASSIGN, GremlinToken.GREMLIN_FUNCTION)
		self._tokenType = tokenType

	def tokenType( self ):
		return self._tokenType

class GremlinIdentifier( GremlinToken ):
	def __init__( self, identifierName ):
		self._identifierName = identifierName
		GremlinToken.__init__( self, GremlinToken.GREMLIN_IDENTIFIER )

	def identifierName( self ):
		return self._identifierName

	def __repr__( self ):
		return 'GremlinIdentifier @{} identifierName={}'.format( id( self ), self._identifierName )

class GremlinAssign( GremlinToken ):
	def __init__( self ):
		GremlinToken.__init__( self, GremlinToken.GREMLIN_ASSIGN )

	def __repr__( self ):
		return 'GremlinAssign @{}'.format( id( self ) )

class GremlinFunction( GremlinToken ):
	def __init__( self, functionName, argumentList=None ):
		self.functionName = functionName
		self.argumentList = argumentList or list()
		self.calls = None
		GremlinToken.__init__( self, GremlinToken.GREMLIN_FUNCTION )

	def addArgument( self, argument ):
		self.argumentList.append( argument )

	def setCalls( self, calledFunction ):
		assert isinstance( calledFunction, GremlinFunction )
		self.calls = calledFunction

	def __repr__( self ):
		return 'GremlinFunction @{} functionName={} argumentList={}'.format( id( self ), self.functionName, self.argumentList ) 

class GremlinParser:
	@staticmethod
	def parse( commandString ):
		gremlinTokenList = list()

		tokenList = tokenize.tokenize( io.BytesIO( commandString.encode() ).readline )
		GremlinParser._process( tokenList, gremlinTokenList )

		return gremlinTokenList

	@staticmethod
	def _processFunction( tokenList, gremlinTokenList ):
		while True:
			tokenType, tokenValue, * _ = next( tokenList )
			if tokenType == tokenize.OP and tokenValue == ')':
				break
			if tokenType == tokenize.STRING:
				argument = tokenValue[ 1 : -1 ] # tokenValue includes quotes and is of the form: 'Apple'. Remove quotes before adding to the argument list.
				gremlinTokenList[ -1 ].addArgument( argument )
			elif tokenType == tokenize.NUMBER:
				gremlinTokenList[ -1 ].addArgument( tokenValue )

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
			gremlinTokenList.append( GremlinFunction( functionName=tokenValue ) )
			GremlinParser._processFunction( tokenList, gremlinTokenList )
		elif nextTokenType == tokenize.OP and nextTokenValue in ('.', '='):
			gremlinTokenList.append( GremlinIdentifier( identifierName=tokenValue ) )
			if nextTokenValue == '=':
				gremlinTokenList.append( GremlinAssign() )
		
		GremlinParser._process( tokenList, gremlinTokenList )
		return gremlinTokenList

class GremlinParserTest( unittest.TestCase ):
	def test_GremlinParser( self ):
		commandString = "i = g.V().has( 'name', 'New York' ).out( 'connects' ).has( 'name', 'Boulder' ).values( 'companies' )"
		print( commandString )
		for gremlinToken in GremlinParser.parse( commandString ):
			print( gremlinToken )

if __name__ == '__main__':
	unittest.main()