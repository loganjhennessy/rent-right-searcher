from google.cloud import pubsub
from rentrightsearcher.zipcoderequest import ZipCodeRequest
# from rentrightsearcher.citysearch import CitySearch

import json
import requests
# import time


with open("/opt/rent-right-searcher/config/config.json", "r") as f:
    config = json.loads(f.read())

cities = config["cities"]


project_id = "rent-right-dev"


def publish(msg):
    publisher = pubsub.PublisherClient()
    topic = "projects/rent-right-dev/topics/listings"
    publisher.publish(topic, msg.encode())


for city, state in cities.items():
    zcr = ZipCodeRequest(city, state)
    zipcodes = zcr.execute()

    r = requests.get("https://api.ipify.org", params={"format": "json"})
    ip = r.json()["ip"]

    msg = {
        "ip": ip,
        "zipcodes": zipcodes
    }

    publish(json.dumps(msg))

    # for zipcode in zipcodes:
    #     zcs = CitySearch(city, zipcode)
    #     zcs.execute()
