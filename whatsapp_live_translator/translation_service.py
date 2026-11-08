"""Explicit opt-in translation; one selected provider, no automatic fallback."""
from __future__ import annotations

import json
import threading
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class TranslationClient:
    PROVIDERS = {'Google': 'https://translate.google.com/translate_a/single',
                 'MyMemory': 'https://api.mymemory.translated.net/get'}

    def __init__(self, opener=None):
        self._opener = opener or urlopen
        self._lock = threading.Lock()
        self._enabled = False
        self._provider = 'MyMemory'
        self._generation = 0

    def configure(self, provider: str, enabled: bool) -> None:
        if provider not in self.PROVIDERS:
            raise ValueError('Unknown translation provider')
        with self._lock:
            self._generation += 1
            self._provider, self._enabled = provider, bool(enabled)

    @property
    def session(self):
        with self._lock:
            return self._generation

    @property
    def enabled(self) -> bool:
        with self._lock:
            return self._enabled

    def translate(self, text: str, target: str, source: str, timeout: int = 15, session=None) -> str:
        with self._lock:
            if not self._enabled or (session is not None and session != self._generation):
                raise RuntimeError('在线翻译未启用，未发送文本')
            provider = self._provider
        if provider == 'Google':
            params = {'client': 'at', 'sl': 'auto', 'tl': target, 'dt': 't', 'q': text}
        else:
            params = {'q': text, 'langpair': f'{source}|{target}'}
        request = Request(self.PROVIDERS[provider] + '?' + urlencode(params),
                          headers={'User-Agent': 'WhatsAppSideTranslator/1.1'})
        try:
            with self._opener(request, timeout=timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
            if provider == 'Google':
                result = ''.join(item[0] for item in data[0] if item and item[0]).strip()
            else:
                if str(data.get('responseStatus', '')) != '200':
                    raise ValueError('Service returned an error')
                result = data.get('responseData', {}).get('translatedText', '').strip()
            if not result:
                raise ValueError('Empty translation')
            return result
        except Exception:
            # Exception strings from HTTP libraries can contain the original URL/text.
            raise RuntimeError(f'{provider} 翻译失败；未切换服务，请检查网络、限制或服务配置') from None
