#!/usr/bin/env python

'''
Usage:
    scrape --site <site-code> --loc <neighborhood_code>
    scrape --list-codes
'''

import os, sys
import unicodedata
import time
import re
from snap import common
import docopt
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

WORD_TO_INT = {
    'one': 1,
    'two': 2,
    'three': 3,
    'four': 4,
    'five': 5,
    'six': 6,
    'seven': 7,
    'eight': 8,
    'nine': 9,
    'ten': 10
}

BK_NEIGHBORHOOD_CODES = {
    'fgrn': 'Fort Greene',
    'fltb': 'Flatbush',
    'bsty': 'Bed-Stuy',
    'mdwd': 'Midwood',
    'bhts': 'Brooklyn Heights',
    'bwck': 'Bushwick'
}

RE_SITE_CODES = {
    'trulia': 'https://www.trulia.com', # scrape
    'olr': 'https://broker.olr.com',       # scrape
    'zillow': 'https://www.zillow.com', # API
    'streeteasy': 'https://www.streeteasy.com'    
}


def word_to_number(input_word):
    if not input_word:
        return None
    key = input_word.strip().lower()
    return WORD_TO_INT.get(key, None)


def decode_olr_condo_coop_price_size_fields(field_array):
    result = {}
    for field  in field_array:
        if 'Price:' in field: # include the colon to avoid price-change fields, which are weird
            price_string = field.split('|')[0]
            print('### PRICE string: ' + price_string)
            price = price_string.split('$')[1].strip()
            result['price'] = int(price.replace(',', ''))
        if 'SF' in field:
            tokens = field.split('|')
            sq_ftg_string = tokens[2].strip()
            result['square_footage'] = int(sq_ftg_string.split(' ')[1])
        if 'Bedroom' in field or 'Studio' in field:
            tokens = field.split('|')
            result['size_description'] = tokens[1].strip()

        if 'Maintenance' in field:            
            charge_string = field.split('|')[1].strip()            
            charge = charge_string.split('$')[1].strip()
            result['monthly_chg'] = charge

        if 'Size' in field:
            print('### parsing field for SIZE:')
            print(field)
            start_index = field.find(':')
            end_index = field.find('|')
            size_substring = field[start_index:end_index]
            print('### size substring: ' + size_substring)
            num_baths = size_substring.split('/')[-1].strip()
            if '.' in num_baths:
                result['bathrooms'] = float(num_baths)
            else:
                result['bathrooms'] = int(num_baths)
            

    if result.get('size_description') and 'Bed' in result['size_description']:
        bedroom_count = result['size_description'].split(' ')[0]
        result['beds'] = word_to_number(bedroom_count)

    return result


def scrape_olr_condo_listings(soup_parse_tree, html_data):
    data = {
        'street_address': '',
        'neighborhood': '',
        'type': '',
        'tags': [],
        'price': '',
        'monthly_chg': '',
        'beds': None,
        'bathrooms': None,
        'square_footage': None,
        'size_description': '' 

    }
    #print(html_data)

    detail_div = soup_parse_tree.find('div', {'class': 'apt_details_left'})

    # this one contains the address
    addr_span = detail_div.find_all('span', {'class': 'txt_gray'})[0]
    address = addr_span.find_all('a')[0].get_text().strip()
    data['street_address'] = unicodedata.normalize('NFKD', address)

    # these spans contain the other feataures of the listing
    feature_spans = detail_div.find_all('span', {'class': 'txt_black_normal'})
    raw_neighborhood_string = unicodedata.normalize('NFKD', feature_spans[0].get_text().strip())

    print('### Raw neighborhood string: %s' % raw_neighborhood_string)

    tokens = [t.strip() for t in raw_neighborhood_string.split('\n')]
    print(tokens)
    data['neighborhood'] = tokens[0]
    data['tags'].extend([t.strip() for t in tokens[1].split('|')])

    raw_pricing_string = unicodedata.normalize('NFKD', feature_spans[1].get_text().strip())

    print('### Raw pricing string: %s' % raw_pricing_string)

    price_size_fields = [token.strip() for token in raw_pricing_string.split('\n')]
    print(price_size_fields)
    data.update(decode_olr_condo_coop_price_size_fields(price_size_fields))

    '''
    price_fields = [token.strip() for token in price_size_fields[0].split('|')]
    data['price'] = price_fields[0].split('$')[0]
    # skip over the price drop field for now
    size_fields = [token.strip() for token in price_size_fields[2].split('|')]
    data['size_description'] = size_fields[1]
    data['square_footage'] = size_fields[2]
    '''

    print(common.jsonpretty(data))

    '''
    for span in soup_parse_tree.find_all('span'):
        spanid = span.get('id')
        print(spanid)
        if spanid:
            continue
        # first span contains address
    '''
        

