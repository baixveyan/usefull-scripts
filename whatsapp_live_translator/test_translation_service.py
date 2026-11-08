import io
import json
import unittest
from urllib.parse import parse_qs, urlsplit

from translation_service import TranslationClient


class TranslationTests(unittest.TestCase):
    def client(self, response=None, failure=None):
        calls = []
        def opener(request, **kwargs):
            calls.append(request)
            if failure:
                raise failure
            return io.BytesIO(json.dumps(response).encode('utf-8'))
        return TranslationClient(opener=opener), calls

    def test_default_disabled_and_revoke(self):
        client, calls = self.client([[['译文', 'text']]])
        with self.assertRaises(RuntimeError):
            client.translate('text', 'zh-CN', 'en')
        self.assertEqual(calls, [])
        client.configure('Google', True)
        self.assertEqual(client.translate('text', 'zh-CN', 'en'), '译文')
        client.configure('Google', False)
        with self.assertRaises(RuntimeError):
            client.translate('text', 'zh-CN', 'en')
        self.assertEqual(len(calls), 1)

    def test_google_no_fallback_and_redacted_error(self):
        client, calls = self.client(failure=OSError('https://example.com/?q=private-text'))
        client.configure('Google', True)
        with self.assertRaises(RuntimeError) as raised:
            client.translate('private-text', 'zh-CN', 'en')
        self.assertNotIn('private-text', str(raised.exception))
        self.assertEqual(len(calls), 1)
        self.assertEqual(urlsplit(calls[0].full_url).hostname, 'translate.google.com')

    def test_mymemory_payload_and_status(self):
        client, calls = self.client({'responseStatus': 200, 'responseData': {'translatedText': '你好'}})
        client.configure('MyMemory', True)
        self.assertEqual(client.translate('hello & friend', 'zh-CN', 'en'), '你好')
        query = parse_qs(urlsplit(calls[0].full_url).query)
        self.assertEqual(query['q'], ['hello & friend'])
        self.assertEqual(query['langpair'], ['en|zh-CN'])
        self.assertEqual(urlsplit(calls[0].full_url).hostname, 'api.mymemory.translated.net')
        client, _ = self.client({'responseStatus': 429, 'responseData': {'translatedText': 'limit'}})
        client.configure('MyMemory', True)
        with self.assertRaises(RuntimeError):
            client.translate('hello', 'zh-CN', 'en')

    def test_invalid_response_and_provider(self):
        for value in (None, {}, [], [[['', 'x']]]):
            client, calls = self.client(value)
            client.configure('Google', True)
            with self.assertRaises(RuntimeError):
                client.translate('x', 'zh-CN', 'en')
            self.assertEqual(len(calls), 1)
        with self.assertRaises(ValueError):
            client.configure('unknown-service', True)


if __name__ == '__main__':
    unittest.main()
