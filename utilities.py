import unittest

def expectInstance( object, expectedType ):
	if not isinstance( object, expectedType ):
		raise TypeError( 'expected type {}'.format( expectedType ) )

if __name__ == '__main__':
	unittest.main()