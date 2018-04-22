import datetime
import json

from google.cloud import datastore
from google.cloud import pubsub
from rentrightsearcher.zipsearch import get_search_results
from rentrightsearcher.util.log import get_configured_logger

logger = get_configured_logger(__name__)

ds_client = datastore.Client()
publisher = pubsub.PublisherClient()


def fetch_cities(ds_client):
    cities = []

    query = ds_client.query(kind="CityZipCodeMap")
    for record in query.fetch():
        city = {
            "city": record["city"],
            "state": record["state"],
            "zipcodes": record["zipcodes"]
        }
        cities.append(city)
    return cities


def publish_listing(listing):
    def date_converter(d):
        if isinstance(d, datetime.datetime):
            return d.__str__()
    project_id = "rent-right-dev"
    topic = "projects/{}/topics/listings".format(project_id)
    data = json.dumps(listing, default=date_converter).encode("utf-8")
    publisher.publish(topic, data)


def save_listing(listing):
    """Write a list of listing dicts to Datastore.

    Data is written to the 'ObservedListing' kind.

    Arguments:
        listings: list of dicts containing listings
    """
    kind = "ListingLink"

    name = listing["clid"]
    key = ds_client.key(kind, name)

    listing_entity = datastore.Entity(key=key)
    listing_entity["content_acquited"] = listing["content_acquired"]
    listing_entity["imgs_acquired"] = listing["imgs_acquired"]
    listing_entity["link"] = listing["link"]
    listing_entity["s"] = listing["s"]
    listing_entity["time_added"] = listing["time_added"]
    listing_entity["time_observed"] = listing["time_observed"]
    listing_entity["title"] = listing["title"]
    listing_entity["zipcode"] = listing["zipcode"]

    ds_client.put(listing_entity)


def main():
    cities = fetch_cities(ds_client)

    for city in cities:
        for zipcode in city["zipcodes"]:
            listings = get_search_results(city["city"], zipcode)
            count = 0
            for listing in listings:
                key = ds_client.key("ListingLink", listing["clid"])
                dup_listing_entity = ds_client.get(key)
                if dup_listing_entity is None:
                    save_listing(listing)
                    publish_listing(listing)
                    count += 1
                else:
                    dup_listing_entity["time_observed"] = listing["time_observed"]
                    ds_client.put(dup_listing_entity)
            logger.info("Wrote {} new listings to Datastore".format(count))


if __name__ == "__main__":
    main()
