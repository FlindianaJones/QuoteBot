import os
import requests

from .exceptions import SlackError, SlackNo

class SlackObject:
    """The base object for all Slack Objects"""

    _LIST_OBJECTS = dict()

    def __init__(self, identifiant, token=None):
        """initialize a way to identify each instance"""
        self.identifiant = identifiant
        self._LIST_OBJECTS[identifiant] = self
        if isinstance(token, SlackAPI):
            self.api = token
        elif isinstance(token, str):
            self.api = SlackAPI.get_object(token)
        else:
            self.api = None

    @classmethod
    def get_object(cls, identifiant, token=None):
        """Return an instance of a class based on its identifiant"""
        if identifiant in cls._LIST_OBJECTS:
            return cls._LIST_OBJECTS[identifiant]
        else:
            return cls(token, identifiant)

class SlackAPI(SlackObject):
    """Main class for manipulation of the API

    Stands as a wrapper for a single token"""

    BASE_URL = "https://slack.com/api/"

    def __init__(self, token=None, allow_env_token=False):
        """Give you a Wrapper for a token
        
        The token can be either given through parameter "token"
        or be read from the environment (when allow_env_token is True)"""
        super().__init__(token)
        if token != None:
            self.token = token
        elif allow_env_token and "SLACK_TOKEN" in os.environ:
            self.token = os.environ["SLACK_TOKEN"]
        else:
            raise SlackError("No token")
        
        self._current_target = str()
        
        # Defaults caches to None
        for cache_category in (
                "channels",
                "groups",
                "users"):
            setattr(self, "_cache_" + cache_category, None)

    def _make_request(self, method, parameters):
        """Send a request to the SlackAPI"""
        url = self.BASE_URL + method
        parameters['token'] = self.token

        response = requests.post(url, data=parameters)

        result = response.json()
        if not result['ok']:
            raise SlackNo(result['error'], result)

        return result

    def __call__(self, **kwargs):
        """Allow users to call API in the form `api.channels.list()`"""
        target = self._current_target
        self._current_target = str()
        return self._make_request(target, kwargs)

    def __getattr__(self, target_link):
        """Allow to call API in fashion way

        It permits to do `api.channels.list()` to call channels.list method"""
        if len(self._current_target) > 0:
            self._current_target += '.'

        self._current_target += target_link
        return self

    @classmethod
    def _generate_caching_methods(cls, name, api_subpart):
        """Special method generating the caching methods
        
        Deleted after use"""

        function_name = "_caching_" + name

        def caching(self):
            list_channels = self._make_request(name + ".list", dict())
            serialize = lambda obj: (obj['name'], obj['id'])
            mapping = dict(map(serialize, list_channels[api_subpart]))
            setattr(self, "_cache_" + name, mapping) 
        
        caching.__doc__ = "Cache {name} in _cache_{name}".format(name=name)
        caching.__name__ = function_name

        setattr(cls, function_name, caching)
    
    @classmethod
    def _generate_id_methods(cls, category, prefix):
        """Special method generating id methods
        
        Deleted after use"""

        cache_name = "_cache_" + category
        caching_method = getattr(cls, "_caching_" + category)

        def id_method(self, name):
            if getattr(self, cache_name) is None:
                caching_method(self)

            to_search = name.strip(prefix)

            if to_search in getattr(self, cache_name):
                return getattr(self, cache_name)[to_search]

        id_method.__doc__ = "Retrieve {category}'s ID".format(
                category=category[:-1]) # Quick hack to remove the trailing s
        id_method.__name__ = "{category}_id".format(category=category)

        setattr(cls, category + "_id", id_method)

# Generate caching methods
for name, api_subpart in (
        ("channels", "channels"),
        ("groups", "groups"),
        ("users", "members")):
    SlackAPI._generate_caching_methods(name, api_subpart)

del SlackAPI._generate_caching_methods


# Generate IDs methods
for category, prefix in (
        ("channels", "#"),
        ("groups", "#"),
        ("users", "@")):
    SlackAPI._generate_id_methods(category, prefix)

del SlackAPI._generate_id_methods
