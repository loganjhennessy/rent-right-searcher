from google.cloud import pubsub
from searcher.zipcoderequest import ZipCodeRequest
# from searcher.citysearch import CitySearch

import json
import requests
# import time


with open("/opt/searcher/config.json", "r") as f:
    config = json.loads(f.read())

cities = config["cities"]


project_id = "rent-right-dev"


def publish(msg):
    publisher = pubsub.PublisherClient()
    topic = "projects/rent-right-dev/topics/listings"
    publisher.publish(topic, msg)


for city, state in cities.items():
    zcr = ZipCodeRequest(city, state)
    zipcodes = zcr.execute()

    r = requests.get("http://jsonip.com")
    ip = r.json()["ip"].encode()

    publish(ip)

    # for zipcode in zipcodes:
    #     zcs = CitySearch(city, zipcode)
    #     zcs.execute()
