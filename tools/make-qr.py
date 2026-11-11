#!/usr/bin/env python3
"""Make a brand-colored QR code SVG for videos.

    python3 tools/make-qr.py <url> <out.svg>

Needs: pip install segno
Error correction Q (about 25% damage tolerance), dark navy on white, 4-module quiet zone.
"""
import sys, segno
url, out = sys.argv[1], sys.argv[2]
qr = segno.make(url, error='q', micro=False)
qr.save(out, kind='svg', dark='#0f2c5c', light='#ffffff', border=4, scale=10, xmldecl=False, svgns=True, omitsize=True)  # viewBox only, so it scales
print(f'wrote {out}  version {qr.version}, {qr.symbol_size(border=0)[0]} modules, error {qr.error}')
