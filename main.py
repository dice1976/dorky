import argparse
import time
import logging
import ConfigParser

import search_engines
from dorks import DorkDB

logging.basicConfig()
log = logging.getLogger('dorking')
log.setLevel(logging.DEBUG)

parser = argparse.ArgumentParser(description='Automated dorking')
parser.add_argument('--once', action="store_true", help='Run queries once.')
args = parser.parse_args()

cfg = ConfigParser.ConfigParser()
cfg.read('dorking.cfg')

filter_terms = cfg.get('filter', 'block_strings').split('\n')
filter_terms = filter(None, filter_terms)
filter_urls = cfg.get('filter', 'block_urls').split('\n')
filter_urls = filter(None, filter_urls)


def ok_result(query, res):
    """Check if a search result is OK or if it should be filtered."""
    # We check against all fields.
    check_text = ' '.join(str(res.values())).lower()
    if query in check_text:
        return False
    if any([ft in check_text for ft in filter_terms]):
        return False
    if any([url in res['engine_id'] for url in filter_urls]):
        return False
    return True

search_engines = {
    'bing': {
        'enabled': cfg.getboolean('bing', 'enabled'),
        'search': search_engines.bing_search
    },
    'google': {
        'enabled': cfg.getboolean('google', 'enabled'),
        'search': search_engines.google_search
    },
    'google_customsearch': {
        'enabled': cfg.getboolean('google_customsearch', 'enabled'),
        'search': search_engines.google_customsearch_search
    },
    'shodan': {
        'enabled': cfg.getboolean('shodan', 'enabled'),
        'search': search_engines.shodan_search
    }
}

storage = DorkDB(cfg)
while True:
    for i, dork in enumerate(storage.get_dorks()):
        if dork['disabled']:
            continue

        engine_name = dork['search_engine']
        engine_details = search_engines[engine_name]

        if not engine_details['enabled']:
            continue

        query = dork['query']
        log.debug("Running: {0} ({1})".format(query, engine_name))
        search_res = engine_details['search'](cfg, query)
        for res in search_res:
            if ok_result(dork['query'], res):
                storage.add_result(dork['_id'], res['engine_id'], res['result'])

    if args.once:
        break

    # Once per 12 hours suffices in most cases.
    time.sleep(12*60*60)