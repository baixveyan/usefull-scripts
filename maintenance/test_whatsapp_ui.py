"""Local-only hidden Tk control checks with fake Store/OCR; no chat/window capture."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'whatsapp_live_translator'))
spec = importlib.util.spec_from_file_location('whatsapp_ui_test_app', ROOT / 'whatsapp_live_translator/app.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class HiddenUiTests(unittest.TestCase):
    def setUp(self):
        original_tk = app.tk.Tk
        def hidden_tk():
            root = original_tk()
            root.withdraw()
            # Scheduled listeners never run in this synthetic test.
            root.after = MagicMock()
            return root
        self.store = MagicMock()
        self.store.chats.return_value = []
        self.patches = [patch.object(app.tk, 'Tk', side_effect=hidden_tk),
                        patch.object(app, 'Store', return_value=self.store),
                        patch.object(app, 'RapidOCR', return_value=MagicMock()),
                        patch.object(app, 'find_whatsapp_window', side_effect=AssertionError('Window capture forbidden in test')),
                        patch.object(app.ImageGrab, 'grab', side_effect=AssertionError('Screenshots forbidden in test'))]
        for item in self.patches:
            item.start()
        self.ui = app.WhatsAppSidecar()
        self.ui.translation_client._opener = MagicMock(side_effect=AssertionError('Network forbidden in test'))

    def tearDown(self):
        self.ui.translation_tasks.close()
        try:
            self.ui.root.destroy()
        except app.tk.TclError:
            pass
        for item in reversed(self.patches):
            item.stop()

    def test_default_disabled_and_hidden(self):
        self.assertFalse(self.ui.translation_client.enabled)
        self.assertFalse(self.ui.online_enabled.get())
        self.assertEqual(self.ui.root.winfo_viewable(), 0)
        self.assertIn('Google', self.ui.provider_combo['values'])
        self.assertIn('MyMemory', self.ui.provider_combo['values'])

    def test_consent_cancel_enable_and_provider_reset(self):
        self.ui.online_enabled.set(True)
        with patch.object(app.messagebox, 'askyesno', return_value=False):
            self.ui.toggle_online_translation()
        self.assertFalse(self.ui.translation_client.enabled)
        self.ui.online_enabled.set(True)
        with patch.object(app.messagebox, 'askyesno', return_value=True):
            self.ui.toggle_online_translation()
        self.assertTrue(self.ui.translation_client.enabled)
        self.ui.translation_provider.set('MyMemory')
        self.ui.change_translation_provider()
        self.assertFalse(self.ui.translation_client.enabled)
        self.assertFalse(self.ui.online_enabled.get())
        self.ui.translation_client._opener.assert_not_called()

    def test_disabled_input_preserved_and_exit(self):
        self.ui.current_chat = 'synthetic-chat'
        self.ui.input.insert('1.0', 'synthetic input')
        self.ui.translate_and_add()
        self.assertEqual(self.ui.input.get('1.0', 'end').strip(), 'synthetic input')
        self.store.add_message.assert_not_called()
        with patch.object(app.messagebox, 'askyesno', return_value=True):
            self.ui.exit_app()
        self.assertTrue(self.ui.closing)
        self.store.clear_messages.assert_called_once()

    def test_queue_full_control_feedback(self):
        self.ui.translation_client.configure('Google', True)
        with patch.object(self.ui.translation_tasks, 'submit', return_value=False):
            self.ui.schedule_translation(1, 'synthetic-chat', 'synthetic input', 'en')
        self.assertIn('队列已满', self.ui.status.get())
        self.ui.translation_client._opener.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
