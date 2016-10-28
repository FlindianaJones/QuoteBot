from .api import SlackObject, SlackAPI

class SlackChannel(SlackObject):

    def __init__(self, token, id):
        super().__init__(id, token)

        self.data = self.api.channels.info(channel=id)['channel']

    def __getattr__(self, name):
        return self.data[name]

    @classmethod
    def from_name(cls, token, name):
        if isinstance(token, SlackAPI):
            api = token
        elif isinstance(token, string):
            api = SlackAPI.get_object(token)
        else:
            raise TypeError
        return cls(api, api.channels_id(name))

    def send(self, message, **kwargs):
        params = {
            'channel': self.id,
            'text': message,
            'as_user': True
        }
        params.update(kwargs)
        self.api.chat.postMessage(**params)
