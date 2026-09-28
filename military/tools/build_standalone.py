#!/usr/bin/env python3
"""Bundle index.html, data/rate_card.js and the logos into ONE self-contained HTML file
(dist/Wilkins Military Proposal Builder.html) that can be saved in Box and opened from anywhere."""
import base64, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..'))
html = open(os.path.join(ROOT, 'index.html')).read()
data = open(os.path.join(ROOT, 'data', 'rate_card.js')).read()
def b64(p): return base64.b64encode(open(os.path.join(ROOT, p), 'rb').read()).decode()
logo_w = 'data:image/png;base64,' + b64('assets/wilkins-logo-white.png')
logo_b = 'data:image/png;base64,' + b64('assets/wilkins-logo.png')
assert '<script src="data/rate_card.js"></script>' in html
html = html.replace('<script src="data/rate_card.js"></script>', '<script>\n' + data + '\n</script>')
html = html.replace('src="assets/wilkins-logo-white.png"', 'src="%s"' % logo_w)
html = html.replace("const res = await fetch('assets/wilkins-logo.png');", "const res = await fetch('%s');" % logo_b)
os.makedirs(os.path.join(ROOT, 'dist'), exist_ok=True)
out = os.path.join(ROOT, 'dist', 'Wilkins Military Proposal Builder.html')
open(out, 'w').write(html)
print('wrote', out, round(os.path.getsize(out) / 1024), 'KB')
