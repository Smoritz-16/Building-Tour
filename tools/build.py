"""Rebuild the self-contained index.html from src/page.html and the FX renderers in src/fx/."""
from pathlib import Path

root = Path(__file__).resolve().parent.parent
page = (root / 'src' / 'page.html').read_text(encoding='utf-8')
page = page.replace('/*__ASCII_FX__*/', (root / 'src' / 'fx' / 'ascii-fx.js').read_text(encoding='utf-8'))
page = page.replace('/*__ORB_FX__*/', (root / 'src' / 'fx' / 'orb-fx.js').read_text(encoding='utf-8'))
(root / 'index.html').write_text(page, encoding='utf-8')
print('Wrote index.html')