def scrape_olr(neighborhood_code, webdriver):
    username = 'jrich@spiregroupny.com'
    password = 'FrGt20'  # TODO: !!! REMOVE THIS -- SECURITY HAZARD !!!

    username_input = webdriver.find_element_by_id('ctl00_ContentPlaceHolder1_txtUserName')
    password_input = webdriver.find_element_by_id('ctl00_ContentPlaceHolder1_txtPassword')

    username_input.send_keys(username)
    time.sleep(1)
    password_input.send_keys(password)

    login_button = webdriver.find_element_by_id('ctl00_ContentPlaceHolder1_Loginexceed')
    time.sleep(1)
    login_button.click()
    time.sleep(1)

    customer_link = webdriver.find_element_by_xpath("//a[@data-label='View Customers']")
    webdriver.execute_script("arguments[0].click();", customer_link)
    time.sleep(2)

    customer_grid = webdriver.find_element_by_xpath("//table[@id='ctl00_ctl00_MyCustContent_MyCustContent_gvParentAjax']")
    jr_tblentry = customer_grid.find_element_by_xpath("//tr[@id='tr_788817']")
    target_div = jr_tblentry.find_element_by_xpath("//div[@id='divDetail_788817']")

    # click on expand button
    expand_btn = customer_grid.find_element_by_xpath("//input[@id='imgExpColl_788817']")
    webdriver.execute_script("arguments[0].click();", expand_btn)
    time.sleep(1)

    #nested_tables = target_div.find_elements_by_tag_name('table')
    
    #print(dir(nested_tables))
    #print('### %d nested tables found in target div.' % len(nested_tables))
    #print('### found target table.')
    search_link_condos = target_div.find_element_by_xpath("//a[@href='MyCustomerImageHndlr.aspx?Type=Runsearch&SearchID=956274&RunSearchType=AdvancedSale&cid=788817&From=View']")
    webdriver.execute_script("arguments[0].click();", search_link_condos)

    time.sleep(1)
    top_div = webdriver.find_element_by_xpath("//div[@class='container_1130 search-ui']")
    detail_areas = top_div.find_elements_by_xpath("//div[@class='apt_details_area clearfix']")

    print('### %s listings found.' % len(detail_areas))
    for da in detail_areas:
        #apt_detail = da.find_element_by_xpath("//div[@class='apt_details_left']")
        markup = da.get_attribute('innerHTML')
        soup_parser = BeautifulSoup(markup, 'html.parser')        
        scrape_olr_condo_listings(soup_parser, markup)

        #print(markup)
        print('#################################################')


def search_trulia(neighborhood_code, webdriver):
    all_buttons = webdriver.find_elements_by_tag_name('button')    
    buy_button = None
    rent_button = None
    sold_button = None
    for b in all_buttons:
        if b.text == 'Buy':
            buy_button = b
        if b.text == 'Rent':
            rent_button = b
        if b.text == 'Sold':
            sold_button = b

    buy_button.click()

    input_search_vectors = [
        "webdriver.find_element_by_id('homepageSearchBoxTextInput')",
        "webdriver.find_element_by_xpath(\"//input[@type='text'][@data-testid='location-search-input']\")"
    ]

    search_input = None
    for isv in input_search_vectors:
        try:
            search_input = eval(isv)    
            if search_input:
                break
        except Exception as err:
            print('### Received %s finding search input element.' % err.__class__.__name__)
            #print(err)
            print('### Retrying...')

    if not search_input:
        print('Could not find search-input element in page.')
        return

    search_input.send_keys('%s, Brooklyn, NY' % BK_NEIGHBORHOOD_CODES[neighborhood_code])

    BUTTON_SEARCH_VECTORS = [
        "webdriver.find_element_by_css_selector('button.addon.btn.btnDefault.homepageSearchButton')",
        "webdriver.find_element_by_xpath(\"//div[@data-testid='location-search-button'][@class='LocationAutosuggestInput__RightIcon-sc-789ttj-3 jtFvQn']\")",
        "webdriver.find_element_by_xpath(\"//button[@data-auto-test-id='searchButton']\")"
    ]

    search_button = None

    for bsv in BUTTON_SEARCH_VECTORS:
        try:
            search_button = eval(bsv)
            if search_button:
                break
        except Exception as err:
            print('### Received %s finding search button.' % err.__class__.__name__)
            #print(err)
            print('### Retrying...')

    if not search_button:
        print('Could not find search button element.')
        return

    search_button.click()
    

def main(args):
    if args['--list-codes']:
        print('Supported site codes:')
        print(common.jsonpretty(RE_SITE_CODES))
        print('\n')
        print('Supported neighborhood codes:')
        print(common.jsonpretty(BK_NEIGHBORHOOD_CODES))
        return

    site_code = args['<site-code>']
    if not RE_SITE_CODES.get(site_code):
        print('unrecognized site code "%s".' % site_code)
        print('valid codes:')
        print(common.jsonpretty(RE_SITE_CODES))
        return

    neighborhood_code = args['<neighborhood_code>']
    if not BK_NEIGHBORHOOD_CODES.get(neighborhood_code):
        print('unrecognized neighborhood code "%s".' % neighborhood_code)
        print('valid codes:')
        print(common.jsonpretty(BK_NEIGHBORHOOD_CODES))
        return

    url = RE_SITE_CODES[site_code]

    # create a new Firefox session
    #options = webdriver.FirefoxOptions()
    #options.add_argument('-headless')
    driver = webdriver.Firefox()
    driver.implicitly_wait(30)
    driver.get(url)    
    #
    
    print('### Issuing search against %s for neighborhood %s...' % (url, BK_NEIGHBORHOOD_CODES[neighborhood_code]))

    if site_code == 'trulia':
        search_trulia(neighborhood_code, driver)
    elif site_code == 'olr':
        scrape_olr(neighborhood_code, driver)

    #soup_toplevel = BeautifulSoup(driver.page_source, 'html.parser')
    #driver.quit()


if __name__ == '__main__':
    args = docopt.docopt(__doc__)
    main(args)
