import json
from datetime import datetime

import pymongo
from bson.objectid import ObjectId

class DorkDB(object):
    def __init__(self, config):
        # Parse config.
        host = config.get('mongo', 'host')
        db_name = config.get('mongo', 'database')
        dork_coll = config.get('mongo', 'dork_coll')
        result_coll = config.get('mongo', 'result_coll')

        # Connect.
        self.connection = pymongo.MongoClient(host)
        self.db = self.connection[db_name]
        self.dorks = self.db[dork_coll]
        self.results = self.db[result_coll]

        # Make sure we have the indexes we need.
        self.dorks.create_index('query')
        self.results.create_index('engine_id')
        self.results.create_index('dork')

    def get_dorks(self):
        for dork in self.dorks.find():
            yield dork

    def add_dork(self, query, category='uncategorized', discovery_date=None, description='', source='internal', search_engine='google', disabled=False):
        """Add a new dork to the database.

        :param query: Query string to execute.
        :param category: Category name used for organization.
        :param discovery_date: When the dork was found, can be used for filtering out older dorks.
        :param description: Description of what the results should represent.
        :param source: Where the dork was found, for example GHDB for the Google Hacking DB.
        :param query_format: Which search engine was the query designed for. Examples are 'google', 'bing', 'shodan'
        :param disabled: If the query should be disabled.
        """
        existing = self.dorks.find_one({'query': query})
        if existing:
            raise KeyError('A dork with that query already exist:\n{0}'.format(json.dumps(existing, None, indent=2)))
        
        now = datetime.now()
        if not discovery_date:
            discovery_date = now

        self.dorks.insert({
            'query': query,
            'search_engine': search_engine,
            'category': category, # Should make this into a db id.
            'discovery_date': discovery_date,
            'description': description,
            'source': source,
            'disabled': disabled,
            'date_added': now
        })

    def update_dork(self, dbid, upd_data):
        self.dorks.update({'_id': ObjectId(dbid)}, {'$set': upd_data})

    def set_dork_disabled(self, dbid, disabled):
        self.dorks.update({'_id': ObjectId(dbid)}, {'$set': {'disabled': disabled}})

    def add_result(self, dork_id, engine_id, result):
        now = datetime.now()
        self.results.insert({
            'dork': dork_id,
            'result': result,
            'engine_id': engine_id,
            'date_added': now
        })

    def get_results(self, dork_id=None, added_after=None):
        query = {}
        if dork_id:
            if type(dork_id) != ObjectId:
                dork_id = ObjectId(dork_id)
            query['dork'] = dork_id
        if added_after:
            query['date_added'] = {'$gte': added_after}
        return self.results.find(query)