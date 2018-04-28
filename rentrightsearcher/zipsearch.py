"""rentright.scraper.zipcodesearch"""
import datetime
import hashlib
import os
import requests
import time

from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from google.cloud import datastore

from rentrightsearcher.util.log import get_configured_logger

class ZipSearch(object):
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
    def __init__(self, city, state, zipcode):
        """Init ZipCodeSearch object with city, zipcode, and mongoclient.

        base is set to value of BASE_URL environment variable
        proxy is set to value of HTTP_PROXY environment variable
        logger is retrieved from get_configured_logger function
        """
        self.base = os.environ['BASE_URL']
        self.city_metro = self._get_city_metro(city, state)
        self.logger = get_configured_logger(__name__)
        self.proxy = os.environ.get('PROXY')
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
        content, request_time = self._search()
        count = self._count_results(content)
        self.logger.info(
            'Found {} results for this zip code'.format(count)
        )

        lists_of_listings = []

        # This is only here so we don't search for the first 120 listings twice
        if int(count) > 0:
            lists_of_listings.append(self._parse_results(content, request_time))

        # The count has to run before this loop
        for s in range(120, int(count), 120):
            content, request_time = self._search(str(s))
            lists_of_listings.append(self._parse_results(content, request_time, str(s)))

        # Flattens the list of listings
        listings = [listing for list_of_listings in lists_of_listings for listing in list_of_listings]
        return listings

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

    def _get_city_metro(self, city, state):
        city_state = "{}, {}".format(city.lower(), state.lower())
        ds_client = datastore.Client()
        city_key = ds_client.key("CityMetroMap", city_state)
        city_entity = ds_client.get(city_key)
        return city_entity["metro"]

    def _parse_results(self, content, request_time, s='0'):
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
            unique_string = \
                title.attrs['data-id'] + title.text + self.cl_city
            unique_identifier = hashlib.md5(unique_string.encode('utf-8'))
            listing = {
                'id': unique_identifier,
                'clid': title.attrs['data-id'],
                'content_acquired': False,
                'imgs_acquired': False,
                'link': title.attrs['href'],
                's': s,
                'time_added': datetime.datetime.utcnow(),
                'time_observed': request_time,
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
        url = self.base.format(self.city_metro)
        headers = {'User-Agent': self.ua.random}
        params = {'postal': self.zipcode, 'availabilityMode': '0'}

        if self.proxy:
            proxies = {'http': self.proxy, 'https': self.proxy}

        if s:
            params['s'] = s

        while True:
            try:
                if self.proxy:
                    resp = requests.get(
                            url,
                            headers=headers,
                            params=params,
                            proxies=proxies
                           )
                    request_time = datetime.datetime.utcnow()
                else:
                    resp = requests.get(
                        url,
                        headers=headers,
                        params=params
                    )
                    request_time = datetime.datetime.utcnow()
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
        return resp.content, request_time


def get_search_results(city, zipcode):
    zipsearch = ZipSearch(city, zipcode)
    return zipsearch.execute()
