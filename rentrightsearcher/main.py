import json
import requests
# import time

from google.cloud import datastore
from google.cloud import pubsub
from rentrightsearcher.citysearch import get_search_results


def fetch_cities(client):
    cities = []

    # Query Datastore
    client = datastore.Client()
    query = client.query(kind="CityZipCodeMap")
    for record in query.fetch():
        city = {
            "city": record["city"],
            "status": record["state"],
            "zipcodes": record["zipcodes"]
        }
        cities.append(city)
    return cities


def publish_listing(listing):
    project_id = "rent-right-dev"
    publisher = pubsub.PublisherClient()
    topic = "projects/rent-right-dev/topics/listings"
    publisher.publish(topic, listing.encode())


def save_listing(listing):
    pass


def update_listing(listing):
    pass


def main():
    ds_client = datastore.Client()
    query = ds_client.query(kind="CityZipCodeMap")
    cities = fetch_cities(ds_client)

    # For each entry (city) in Datastore
    for city in cities:
        # For each zip in each city
        for zipcode in city["zipcodes"]:
            # Do a search using city/zip
            listings = get_search_results(city, zipcode)
            # For each listing returned
            for listing in listings:
                ds_client.query("Listing")
                query.add_filter("listing_id", "=", listing["id"])
                # Check Datastore to see if it exists and has been processed
                if query.fetch() is None:
                    # Enter it in Datastore
                    save_listing(listing)
                    # Publish to pubsub
                    publish_listing(listing)
                else:
                    # Update the last_seen field
                    update_listing(listing)


if __name__ == "__main__":
    main()
