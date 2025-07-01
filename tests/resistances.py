#!/usr/bin/env python3

import util

for row in util.dbc('resistances'):
  print(f'resistance name: {row.Name_lang}')
