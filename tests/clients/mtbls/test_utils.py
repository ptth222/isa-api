import unittest
from unittest.mock import patch
from isatools.net.metabolights.utils import MTBLSDownloader


@patch('isatools.net.metabolights.utils.FTP', autospec=True)
class TestMTBLSDownloader(unittest.TestCase):

    def test_singleton(self, mock_ftp):
        mock = mock_ftp.return_value
        mock.login.return_value = "230"
        a = MTBLSDownloader()
        b = MTBLSDownloader()
        self.assertEqual(id(a), id(b))

    def test_connection_error(self, mock_ftp):
        def mock_login(*args, **kwargs):
            raise Exception('Mock FTP Failure')
        mock = mock_ftp.return_value
        mock.login.return_value = '500'
        mock.login = mock_login
        MTBLSDownloader._instance = None  # reset singleton to get a new mock
        with self.assertRaises(Exception) as context:
            MTBLSDownloader()
        self.assertEqual(str(context.exception), "Cannot contact the remote FTP server: Mock FTP Failure")
