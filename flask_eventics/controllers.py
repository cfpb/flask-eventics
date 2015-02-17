# -*- coding: utf-8 -*-

from flask import Blueprint, request, Response, current_app

import os
from datetime import datetime
import pytz
import icalendar

eventics = Blueprint("flask-eventics", __name__, url_prefix="")

# Configuration Variables
# Other Flask-related projects at CFPB use environment variables rather than
# Flask configuration files. flask-eventics will provide the option for both,
# falling back on envvars if no configuration variables exist.
# Note: Flask doesn't make it easy for Blueprints to get access to app
# configuration. We have to capture that from the app state when the Blueprint
# is registered with the application.

EVENTICS_CONFIG = {
    'CALENDAR_PRODID': '-//A Calendar//somewhere.com//',
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

    EVENTICS_CONFIG['CALENDAR_PRODID'] = get_config('CALENDAR_PRODID')

# Weakness in Python decorators is that you can't mport and directly test the
# decorated functions, which is why this (and generate_ics below) are
# undecorated.
eventics.record(record_state)

def generate_ics(event_slug):
    """
    Return an ics file for a given event.
    """

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
    return calendar.to_ical(), 200, {'Content-Type': 'text/plain; charset=utf-8'}


