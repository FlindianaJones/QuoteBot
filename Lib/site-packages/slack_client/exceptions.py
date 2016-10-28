class SlackError(Exception):
    pass

class SlackNo(SlackError):
    def __init__(self, msg_error):
        self.msg = msg_error

    def __str__(self):
        return repr(self.msg)

class SlackTooManyRequests(SlackError):
    def __init__(self, time_to_wait):
        self.time_to_wait = time_to_wait

    def __str__(self):
        return ("Too many requests. Wait %d seconds before trying again" \
                % (self.time_to_wait))
