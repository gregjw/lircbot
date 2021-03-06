import unittest
import socket

from mock import patch, MagicMock

from lircbot.lircbot import ircBot


class BotSetupMixin(object):

    FAKE_SERVER = "0.0.0.0"
    FAKE_PORT = 50227

    def setUp(self):
        # Instantiate new ircBot
        self.bot = ircBot(self.FAKE_SERVER, self.FAKE_PORT, "TestBot", "Testing the bot framework")

    def tearDown(self):
        # Stop the bot
        if self.bot.is_alive():
            self.bot.stop()
            self.bot.join(10)


@patch('lircbot.lircbot.socket.socket')
class TestBotConnect(BotSetupMixin, unittest.TestCase):

    TIMEOUT_THRESHOLD = 3 * 60

    def setUp(self):
        super(TestBotConnect, self).setUp()

    def tearDown(self):
        super(TestBotConnect, self).tearDown()

    def test_socket_connect_called(self, mock_socket):
        # Test socket.connect() called correctly
        self.bot._connect()
        self.bot.irc.connect.assert_called_once_with((self.FAKE_SERVER, self.FAKE_PORT))

    def test_socket_timeout_set(self, mock_socket):
        # Set bot timeout
        self.bot.timeout_threshold(self.TIMEOUT_THRESHOLD)
        # Test socket.settimeout() called correctly
        self.bot._connect()
        self.bot.irc.settimeout.assert_called_once_with(self.TIMEOUT_THRESHOLD)

    def test_bot_connected_set(self, mock_socket):
        # Test that the bot.connected variable was set to True
        self.bot._connect()
        self.assertTrue(self.bot.connected)

    def test_socket_error_raised(self, mock_socket):
        # Tell the mock socket.connect() method to raise a socket error
        mock_socket().connect = MagicMock(side_effect=socket.error)
        # Check socket error was raised and bot.connected variable was set to False
        self.assertRaises(socket.error, self.bot._connect)
        self.assertFalse(self.bot.connected)


class TestBotDisconnect(BotSetupMixin, unittest.TestCase):

    DC_MESSAGE = "Disconnect Test"

    def setUp(self):
        super(TestBotDisconnect, self).setUp()
        # Set up MagicMock objects for the bot's socket and input/output buffers
        with patch('lircbot.lircbot.socket.socket') as socketMock:
            self.bot.irc = socketMock
        with patch('lircbot.lircbot.ircInputBuffer') as ircInputBufferMock:
            self.bot.inBuf = ircInputBufferMock
        with patch('lircbot.lircbot.ircOutputBuffer') as ircOutputBufferMock:
            self.bot.outBuf = ircOutputBufferMock

    def tearDown(self):
        super(TestBotDisconnect, self).tearDown()

    def test_socket_close_called(self):
        # Test socket.close() called correctly
        self.bot._disconnect(self.DC_MESSAGE)
        self.bot.irc.close.assert_called_once_with()

    def test_bot_connected_set(self):
        # Test that the bot.connected variable was set to False
        self.bot._disconnect(self.DC_MESSAGE)
        self.assertFalse(self.bot.connected)

    def test_quit_message_set(self):
        # Test outBuf.sendBuffered() called correctly
        self.bot._disconnect(self.DC_MESSAGE)
        self.bot.outBuf.sendBuffered.assert_called_once_with("QUIT :" + self.DC_MESSAGE)

    def test_socket_error_raised(self):
        # Tell the mock outBuf.sendBuffered() method to raise a socket error
        self.bot.outBuf().sendBuffered = MagicMock(side_effect=socket.error)
        # Check socket error was raised and bot.connected variable was set to False
        self.assertRaises(socket.error, self.bot._disconnect(self.DC_MESSAGE))
        self.assertFalse(self.bot.connected)


class TestBotReconnect(BotSetupMixin, unittest.TestCase):

    def setUp(self):
        super(TestBotReconnect, self).setUp()
        self.bot._connect = MagicMock()
        self.bot._disconnect = MagicMock()
        self.bot.send_auth_details = MagicMock()

    def tearDown(self):
        super(TestBotReconnect, self).tearDown()

    def test_connect_called(self):
        # Test bot._connect was called
        self.bot.reconnect()
        self.bot._connect.assert_called_once_with()

    def test_send_auth_details_called(self):
        # Test bot.send_auth_details() was called
        self.bot.reconnect()
        self.bot.send_auth_details.assert_called_once_with()

    def test_disconnect_called(self):
        self.bot.connected = True
        # Test bot._disconnect was called
        self.bot.reconnect()
        self.bot._disconnect.assert_called_once_with('Reconnecting')

    def test_disconnect_not_called(self):
        self.bot.connected = False
        # Test bot._disconnect was not called
        self.bot.reconnect()
        assert not self.bot._disconnect.called, 'Method was called, expected no call'
