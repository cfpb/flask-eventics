# -*- coding: utf-8 -*-

from werkzeug.routing import Rule, Map
from flask import Blueprint, request, Response, current_app

import os
from datetime import datetime
import dateutil.parser
import icalendar
from pytz import timezone

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
    # The URL pattern for ics files
    # MUST contain <event_slug> that corrosponds to the source lookup below
    'EVENT_ICS_URL': '/events/<event_slug>/ics',

    # A REST endpoint for events
    # Example: an elasticsearch endpoint
    'EVENT_SOURCE': 'http://localhost:9200/content/events/<event_slug>/_source',

    # Calendar product id
    'EVENT_CALENDAR_PRODID': '-//CFPB//Event Calendar//EN',

    # Field mapping for iCalendar fields from JSON object properties
    'EVENT_FIELD_SUMMARY': 'summary',
    'EVENT_FIELD_DTSTART': 'dtstart',
    'EVENT_FIELD_DTEND': 'dtend',
    'EVENT_FIELD_DTSTAMP': 'dtstamp',
    'EVENT_FIELD_UID': 'uid',
    'EVENT_FIELD_PRIORITY': 'priority',
    'EVENT_FIELD_ORGANIZER': 'organizer',
    'EVENT_FIELD_ORGANIZER_ADDR': 'organizer_email',
    'EVENT_FIELD_LOCATION': 'location',
    'EVENT_FIELD_STATUS': 'status',

    # Status is one of:
    # TENTATIVE/CONFIRMED/CANCELLED

    # Defaults
    'EVENT_DEFAULT_SUMMARY': '',
    'EVENT_DEFAULT_DTSTART': '2015-01-11T10:30:00Z',
    'EVENT_DEFAULT_DTEND': '2015-01-11T10:30:00Z',
    'EVENT_DEFAULT_DTSTAMP': '2015-01-11T10:30:00Z',
    'EVENT_DEFAULT_UID': '',
    'EVENT_DEFAULT_PRIORITY': 1,
    'EVENT_DEFAULT_ORGANIZER': '',
    'EVENT_DEFAULT_ORGANIZER_ADDR': '',
    'EVENT_DEFAULT_LOCATION': '',
    'EVENT_DEFAULT_STATUS': 'TENTATIVE',
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

    # Get the event json from our source
    event_json, source_status = get_event_json(event_slug)
    if source_status != 200:
        return '', source_status

    # Create the Calendar
    calendar = icalendar.Calendar()
    calendar.add('prodid', EVENTICS_CONFIG['EVENT_CALENDAR_PRODID'])
    calendar.add('version', '2.0')
    calendar.add('method', 'publish')

    # Create the event
    event = icalendar.Event()

    # Populate the event
    ics_fields = event_json.get('ics')
    tz_dict = {'dtstart': 'starting_tzinfo', 'dtend': 'ending_tzinfo'}
    for ics_field, timezoneName in tz_dict.items():
        if ics_field in ics_fields:
            esdate = dateutil.parser.parse(ics_fields[ics_field])
            naive = esdate.replace(tzinfo=None)
            if timezoneName in ics_fields:
                date = timezone(ics_fields[timezoneName]).localize(naive)
            else:
                date = esdate.astimezone(timezone('UTC'))
            event.add(ics_field, date)
            del ics_fields[ics_field]
            del ics_fields[timezoneName]
    for field in ics_fields:
        if field == 'dtstamp':
            esdate = dateutil.parser.parse(ics_fields[field])
            event.add(field, date)
        else:
            event.add(field, ics_fields[field])

    # Add the event to the calendar
    calendar.add_component(event)

    # Return the ICS formatted calendar
    return calendar.to_ical(), source_status, {
        'Content-Type': 'text/calendar; charset=utf-8',
        'Content-Disposition': 'attachment;filename=' + event_slug + '.ics'
    }


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

    for config_key in EVENTICS_CONFIG:
        EVENTICS_CONFIG[config_key] = get_config(config_key)

    # Set the route for generate_ics?
    eventics.route(EVENTICS_CONFIG['EVENT_ICS_URL'], methods=['GET'])(generate_ics)

# Weakness in Python decorators is that you can't mport and directly test the
# decorated functions, which is why this (and generate_ics) are
# undecorated.
eventics.record(record_state)
