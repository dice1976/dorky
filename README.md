# Documentation is a WIP.

![Dorky Logo](mgmt_ui/static/dork_logo.png?raw=true)

Dorky is an automated search engine scraper that collects results into a mongo database for later use.

Dorky currently supports:
* Google
* Google Custom Search
* Bing
* Shodan

# Quickstart

Create a virtualenv and install the modules from `requirements.txt`
```
$ virtualenv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```
Next, you need to start a `mongod` instance and update the `[mongo]` section in `dorking.cfg`, while doing it that it's probably 
a good idea to enable the search engines you're interested in as well as adding the appropriate API keys / proxies.

In order to fire up the management UI run
```
$ python manage_dorks.py
```
which will start a webserver running on http://localhost:5000 from where you can add dorks and view results.

Once you have added a dork you can start the actual quering process
```
$ python main.py
```
and results should start populating.

For testing it might be a good idea to run `main.py` with the `--once` flag.
