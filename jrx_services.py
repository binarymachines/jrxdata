#!/usr/bin/env python

import os, sys
import requests
import json
from snap import common



class StreetEasyAPIService(object):
    def __init__(self, **kwargs):
        pass


class ZillowAPIService(object):
    def __init__(self, **kwargs):
        kwreader = common.KeywordArgReader('api_key')
        kwreader.read(**kwargs)
        self.api_key = kwreader.get_value('api_key')
        self.service_url = 'http://www.zillow.com/webservice/GetDeepSearchResults.htm'


    def lookup_address(self, **kwargs):
        kwreader = common.KeywordArgReader('address', 'city', 'state', 'zip_code')
        kwreader.read(**kwargs)

        address = requests.utils.quote(kwargs['address'])
        city_state_zip = requests.utils.quote('%s %s %s' % (kwargs['city'], kwargs['state'], kwargs['zip_code']))

        parameters = {
            'zws-id': self.api_key,
            'address': address,
            'citystatezip': city_state_zip
        }
        try:
            response = requests.get(self.service_url, params=parameters)
            if response:
                print(response.content)
            else:
                print('!!! Error connecting to Zillow service.')
        except:
            raise
            
