# -*- coding: utf-8 -*-

import unittest
import mock

import icalendar
import dateutil

from flask import Flask
from flask_eventics.controllers import eventics, record_state, get_event_json, generate_ics, EVENTICS_CONFIG

class EventICSTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_record_state(self):
        """
        Test that the application state is appropriately recorded when
        the blueprint is registered. To do this, we'll mock Flask's
        app.config.get and os.environ.get and make sure they're called
        appropriately.

        We want to test our fail-through, wherein:
            If there is a value in app.config, use it
            Otherwise if there is a value in os.environ, us it
            Otherwise use the default value

        We want to configure Flask blueprints differently, or have the
        option to configure them differently, and not just through
        envvars. This is a first step.
        """

        # This is a mock app, with mock config that is simply a dictionary. We
        # don't need to test dictionary lookups, so we'll mock that later. We
        # just need to test that the lookup happens in the right order, the
        # value comes from the appropriate place, and that it gets appropriately
        # assigned.
        mock_app = mock.MagicMock()
        mock_app.config = {}

        # This is a mock state object which gets passed to record_state.
        mock_state = mock.MagicMock()
        mock_state.app = mock_app

        # Test fail through to default value
        record_state(mock_state)
        self.assertEqual(EVENTICS_CONFIG['EVENT_CALENDAR_PRODID'],
                         '-//A Calendar//somewhere.com//')

        # Test using os.environ value
        with mock.patch.dict('os.environ', {'EVENT_CALENDAR_PRODID':
                '-//Another Calendar//somewhere.com//'}):
            record_state(mock_state)
            self.assertEqual(EVENTICS_CONFIG['EVENT_CALENDAR_PRODID'],
                             '-//Another Calendar//somewhere.com//')

        # Test using the app.config value
        with mock.patch.dict(mock_state.app.config, {'EVENT_CALENDAR_PRODID':
                '-//My Calendar//anywhere.com//'}):
            record_state(mock_state)
            self.assertEqual(EVENTICS_CONFIG['EVENT_CALENDAR_PRODID'],
                             '-//My Calendar//anywhere.com//')

    @mock.patch("requests.get")
    def test_get_event_json(self, mock_request_get):
        """
        Test that we're constructing the event source URL from which to fetch
        JSON correctly.
        """
        # We want two possible responses, first a good, 200 response, and
        # then a 404 response (a response that doesn't provide JSON). We
        # need to make sure we're handling the ValueError (JSONDecodeError).
        mock_good_response = mock.MagicMock()
        mock_good_response.status_code = 200
        mock_good_response.json.return_value = {'some': 'json'}

        mock_bad_response = mock.MagicMock()
        mock_bad_response.status_code = 404
        mock_bad_response.json.side_effect = ValueError()

        mock_request_get.side_effect = [
            mock_good_response,
            mock_bad_response
        ]

        EVENTICS_CONFIG['EVENT_SOURCE'] = 'http://localhost:9200/event/<event_slug>/'

        source_json, source_status = get_event_json('myevent')
        self.assertEqual(source_status, 200)
        mock_request_get.assert_called_with('http://localhost:9200/event/myevent/')

        source_json, source_status = get_event_json('myevent')
        self.assertEqual(source_status, 404)
        self.assertEqual(source_json, {})


    def test_generate_ics(self):
        """
        Test that, given a specific set of JSON, the generate_ics
        function generates valid iCalendar data.
        """
        event_json = {
            "summary": "Test Event",
            "location": "Washington, DC",
            "uid": "8DB71F484FA2ABC57F621CB7F1@2013-07-03 09:30:00",
            "dtstart": "2013-07-03T09:30:00Z",
            "dtend": "2013-07-03T10:30:00Z",
            "dtstamp": "2013-07-02T14:29:08Z"
        }

        with mock.patch('flask_eventics.controllers.get_event_json') as mock_get_event_json:
            mock_get_event_json.return_value = event_json, 200
            ics, status, headers = generate_ics('foo')

            # Make sure the ics parses
            try:
                icalendar.Calendar.from_ical(ics)
            except ValueError:
                self.fail("generate_ics() did not return a valid iCalendar file")


    def test_eventics(self):
        """
        Test that, as eventics registers and responds appropriately as a
        Flask Blueprint.
        """
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.register_blueprint(eventics)

        client = app.test_client()
        response = client.get('/events/foo/ics')



if __name__ == '__main__':
    unittest.main()

