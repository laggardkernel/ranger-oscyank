import importlib.util
import os
import sys
import types
import unittest


class FakeYank:
    pass


def load_plugin():
    commands = types.ModuleType("ranger.config.commands")
    commands.set_ = type("set_", (), {})
    commands.yank = FakeYank
    ranger = types.ModuleType("ranger")
    ranger.api = types.ModuleType("ranger.api")
    ranger.api.hook_ready = lambda fm: setattr(fm, "delegated", True)
    config = types.ModuleType("ranger.config")
    config.commands = commands
    ranger.config = config
    sys.modules.update(
        {
            "ranger": ranger,
            "ranger.api": ranger.api,
            "ranger.config": config,
            "ranger.config.commands": commands,
        }
    )
    root = os.path.dirname(__file__)
    spec = importlib.util.spec_from_file_location(
        "oscyank_plugin", os.path.join(root, "__init__.py"),
        submodule_search_locations=[root],
    )
    plugin = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = plugin
    spec.loader.exec_module(plugin)
    return plugin


class PluginTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plugin = load_plugin()

    def test_payload_is_utf8_base64_osc52(self):
        module = __import__("oscyank_plugin.oscyank", fromlist=["osc52_payload"])
        self.assertEqual(
            module.osc52_payload("hé"),
            b"\033]52;c;aMOp\a",
        )

    def test_over_limit_does_not_write(self):
        command = self.plugin.oscyank.__new__(self.plugin.oscyank)
        module = __import__("oscyank_plugin.oscyank", fromlist=["open"])
        command.fm = types.SimpleNamespace(
            settings=types.SimpleNamespace(_settings={"oscyank:max_length": 1}),
            notify=lambda *args, **kwargs: setattr(command, "warning", args[0]),
        )
        module.open = lambda *args, **kwargs: self.fail("tty must not be opened")
        try:
            command.osc_copy("é")
        finally:
            del module.open
        self.assertIn("2 bytes", command.warning)

    def test_startup_warning_once_and_hook_delegation(self):
        fm = types.SimpleNamespace(notifications=[])
        fm.notify = lambda *args, **kw: fm.notifications.append(args[0])
        original = self.plugin.curses.tigetstr
        self.plugin._warned = False
        self.plugin.curses.tigetstr = lambda name: None
        try:
            self.plugin.hook_ready(fm)
            self.plugin.hook_ready(fm)
        finally:
            self.plugin.curses.tigetstr = original
        self.assertEqual(len(fm.notifications), 1)
        self.assertTrue(fm.delegated)


if __name__ == "__main__":
    unittest.main()
