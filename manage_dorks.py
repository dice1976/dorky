
import ConfigParser
import os
import json
import urlparse
import traceback

from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.wsgi import SharedDataMiddleware
from werkzeug.utils import redirect
from bson import json_util

from jinja2 import Environment, FileSystemLoader

from dorks import DorkDB


class Dorky(object):
    def __init__(self):
        template_path = os.path.join(os.path.dirname(__file__), 'mgmt_ui', 'templates')
        self.jinja_env = Environment(loader=FileSystemLoader(template_path),
                                     autoescape=True)

        get_hostname = lambda url: urlparse.urlparse(url).netloc
        self.jinja_env.filters['hostname'] = get_hostname

        self.url_map = Map([
            Rule('/', endpoint='main'),
            Rule('/disable', endpoint='disable'),
            Rule('/get', endpoint='get'),
            Rule('/update', endpoint='update'),
            Rule('/delete', endpoint='delete'),
            Rule('/edit_blacklist', endpoint='edit_blacklist')
        ])
        cfg = ConfigParser.ConfigParser()
        cfg.read('dorking.cfg')

        self.storage = DorkDB(cfg)

    def on_main(self, request):
        return self.render_template('main.html')

    def on_disable(self, request):
        """ Disable/enable dorks.
        """
        dbid = request.form['dbid']
        disabled = True if request.form['status'] == 'true' else False
        print dbid, disabled
        try:
            self.storage.set_dork_disabled(dbid, disabled)
        except Exception as exc:
            return Response(str(exc), status=500)
        return Response('OK')

    def on_update(self, request):
        """ Editing/creating dorks.
        """
        dork = request.form
        print dork
        old_dork = '_id' in dork
        if old_dork:
            did = dork['_id']
            try:
                new_dork = {}
                for k, v in dict(dork).items():
                    new_dork[k] = v[0]
                del new_dork['_id']
                self.storage.update_dork(did, new_dork)
            except Exception as exc:
                print traceback.format_exc()
                return Response(str(exc), status=500)
        else:
            try:
                self.storage.add_dork(dork['query'],
                  category=dork['category'],
                  description=dork['description'],
                  source=dork['source'],
                  search_engine=dork['search_engine'])
            except Exception as exc:
                print traceback.format_exc()
                return Response(str(exc), status=500)
        return Response('OK')

    def on_get(self, request):
        """ Various getters.
        """
        what = request.form['what']
        resp = {}
        if what == 'results':
            dbid = request.form['dbid']
            resp['results'] = list(self.storage.get_results(dbid))
        elif what == 'dorks':
            dorks = list(self.storage.get_dorks())
            resp['categories'] = list(set([d['category'] for d in dorks]))
            resp['dorks'] = dorks
        elif what == 'blacklist':
            resp['blacklist'] = {'url': [], 'text': []}
            for bl in self.storage.get_blacklist():
                resp['blacklist'][bl['type']].append(bl['term'])
        else:
            resp['error'] = 'Unknown'
        return Response(json.dumps(resp, default=json_util.default), mimetype='application/json')

    def on_delete(self, request):
        """ Delete a dork and all its results.
        """
        dbid = request.form['dbid']
        self.storage.delete_dork(dbid)
        return Response("OK")

    def on_edit_blacklist(self, request):
        updates = json.loads(request.form['updates'])
        for item in updates['add']:
            self.storage.add_blacklist(item['term'], item['type'])
        for item in updates['remove']:
            self.storage.remove_blacklist(item['term'], item['type'])
        return Response("OK")

    def error_404(self):
        response = self.render_template('404.html')
        response.status_code = 404
        return response

    def render_template(self, template_name, **context):
        t = self.jinja_env.get_template(template_name)
        return Response(t.render(context), mimetype='text/html')

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return getattr(self, 'on_' + endpoint)(request, **values)
        except NotFound:
            return self.error_404()
        except HTTPException as exc:
            return exc

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


def create_app(with_static=True):
    app = Dorky()
    if with_static:
        app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
            '/static':  os.path.join(os.path.dirname(__file__), 'mgmt_ui', 'static')
        })
    return app

if __name__ == '__main__':
    from werkzeug.serving import run_simple
    app = create_app()
    run_simple('127.0.0.1', 5000, app, use_debugger=True, use_reloader=True)