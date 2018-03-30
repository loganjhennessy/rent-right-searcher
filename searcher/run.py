from searcher.zipcoderequest import ZipCodeRequest
from searcher.citysearch import CitySearch

import json


with open("/opt/searcher/config.json", "r") as f:
    config = json.loads(f.read())

cities = config["cities"]

for city, state in cities.items():
    zcr = ZipCodeRequest(city, state)
    zipcodes = zcr.execute()

    for zipcode in zipcodes:
        zcs = CitySearch(city, zipcode)
        zcs.execute()
