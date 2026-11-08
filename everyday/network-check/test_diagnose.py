import importlib.util
import io
import json
from pathlib import Path
import unittest
from urllib.error import HTTPError, URLError

spec = importlib.util.spec_from_file_location('network_diagnose', Path(__file__).with_name('diagnose.py'))
network = importlib.util.module_from_spec(spec)
spec.loader.exec_module(network)


class Response(io.BytesIO):
    status = 200
    def geturl(self):
        return 'https://example.com/sensitive?token=secret'
    def read(self, *args):
        raise AssertionError('Body should not be read')


class NetworkTests(unittest.TestCase):
    def test_head_only_and_private_paths_not_in_report(self):
        seen = []
        def opener(request, **kwargs):
            seen.append(request)
            return Response()
        result = network.diagnose(['https://example.com/private?token=secret'], default_opener=opener, proxies={})
        self.assertEqual(seen[0].get_method(), 'HEAD')
        self.assertTrue(result['endpoints'][0]['system_path']['successful_status'])
        self.assertNotIn('secret', json.dumps(result))
        self.assertNotIn('private', json.dumps(result))

    def test_proxy_password_and_error_redaction(self):
        proxy = network.proxy_summary({'https': 'http://user:secret@127.0.0.1:9999', 'no': 'private.local'})
        self.assertNotIn('secret', json.dumps(proxy))
        self.assertNotIn('private.local', json.dumps(proxy))
        self.assertTrue(proxy['https']['credentials_present'])
        def fail(*args, **kwargs):
            raise URLError(OSError('URL token=secret'))
        result = network.probe('https://example.com', 3, fail)
        self.assertFalse(result['http_response_received'])
        self.assertNotIn('secret', json.dumps(result))

    def test_http_403_is_a_response_not_connection_failure(self):
        def denied(*args, **kwargs):
            raise HTTPError('https://example.com/?secret', 403, 'Denied secret', {}, None)
        result = network.probe('https://example.com', 3, denied)
        self.assertTrue(result['http_response_received'])
        self.assertFalse(result['successful_status'])
        self.assertEqual(result['status'], 403)

    def test_explicit_direct_comparison(self):
        calls = []
        def fail(*args, **kwargs):
            calls.append('system')
            raise OSError('synthetic')
        def succeed(*args, **kwargs):
            calls.append('direct')
            return Response()
        result = network.diagnose(['https://example.com'], compare_direct=True,
                                  default_opener=fail, direct_opener=succeed, proxies={})
        self.assertEqual(calls, ['system', 'direct'])
        self.assertTrue(result['endpoints'][0]['direct_path']['successful_status'])

    def test_bad_targets_and_limits(self):
        for url in ['file:///secret', 'https://user:password@example.com', 'https://example.com/\nsecret', 'https://example.com:bad']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                network.target_info(url)
        with self.assertRaises(ValueError):
            network.diagnose([])
        with self.assertRaises(ValueError):
            network.diagnose(['https://example.com'], timeout=0)


if __name__ == '__main__':
    unittest.main()
