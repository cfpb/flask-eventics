# flask-eventics

This is a [Flask Blueprint](http://flask.pocoo.org/docs/0.10/blueprints/) for generating [iCalendar files](https://www.ietf.org/rfc/rfc2445.txt) from JSON returned by a REST API Endpoint.

**Status:** Proof-of-concept.

## Requirements

Requirements can be satisfied with `pip`:

```shell
$ pip install -r requirements.txt
```

* [Flask](http://flask.pocoo.org/)
* [Python icalendar](http://icalendar.readthedocs.org/en/latest/) 
* [Python Dateutil](https://dateutil.readthedocs.org/en/latest/)
* [Python mock (for the tests)](http://www.voidspace.org.uk/python/mock/)

## Installation

To clone and install flask-eventics locally in an existing Python 
[`virtualenv`](https://virtualenv.pypa.io/en/latest/):

```shell
$ git clone https://github.com/cfpb/flask-eventics
$ pip install -e flask-eventics
```

Note: this installs flask-eventics in 'editable' mode.

flask-eventics can be installed directly from Github:

```shell
$ pip install git+https://github.com/cfpb/flask-eventics
```

Once installed, the flask-eventics blueprint simply needs to be
registered with your flask application:

```python
from flask import Flask
from flask_eventics import eventics

app = Flask(__name__)
app.register_blueprint(eventics)
```

If using [Sheer](https://github.com/cfpb/sheer), flask-eventics can be
added to your site's `_settings/blueprints.json` file.

```json
{
  "flask_eventics": {
    "package": "flask_eventics.controllers",
    "module":  "eventics"
  }
}
```

## Configuration

flask-eventics can optionally use the Flask app configuration or
environment variables for configuration. 

#### `EVENT_ICS_URL` 
The URL at which ICS files will be available. It should include a named 
argument, `event_slug`, which will corropsond to an event available 
from a source url.

Example: `/events/<event_slug>/ics`

#### `EVENT_SOURCE` 
The REST URL at which JSON that describes a particular event is available. 
This was designed to work with Elasticsearch, but it should work with any 
REST API that provides all the necessary properties within a single 
JSON object.

Example: `http://localhost:9200/content/event/<event_slug>/_source`

#### `EVENT_CALENDAR_PRODID` 
The iCalendar product identifier that will be returned for generated 
calendars.

#### JSON-iCalendar Field Mapping

There is a series of configuration options that map iCalendar fields to
properties on the JSON object returned by the event source. 

* `EVENT_FIELD_SUMMARY`: `summary`
* `EVENT_FIELD_DTSTART`: `dtstart`
* `EVENT_FIELD_DTEND`: `dtend`
* `EVENT_FIELD_DTSTAMP`: `dtstamp`
* `EVENT_FIELD_UID`: `uid`
* `EVENT_FIELD_PRIORITY`: `priority`
* `EVENT_FIELD_ORGANIZER`: `organizer`
* `EVENT_FIELD_ORGANIZER_ADDR`: `organizer_email`
* `EVENT_FIELD_LOCATION`: `location`
* `EVENT_FIELD_STATUS`: `status`

#### Field Defaults

The following configuration options define defaults that will be used 
if the above fields are not available in the JSON object returned by 
the event source, 

* `EVENT_DEFAULT_SUMMARY`: `''`,
* `EVENT_DEFAULT_DTSTART`: `2015-01-11T10:30:00Z`,
* `EVENT_DEFAULT_DTEND`: `2015-01-11T10:30:00Z`,
* `EVENT_DEFAULT_DTSTAMP`: `2015-01-11T10:30:00Z`,
* `EVENT_DEFAULT_UID`: `''`,
* `EVENT_DEFAULT_PRIORITY`: `1`,
* `EVENT_DEFAULT_ORGANIZER`: `''`,
* `EVENT_DEFAULT_ORGANIZER_ADDR`: `''`,
* `EVENT_DEFAULT_LOCATION`: `''`,
* `EVENT_DEFAULT_STATUS`: `TENTATIVE`,

## Event Sources

An Event Source is a simply a REST API endpoint that returns a JSON
object that describes an event. This could be a custom API or a 
service such as [Elasticsearch](http://www.elasticsearch.org/). With the
default JSON-iCalendar field mappings above the JSON object returned
from the REST endpoint might look like this:

```json
{
    "dtstamp": "2015-01-11T09:29:08Z", 
    "uid": "F964B38DB71F484FA2ABC57F621CB7F1@2015-01-11 09:30:00", 
    "dtend": "2015-01-11T10:30:00Z", 
    "created": "2015-01-11T10:09:42Z", 
    "summary": "A Test Meeting", 
    "location": "Washington, DC", 
    "dtstart": "2015-01-11T09:30:00Z", 
    "id": 24407, 
    "day": "2015-01-11", 
    "description": ""
}
```

This would result in the following iCalendar file being generated:

```
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//A Calendar//somewhere.com//
METHOD:publish
BEGIN:VEVENT
SUMMARY:A Test Meeting
DTSTART;VALUE=DATE-TIME:20150111T093000Z
DTEND;VALUE=DATE-TIME:20150111T103000Z
DTSTAMP;VALUE=DATE-TIME:20150111T142908Z
UID:F964B38DB71F484FA2ABC57F621CB7F1@2015-01-11 09:30:00
LOCATION:Washington\, DC. 
ORGANIZER;CN=:MAILTO:
STATUS:TENTATIVE
END:VEVENT
END:VCALENDAR
```

## Licensing 

Public Domain/CC0 1.0

1. [Terms](TERMS.md)
2. [License](LICENSE)
3. [CFPB Source Code Policy](https://github.com/cfpb/source-code-policy/)


