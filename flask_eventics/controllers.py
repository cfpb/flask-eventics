# -*- coding: utf-8 -*-

from werkzeug.routing import Rule, Map
from flask import Blueprint, request, Response, current_app

import os
from datetime import datetime
import pytz
import icalendar

from urlparse import urlparse, urlunparse
import requests

eventics = Blueprint("flask-eventics", __name__, url_prefix="")

# Configuration Variables
# Other Flask-related projects at CFPB use environment variables rather than
# Flask configuration files. flask-eventics will provide the option for both,
# falling back on envvars if no configuration variables exist.
# Note: Flask doesn't make it easy for Blueprints to get access to app
# configuration. We have to capture that from the app state when the Blueprint
# is registered with the application.
EVENTICS_CONFIG = {
    'EVENT_CALENDAR_PRODID': '-//A Calendar//somewhere.com//',

    # The URL pattern for ics files
    # MUST contain <event_slug> that corrosponds to the source lookup below
    'EVENT_ICS_URL': '/events/<event_slug>/ics',

    # A REST endpoint for events
    # Example: an elasticsearch endpoint
    'EVENT_SOURCE': 'http://localhost:9200/content/calendar_event/<event_slug>/_source',

    # Field mapping from source JSON above to iCalendar
    'EVENT_FIELDS': {
        'summary': '',
        'dtstart': '',
        'dtend': '',
        'dtstamp': '',
        'uid': '',
        'priority': '',
        'organizer': '',
        'location': '',
    },

}


def get_event_json(event_slug):
    """
    Fetch the event json from the configured event source
    (EVENTICS_CONFIG['EVENT_SOURCE']).

    Returns the JSON and a status code
    """
    # First, construct the url from EVENT_SOURCE, which uses Werkzeug URL
    # placeholders the same as our Flask url. This means constructing a simple
    # URL mapping.
    source_url_parts = urlparse(EVENTICS_CONFIG['EVENT_SOURCE'])
    source_map = Map([
        Rule(source_url_parts.path, endpoint="event_source")
    ])
    source_adapter = source_map.bind('')
    source_url_path = source_adapter.build('event_source', {'event_slug': event_slug})
    source_url = urlunparse(source_url_parts._replace(path=source_url_path))
    source_response = requests.get(source_url)

    try:
        return source_response.json(), source_response.status_code
    except ValueError:
        return {}, source_response.status_code


def generate_ics(event_slug):
    """
    Return an ics file for a given event.
    """

    event_json, source_status = get_event_json(event_slug)

    # Create the Calendar
    calendar= icalendar.Calendar()
    calendar.add('prodid', EVENTICS_CONFIG['CALENDAR_PRODID'])
    calendar.add('version', '2.0')
    caledar.add('method', 'publish')

    # ...
    # XXX: Get the event and add it?
    # Create the event
    # event = icalendar.Event()
    # event.add('summary', '...')
    # event.add('dtstart', datetime(..., tzinfo=pytz.utc))
    # event.add('dtend', datetime(..., tzinfo=pytz.utc))
    # event.add('dtstamp', datetime(..., tzinfo=pytz.utc))
    # event.add('last-modified', datetime(..., tzinfo=pytz.utc))
    # event.add('uid', '...')
    # event.add('location', icalendar.vText('...'))

    # TENTATIVE/CONFIRMED/CANCELLED
    # event.add('status', 'tentative')

    # Create any persons associated with the event
    # organizer = icalendar.vCalAddress('MAILTO:...')
    # organizer.params['cn'] = icalendar.vText('...')
    # event.add('organizer', organizer)

    # Add the event to the calendar
    calendar.add_component(event)

    # Return the ICS formatted calendar
    # return calendar.to_ical(), 200, {'Content-Type': 'text/calendar; charset=utf-8'}
    return calendar.to_ical(), source_status, {'Content-Type': 'text/plain; charset=utf-8'}


def record_state(state):
    """
    Record the application state when this blueprint is registered.
    Here we exact appropriate configuration values from the application
    config, if they're available, and use environment variables or
    defaults if not.
    """
    global EVENTICS_CONFIG
    app = state.app

    # For each of these values get the app config value. If it doesn't exist,
    # get an environment variable. If that doesn't exist, use the default.
    # This is a simple function to do that.
    get_config = lambda k: app.config.get(k, os.environ.get(k, EVENTICS_CONFIG[k]))

    EVENTICS_CONFIG['EVENT_CALENDAR_PRODID'] = get_config('EVENT_CALENDAR_PRODID')
    EVENTICS_CONFIG['EVENT_ICS_URL'] = get_config('EVENT_ICS_URL')
    EVENTICS_CONFIG['EVENT_SOURCE'] = get_config('EVENT_SOURCE')

    # Set the route for generate_ics?

# Weakness in Python decorators is that you can't mport and directly test the
# decorated functions, which is why this (and generate_ics below) are
# undecorated.
eventics.record(record_state)


# eventics.route(EVENT_ICS_URL, methods=['GET'])

