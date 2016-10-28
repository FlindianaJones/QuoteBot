import os
import time
import redis
from slackclient import SlackClient
from random import randint
import re

BASE_CMD = "quote "
LIST_CMD = "all"
USR_CMD = "users"
HELP_CMD = "help"
QUOTE_ADD = "--"

slack_client = SlackClient(os.environ['API_KEY'])
       
        
def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = "Cool story bro."
    r = redis.from_url(os.environ.get("REDIS_URL")
    if QUOTE_ADD in command:
        if re.match('^"[^"]+"\s*\-\-\w+$', command):
            parts = command.split(QUOTE_ADD)
            res = 0
            if len(parts) > 1 and parts[1] and parts[0]:
                res = r.append(parts[1].lower(), parts[0] + ";")#should create if not there
                if res > 0: 
                    response = ""
                else:
                    response = "Failure storing quote"
            else:
                response = ""#this is probably someone using bolo
        else:
            response = ""#this is probably someone using bolo
    if command.startswith(BASE_CMD + HELP_CMD):
        response = "To enter a quote, type it in this form:\n\"I hate mondays\"\
 --Garfield\nNo spaces in the person you attribute the quote to, nothing \
else on the line.\nTo retrieve a random quote for someone, type it \
thusly:\nquote Garfield\nTo get all quotes for someone, type it \
like so:\nquote all Garfield\nTo see who has quotes, ask like this:\n\
quote users"
    if command.startswith(BASE_CMD + LIST_CMD):
        parts = command.split(' ')#get the words
        if len(parts) > 2 and parts[2]:
            response = "Here are " + parts[2].title() + "'s quotes:\n"
            rQuotes = r.get(parts[2].lower())
            if rQuotes and len(rQuotes) > 0:
                pQuotes = rQuotes.decode().split(";")
                for quote in pQuotes:
                    response += quote + "\n"
            else:
                response = "I guess "+parts[2]+" isn't funny, meatbag."
        else:
            response = "Whose quotes, meatbag?"     
    if command.startswith(BASE_CMD + USR_CMD):
        response = "Users with quotes:\n"
        rKeys = r.keys('*')
        if rKeys:
            for key in rKeys:
                response += key.decode().title() + "\n"
            response.strip()
        else:
            response = "Apparently nobody is funny yet, meatbag."
    #The base, get a random quote case.
    if LIST_CMD not in command and QUOTE_ADD not in command \
    and USR_CMD not in command and HELP_CMD not in command:
        parts = command.split(' ')#get the words
        if len(parts) > 1 and parts[1]:
            rQuotes = r.get(parts[1].lower())
            if rQuotes and len(rQuotes) > 0:
                pQuotes = rQuotes.decode().split(";")
                index = randint(0, len(pQuotes)-2) if len(pQuotes) > 1  else 0
                response = parts[1].title() +": " + pQuotes[index] 
            else:
                response = "I guess "+parts[1]+" isn't funny, meatbag."
        else:
            response = "Whose quote, meatbag?"
    if response:
        slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)
    
def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Message API is an events firehose.
        This parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output:
                if output['text'].startswith(BASE_CMD) \
                or QUOTE_ADD in output['text']:
                    #return text after the mention, no whitespace
                    return output['text'], output['channel']
    return None, None

if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 #apparently a firehose reading gap
    if slack_client.rtm_connect():
        print("Quotebot connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
