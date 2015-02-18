# -*- coding: utf-8 -*-

import unittest
import mock

from flask import Flask
from flask_eventics.controllers import eventics, record_state, get_event_json, EVENTICS_CONFIG

class EventICSTestCase(unittest.TestCase):

    def setUp(self):
        # Basic Flask setup
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

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
        # This is what we will do when we're able to test something.
        # response = self.client.get('...')
        pass


if __name__ == '__main__':
    unittest.main()

