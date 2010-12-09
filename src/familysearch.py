"""
A library to interact with the FamilySearch API

Licensed under the FamilySearch API License Agreement;
see the included LICENSE file for details.

Example usage:

from familysearch import FamilySearch

# Log in immediately
fs = FamilySearch('ClientApp/1.0', 'developer_key', 'username', 'password')

# Log in in a separate step
fs = FamilySearch('ClientApp/1.0', 'developer_key')
fs.login('username', 'password')

# Log in in two steps
fs = FamilySearch('ClientApp/1.0', 'developer_key')
fs.initialize()
fs.authenticate('username', 'password')

# Restore a previous session
fs = FamilySearch('ClientApp/1.0', 'developer_key', session='session_id')

# Use the production system instead of the reference system
fs = FamilySearch('ClientApp/1.0', 'developer_key', base='https://api.familysearch.org')
"""

import urllib
import urllib2
import urlparse

from enunciate import identity

__version__ = '0.1'


class FamilySearch(object):

    """
    A FamilySearch API proxy

    The constructor must be called with a user-agent string and a developer key.
    A username, password, session ID, and base URL are all optional.

    Public methods:

    login -- log into FamilySearch with a username and password
    initialize -- create an unauthenticated session
    authenticate -- authenticate a session with a username and password
    """

    def __init__(self, agent, key, username=None, password=None, session=None, base='http://www.dev.usys.org'):
        """
        Instantiate a FamilySearch proxy object.

        Keyword arguments:
        agent -- User-agent string to use for requests
        key -- FamilySearch developer key (optional if reusing an existing session ID)
        username (optional)
        password (optional)
        session (optional) -- existing session ID to reuse
        base (optional) -- base URL for the API;
                           defaults to 'http://www.dev.usys.org' (the Reference System)
        """
        self.agent = '%s Python-FS-Stack/%s' % (agent, __version__)
        self.key = key
        self.session = session
        self.base = base
        identity_base = base + '/identity/v2/'
        self.login_url = identity_base + 'login'
        self.initialize_url = identity_base + 'initialize'
        self.authenticate_url = identity_base + 'authenticate'
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor)

        if username and password:
            self.login(username, password)

    def login(self, username, password):
        """
        Log into FamilySearch using Basic Authentication.

        Web applications must use OAuth.

        """
        credentials = urllib.urlencode({'username': username, 'password': password, 'key': self.key})
        self.session = identity.parse(self._request(self.login_url, credentials)).session.id
        return self.session

    def initialize(self):
        """
        Initialize a FamilySearch session using Basic Authentication.

        This creates an unauthenticated session and should be followed by an
        authenticate call. Web applications must use OAuth.

        """
        key = urllib.urlencode({'key': self.key})
        self.session = identity.parse(self._request(self.initialize_url, key)).session.id
        return self.session

    def authenticate(self, username, password):
        """
        Authenticate a FamilySearch session using Basic Authentication.

        This should follow an initialize call. Web applications must use OAuth.

        """
        credentials = urllib.urlencode({'username': username, 'password': password})
        self.session = identity.parse(self._request(self.authenticate_url, credentials)).session.id
        return self.session

    def _request(self, url, data=None):
        """
        Make a GET or a POST request to the FamilySearch API.

        Adds the User-Agent header and sets the response format to JSON.
        If the data argument is supplied, makes a POST request.
        Returns a file-like object representing the response.

        """
        url = self._add_json_format(url)
        request = urllib2.Request(url, data)
        request.add_header('User-Agent', self.agent)
        return self.opener.open(request)

    def _add_json_format(self, url):
        """
        Add dataFormat=application/json to the query string of the given URL.
        """
        parts = urlparse.urlsplit(url)
        query_parts = urlparse.parse_qsl(parts[3])
        query_parts.append(('dataFormat', 'application/json'))
        query = urllib.urlencode(query_parts)
        return urlparse.urlunsplit((parts[0], parts[1], parts[2], query, parts[4]))
