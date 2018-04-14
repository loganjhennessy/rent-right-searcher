"""rentright.scraper.zipcodesearch"""
import datetime
import os
import requests
import time

from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from google.cloud import datastore

from rentrightsearcher.util.log import get_configured_logger

class CitySearch(object):
    """Implements a search for all rental listings by zip code.

    Attributes:
        base: base URL for the search
        city: used to complete the base URL
        logger: self explanatory
        proxy: proxy IP set by env var HTTP_PROXY
        sleeplong: time to wait between subsequent successful requests
        sleepshort: time to wait after failed request
        ua: UserAgent object to generate random user agents
        zipcode: zip code for this search
    """
    def __init__(self, city, zipcode):
        """Init ZipCodeSearch object with city, zipcode, and mongoclient.

        base is set to value of BASE_URL environment variable
        proxy is set to value of HTTP_PROXY environment variable
        logger is retrieved from get_configured_logger function
        """
        self.base = os.environ['BASE_URL']
        self.city = city.lower()
        self.logger = get_configured_logger(__name__)
        self.proxy = os.environ['PROXY']
        self.sleeplong = 2
        self.sleepshort = 0.5
        self.ua = UserAgent()
        self.zipcode = zipcode

        self.logger.info(
            'ZipCodeSearch initialized for zip code {}'.format(
                self.zipcode
            )
        )

    def execute(self):
        """Executes a zip code search for rental properties."""
        content = self._search()
        count = self._count_results(content)
        self.logger.info(
            'Found {} results for this zip code'.format(count)
        )

        if int(count) > 0:
            listings = self._parse_results(content)
            self._write_listings_to_datastore(listings)

        for s in range(120, int(count), 120):
            #time.sleep(self.sleepshort)
            content = self._search(str(s))
            listings = self._parse_results(content, str(s))
            self._write_listings_to_datastore(listings)

    def _count_results(self, content):
        """Return number of results found in content.

        Arguments:
            content: str containing the contents of a search query response

        Returns:
            int: count of listings found in search
        """
        soup = BeautifulSoup(content, 'html.parser')

        count = 0
        if soup.select('.totalcount'):
            count = soup.select('.totalcount')[0].text
        return count

    def _is_dup(self, listing):
        """Check database for prior existence of listing.

        Arguments:
            listing: dict representing one listing record

        Returns:
            bool: True if listing exists in db, else False
        """
        # TODO: Figure out how to do  this with Datastore
        scraper_db = self.mongoclient.scraper
        query = {
            "clid": listing['clid'],
            "title": listing['title']
        }
        # self.logger.debug('Checking for duplicates')
        listing_collection = scraper_db.listing

        count = listing_collection.find(query, no_cursor_timeout=True).count()
        # self.logger.debug('Found {} existing records like this'.format(count))

        return count > 0

    def _parse_results(self, content, s='0'):
        """Parse results of a search for link and title.

        Arguments:
            content: str containing the contents of a search query response
            s: str, the current 'page' of serch results, defaults to '0'

        Returns:
            list of dicts representing parsed listings
        """
        listings = []
        soup = BeautifulSoup(content, 'html.parser')
        result_titles = soup.select('.result-title.hdrlnk')
        for title in result_titles:
            listing = {
                'clid': title.attrs['data-id'],
                'content_acquired': False,
                'imgs_acquired': False,
                'link': title.attrs['href'],
                's': s,
                'time_added': datetime.datetime.utcnow(),
                'time_observed': datetime.datetime.utcnow(),
                'title': title.text,
                'zipcode': self.zipcode
            }
            listings.append(listing)
        self.logger.info('Parsed {} listings'.format(len(listings)))
        return listings

    def _search(self, s=None):
        """Get a page of search results.

        Includes re-try logic in case of bad proxy.

        Arguments:
            s: str, the search result index to start at, defaults to None

        Returns:
            str: content of the HTTP response
        """
        url = self.base.format(self.city)
        headers = {'User-Agent': self.ua.random}
        params = {'postal': self.zipcode, 'availabilityMode': '0'}
        proxies = {'http': self.proxy, 'https': self.proxy}

        if s:
            params['s'] = s

        while True:
            try:
                resp = requests.get(
                        url,
                        headers=headers,
                        params=params,
                        proxies=proxies
                       )
                if resp.status_code != 200:
                    raise Exception(
                            'Response contained invalid '
                            'status code {}'.format(resp.status_code)
                          )
                break
            except Exception as e:
                self.logger.info('Exception occurred during request.')
                self.logger.info('{}'.format(e))
                self.logger.info(
                    'Sleeping for {} seconds'.format(self.sleeplong)
                )
                time.sleep(self.sleeplong)
                self.logger.info('Retrying')
        return resp.content

    def _write_listings_to_datastore(self, listings):
        """Write a list of listing dicts to Datastore.

        Data is written to the 'ObservedListing' kind.

        Arguments:
            listings: list of dicts containing listings
        """
        ds_client = datastore.Client()
        kind = "ObservedListing"

        new_count = 0
        for listing in listings:
            if self._is_dup(listing):
                # TODO: Update the listing's "time_observed" field to now
                pass
            else:
                name = listing["clid"]
                key = ds_client.key(kind, name)

                # TODO: Is there a way to pass a dict of params to datastore client instead of individually writing each one?
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
                new_count += 1

        self.logger.info("Wrote {} new listings to Datastore".format(new_count))


def get_search_results(city, zipcode):
    citysearch = CitySearch(city, zipcode)
    return citysearch.execute()
