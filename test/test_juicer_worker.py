# Copyright (C) 2014 SEE AUTHORS FILE
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Unittests.
"""

import pika
import mock
import sys

from contextlib import nested

from . import TestCase

import logging

logging.disable(logging.CRITICAL)

MQ_CONF = {
    'server': '127.0.0.1',
    'port': 5672,
    'vhost': '/',
    'user': 'guest',
    'password': 'guest',
}
CHANGE_NAME = "CHG1337"
CART_ENV = "qa"


class TestFuncWorker(TestCase):

    def setUp(self):
        """
        Set up some reusable mocks.
        """
        TestCase.setUp(self)
        self.channel = mock.MagicMock('pika.spec.Channel')
        self.channel.basic_consume = mock.Mock('basic_consume')
        self.channel.basic_ack = mock.Mock('basic_ack')
        self.channel.basic_reject = mock.Mock('basic_reject')
        self.channel.basic_publish = mock.Mock('basic_publish')

        self.basic_deliver = mock.MagicMock()
        self.basic_deliver.delivery_tag = 123

        self.properties = mock.MagicMock(
            'pika.spec.BasicProperties',
            correlation_id=123,
            reply_to='me')

        self.logger = mock.MagicMock('logging.Logger').__call__()
        self.app_logger = mock.MagicMock('logging.Logger').__call__()
        self.connection = mock.MagicMock('pika.SelectConnection')

    def tearDown(self):
        """
        After every test.
        """
        TestCase.tearDown(self)
        self._reset_mocks()

    def _reset_mocks(self):
        """
        Force reset mocks.
        """
        self.channel.reset_mock()
        self.channel.basic_consume.reset_mock()
        self.channel.basic_ack.reset_mock()
        self.channel.basic_reject.reset_mock()
        self.channel.basic_publish.reset_mock()

        self.basic_deliver.reset_mock()
        self.properties.reset_mock()

        self.logger.reset_mock()
        self.app_logger.reset_mock()
        self.connection.reset_mock()

    def test_process(self):
        """
        Test were everything is nice, up to calling pull/push
        """
        body = {
            'dynamic': {
                'cart': CHANGE_NAME,
                'environment': CART_ENV
            }
        }

        juicer_mock = mock.Mock()
        modules = {
            # juicer
            'juicer': juicer_mock,
            # juicer.juicer.Juicer/Parser
            'juicer.juicer': mock.Mock(), 'juicer.juicer.Juicer': mock.Mock(), 'juicer.juicer.Parser': mock.Mock(),
            # juicer.utils.Log
            'juicer.utils': mock.Mock(), 'juicer.utils.Log': mock.Mock(),
            # juicer.common.Cart
            'juicer.common': mock.Mock(), 'juicer.common.Cart': mock.Mock()
        }

        # We need to mock out the dependent juicer modules before we
        # can import the code to be tested.
        with mock.patch.dict('sys.modules', modules):
            mock.patch('replugin.juicerworker.reworker.worker.pika')
            # for k in sorted(sys.modules.keys()):
            #     print "%s: %s" % (k, sys.modules[k])
            import replugin.juicerworker
            with mock.patch.object(replugin.juicerworker.JuicerWorker, '_j_pull') as (
                    mock_j_pull):
                with mock.patch.object(replugin.juicerworker.JuicerWorker, '_j_push') as (
                        mock_j_push):
                    with mock.patch('pika.SelectConnection'):
                        jw = replugin.juicerworker.JuicerWorker(MQ_CONF,
                                                                output_dir='/tmp/')

                        jw.process(self.channel, self.basic_deliver,
                                   self.properties, body, self.logger)

                        jw.on_upload('juicer')

                        mock_j_pull.assert_called_once_with(CHANGE_NAME)
                        mock_j_push.assert_called_once_with(CHANGE_NAME, CART_ENV)

        self._reset_mocks()


    def test_process_no_dynamic(self):
        """
        no dynamic data is provided = failboat
        """
        body = {
            'dynamic': { }
        }

        juicer_mock = mock.Mock()
        modules = {
            # juicer
            'juicer': juicer_mock,

            # juicer.juicer.Juicer/Parser
            'juicer.juicer': mock.Mock(),
            'juicer.juicer.Juicer': mock.Mock(),
            'juicer.juicer.Parser': mock.Mock(),

            # juicer.utils.Log
            'juicer.utils': mock.Mock(),
            'juicer.utils.Log': mock.Mock(),

            # juicer.common.Cart
            'juicer.common': mock.Mock(),
            'juicer.common.Cart': mock.Mock()
        }

        with mock.patch.dict('sys.modules', modules):
            import replugin.juicerworker
            with mock.patch.object(replugin.juicerworker.JuicerWorker, '_j_pull') as (
                    mock_j_pull):
                with mock.patch.object(replugin.juicerworker.JuicerWorker, '_j_push') as (
                        mock_j_push):
                    with mock.patch('pika.SelectConnection'):
                        jw = replugin.juicerworker.JuicerWorker(MQ_CONF,
                                                                output_dir='/tmp/')

                        jw.process(self.channel, self.basic_deliver,
                                   self.properties, body, self.logger)

                        assert mock_j_pull.call_count == 0
                        assert mock_j_push.call_count == 0

        self._reset_mocks()


    def test_pull(self):
        """
        Test pulling
        """
        body = {
            'dynamic': {
                'cart': CHANGE_NAME,
                'environment': CART_ENV
            }
        }

        juicer_mock = mock.Mock()
        modules = {
            # juicer
            'juicer': juicer_mock,

            # juicer.juicer.Juicer/Parser
            'juicer.juicer': mock.Mock(),
            'juicer.juicer.Juicer': mock.Mock(),
            'juicer.juicer.Parser': mock.Mock(),

            # juicer.utils.Log
            'juicer.utils': mock.Mock(),
            'juicer.utils.Log': mock.Mock(),

            # juicer.common.Cart
            'juicer.common': mock.Mock(),
            'juicer.common.Cart': mock.Mock()
        }

        # We need to mock out the dependent juicer modules before we
        # can import the code to be tested.
        with mock.patch.dict('sys.modules', modules):
            import replugin.juicerworker
            with mock.patch('pika.SelectConnection'):
                jw = replugin.juicerworker.JuicerWorker(MQ_CONF,
                                                        output_dir='/tmp/')
                jw.process(self.channel, self.basic_deliver,
                           self.properties, body, self.logger)

        self._reset_mocks()
