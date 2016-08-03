import json
import time
import re
import urllib
import random

from urllib import quote_plus

import requests
import googleapiclient
import shodan
from apiclient.discovery import build
from bs4 import BeautifulSoup

user_agents = []
with open('user-agents.txt') as fd:
    for ua in fd:
        user_agents.append(ua.replace('\n', '').strip())
user_agents = filter(None, user_agents)


def random_proxy(cfg):
    """ Choose a random proxy server.
    :param cfg: Dorking configuration object.
    :return: Proxy setting usable by requests.
    """
    proxy_user = cfg.get('proxy', 'user')
    proxy_pass = cfg.get('proxy', 'password')
    proxy_servers = filter(None, cfg.get('proxy', 'servers').split('\n'))
    proxy_port = cfg.get('proxy', 'port')
    return {
        'https': 'http://{0}:{1}@{2}:{3}/'.format(
                proxy_user,
                proxy_pass,
                random.choice(proxy_servers),
                proxy_port
        )
    }


def random_ua():
    """ Choose a random user agent.
    """
    return random.choice(user_agents)


def bing_search(cfg, query, limit=1000):
    """ Perform a Bing API query.
    :param cfg: Dorking configuration object.
    :param query: Query to execute.
    :param limit: Limit results to a specific count.
    :return: List of search results.
    """
    api_key = cfg.get('bing', 'api_key')

    url = "https://api.datamarket.azure.com/Bing/Search/v1/Web"
    url += "?$format=json&$top={0}&Query=%27{1}%27".format(limit, quote_plus(query))

    try:
        r = requests.get(url, auth=("", api_key))
        resp = json.loads(r.text)
    except Exception as exc:
        import traceback
        print traceback.format_exc()
        exit(1)

    # Convert the json response to the required format.
    return map(lambda res: {
        'engine_id': res['Url'],
        'result': {
            'title': res['Title'],
            'description': res['Description']
        }
    }, resp['d']['results'])


def google_customsearch_search(cfg, query):
    """ Perform a custom search.

    Create an API account with Custom Search enabled, then create a CSE @ https://cse.google.com/cse/manage/all
    First create one with a random URL, then afterwards you can manage it to be "Search entire web but emphasize included sites"

    Inspiration: http://scriptsonscripts.blogspot.se/2015/02/python-google-search-api-requests.html

    :param cfg: Dorking configuration object.
    :param query: Query to execute.
    :return: List of search results.
    """
    search_engine_id = cfg.get('google', 'search_engine_id')
    api_key = cfg.get('google', 'api_key')

    service = build('customsearch', 'v1', developerKey=api_key)
    collection = service.cse()

    results = []
    results_per_page = 10
    for i in range(0, 10):
        # This is the offset from the beginning to start getting the results from
        start_val = 1 + (i * results_per_page)

        request = collection.list(q=query,
            num=results_per_page,
            start=start_val,
            cx=search_engine_id
        )
        try:
            response = request.execute()
        except googleapiclient.errors.HttpError as exc:
            import pdb
            pdb.set_trace()
        for item in response.get('items', []):
            results.append({
                'engine_id': item['link'],
                'result': {
                    'title': item['title'],
                    'description': item['snippet']
                }
            })

        # Page until we have all the results.
        if len(results) == int(response['searchInformation']['totalResults']):
            break

        time.sleep(5)
    return results


def google_search(cfg, query):
    """ Very basic Google Search scraper.

    :param cfg: Dorking configuration object.
    :param query: Query to execute.
    :return: List of search results.
    """
    max_pages = 7
    num_results = 10
    results = []
    base_url = 'https://google.com/search?q='

    my_proxy = random_proxy()
    print "Using proxy: {0}".format(my_proxy)
    my_ua = random_ua()
    print "Using user-agent: {0}".format(my_ua)

    def current_url(query, page):
        url = base_url+urllib.quote(query)
        if page > 0:
            url += "&start=" + str(page * num_results)
        return url

    for c_page in range(max_pages):
        print "Google Search - Page: {0} for {1}".format(c_page, query)
        try:
            resp = requests.get(current_url(query, c_page), headers={'User-Agent': my_ua}, proxies=my_proxy)
            resp.raise_for_status()
        except Exception as exc:
            # If we fail here we need to back off for a bit.
            print exc
            print "Waiting one hour and aborting..."
            time.sleep(60*60)
            return results
        sp = BeautifulSoup(resp.text)

        result_set = sp.select('.g')
        if len(result_set) == 0:
            print "No results remaining."
            break

        for res in sp.select('.g'):
            link_obj = res.select('.r a')
            summ_obj = res.select('.st')
            if len(link_obj) == 0 or len(summ_obj) == 0:
                continue
            summ = summ_obj[0].text
            try:
                link_href = link_obj[0]['href']
            except IndexError as exc:
                print "Skipping object."
                continue
            link_title = link_obj[0].text
            results.append({
                'engine_id': link_href,
                'result': {
                    'title': link_title,
                    'description': summ
                }
            })

        # We always sleep, even if its the last page.
        time.sleep(random.randint(40, 50))
    return results

def change_keys(obj, convert):
    """
    Recursivly goes through the dictionnary obj and replaces keys with the convert function.
    """
    if isinstance(obj, dict):
        new = {}
        for k, v in obj.iteritems():
            new[convert(k)] = change_keys(v, convert)
    elif isinstance(obj, list):
        new = []
        for v in obj:
            new.append(change_keys(v, convert))
    else:
        return obj
    return new

def shodan_search(cfg, query):
    """ Perform a Shodan API query.

    :param cfg: Dorking configuration object.
    :param query: Query to execute.
    :return: List of search results.
    """
    api_key = cfg.get('shodan', 'api_key')
    api = shodan.Shodan(api_key)
    page = 1
    results = []

    while True:
        try:
            search_res = api.search(query, page=page)
        except shodan.APIError as exc:
            print "Shodan error\t{0}".format(str(exc))
            return results

        for match in search_res['matches']:
            # Key of IP and Port.
            engine_id = "shodan:{0[ip_str]}:{0[port]}".format(match)
            # Replace dot notation with double underscores.
            match = change_keys(match, lambda x: x.replace('.', '__'))
            results.append({
                'engine_id': engine_id,
                'result': match
            })
        # Let's pause a little bit in between requests.
        time.sleep(3)
        if len(results) == search_res['total'] or len(search_res['matches']) == 0:
            break
        page += 1
    return results
