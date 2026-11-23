"""Checks on the static page (no browser needed). Run: python tools/test_web.py

- Relative URLs only (the proxy serves the app under /doom/), and nothing from the internet
  at runtime: no external scripts, styles or fetches.
- The key codes the touch controls send match PrBoom+'s bindings (doomdef.h / m_misc.c),
  including the ones written into the default config.
"""
import re
import sys
import unittest
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"


class Page(unittest.TestCase):
    def setUp(self):
        self.files = {p.name: p.read_text(encoding="utf-8") for p in WEB.iterdir()
                      if p.suffix in (".html", ".js", ".css", ".webmanifest")}

    def test_relative_urls(self):
        bad = []
        for name, text in self.files.items():
            for m in re.finditer(r'(?:src|href)\s*=\s*"(/[^"]*)"', text):
                bad.append(f"{name}: {m.group(1)}")
            for m in re.finditer(r'fetch\(\s*["\'`](/[^"\'`]*)', text):
                bad.append(f"{name}: fetch {m.group(1)}")
            for m in re.finditer(r'url\(\s*["\']?(/[^)"\']*)', text):
                bad.append(f"{name}: css url {m.group(1)}")
        self.assertEqual(bad, [])

    def test_nothing_loaded_from_the_internet(self):
        bad = []
        for name, text in self.files.items():
            for m in re.finditer(r'<(?:script|link)[^>]+(?:src|href)="(https?:)?//', text):
                bad.append(f"{name}: {m.group(0)}")
            for m in re.finditer(r'(?:fetch|import)\(\s*["\'`]https?://', text):
                bad.append(f"{name}: {m.group(0)}")
            for m in re.finditer(r'url\(\s*["\']?https?://', text):
                bad.append(f"{name}: {m.group(0)}")
        self.assertEqual(bad, [])

    def test_home_button(self):
        # app contract item 10: the AirplaneMode home button, in the launcher's header and
        # floating over the loading, game and error screens; no old text link
        html = self.files["index.html"]
        links = re.findall(r'<a class="am-home[^"]*"[^>]*>', html)
        self.assertEqual(len(links), 2, links)
        for a in links:
            self.assertIn('href="../"', a)
            self.assertIn('aria-label="AirplaneMode home"', a)
        self.assertRegex(html, r'(?s)<header>.*<a class="am-home" href="\.\./".*</header>')
        self.assertNotIn('class="home"', html)
        self.assertIn(".am-home:focus-visible", self.files["style.css"])

    def test_touch_key_codes(self):
        js = self.files["touch.js"]
        expect = {
            "up": "0xad", "down": "0xaf", "left": "0xac", "right": "0xae",   # KEYD_*ARROW
            "esc": "27", "enter": "13", "backspace": "127", "map": "9",
            "fire": "0x80 + 0x1d",        # KEYD_RCTRL (key_fire)
            "use": "32",                  # space (key_use)
            "speed": "0x80 + 0x36",       # KEYD_RSHIFT (key_speed)
            "nextweapon": "0x80 + 0x6b",  # KEYD_MWHEELUP (key_nextweapon default)
            "prevweapon": "0x80 + 0x6c",  # KEYD_MWHEELDOWN
            "forward": "119", "back": "115", "strafeleft": "97", "straferight": "100",  # w s a d
        }
        for name, code in expect.items():
            self.assertRegex(js, rf"\b{name}: {re.escape(code)}\b", name)

    def test_buttons_name_known_keys(self):
        js = self.files["touch.js"]
        keys = set(re.findall(r"^\s+(\w+): ", js.split("const KEY = {")[1].split("};")[0], re.M))
        keys |= set(re.findall(r"(\w+): [0-9x]", js.split("const KEY = {")[1].split("};")[0]))
        used = set(re.findall(r'data-key="(\w+)"', self.files["index.html"]))
        self.assertTrue(used, "no buttons found")
        self.assertEqual(used - keys, set())

    def test_default_config_weapon_keys(self):
        # key_nextweapon/prevweapon in the default cfg must equal what the buttons send
        cfg = self.files["app.js"]
        self.assertIn("key_nextweapon 0xeb", cfg)   # 0x80 + 0x6b
        self.assertIn("key_prevweapon 0xec", cfg)
        self.assertIn('snd_midiplayer "opl2"', cfg)


if __name__ == "__main__":
    sys.exit(unittest.main(verbosity=1))
