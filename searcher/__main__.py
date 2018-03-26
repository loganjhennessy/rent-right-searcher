from searcher.zipcoderequest import ZipCodeRequest
from searcher.zipcodesearch import ZipCodeSearch

import sys

city = sys.argv[1]
zipcode = sys.argv[2]

print(city)
print(zipcode)

zcr = ZipCodeRequest()
zcr.execute()

zcs = ZipCodeSearch()
zcs.execute()
