# -*- coding: utf-8 -*-
"""
Functional test suite for the root controller.

This is an example of how functional tests can be written for controllers.

As opposed to a unit-test, which test a small unit of functionality,
functional tests exercise the whole application and its WSGI stack.

Please read http://pythonpaste.org/webtest/ for more information.

"""
from nose.tools import assert_true

from saip.tests import TestController


class TestRootController(TestController):
    """Tests for the method in the root controller."""

    def test_environ(self):
        """Displaying the wsgi environ works"""
        response = self.app.get('/environ.html')
        assert_true('The keys in the environment are: ' in response)

    def test_data(self):
        """The data display demo works with HTML"""
        response = self.app.get('/data.html?a=1&b=2')
        expected = """\
<table>
        <tr>
            <td>a</td>
            <td>1</td>
        </tr>
        <tr>
            <td>b</td>
            <td>2</td>
        </tr>
    </table>
"""
        assert expected in response, response

    def test_data_json(self):
        """The data display demo works with JSON"""
        resp = self.app.get('/data.json?a=1&b=2')
        assert '"a": "1", "b": "2"' in resp, resp

    def test_secc_with_anonymous(self):
        """Anonymous users must not access the secure controller"""
        self.app.get('/secc', status=401)
        # It's enough to know that authorization was denied with a 401 status
