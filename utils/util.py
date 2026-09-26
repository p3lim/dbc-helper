#!/usr/bin/env python3

import csv
import os
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path
from types import SimpleNamespace

build = os.environ.get('DBC_BUILD')
flavor = os.environ.get('INPUT_FLAVOR')
classic = os.environ.get('IS_CLASSIC', 'false') == 'true'

def log(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)

def bail(*args, **kwargs):
  log(*args, **kwargs)
  sys.exit(1)

# let wago track requests
opener = urllib.request.build_opener()
opener.addheaders = [('User-agent', 'actions/dbc-helper')]
urllib.request.install_opener(opener)

# set timeout
socket.setdefaulttimeout(60)

def _coerce_row(row):
  # coerce rows into SimpleNamespace for easier lookups
  coerced = {}
  for key, value in row.items():
    try:
      coerced[key] = int(value)
    except (ValueError, TypeError):
      coerced[key] = value
  return SimpleNamespace(**coerced)

def dbc(file, extra_rows=None):
  # it would be highly preferable if we just had access to all of the csv files in a repo
  # just because of this collision crap, also downloading can be slow

  # cache file to disk
  file_path = Path(f'{os.environ.get("RUNNER_TEMP")}/{build}/{file}.csv')
  file_path.parent.mkdir(parents=True, exist_ok=True)

  if not file_path.is_file():
    url = f'https://wago.tools/db2/{file}/csv?build={build}'
    log(f'- Downloading {url} to {file_path}')

    tmp_path = file_path.with_suffix('.csv.part')
    try:
      urllib.request.urlretrieve(url, tmp_path)
      tmp_path.rename(file_path)
    except urllib.error.HTTPError as e:
      cfray = e.headers.get('CF-RAY', '')
      bail(f'Failed to download "{file_path.stem}": {e} (CF-RAY={cfray})')
    except urllib.error.URLError as e:
      bail(f'Failed to download "{file_path.stem}": {e}')
    finally:
      tmp_path.unlink(missing_ok=True)

  # return rows as a yielder
  def rows():
    with file_path.open('r', newline='') as f:
      for row in csv.DictReader(f):
        yield _coerce_row(row)
    for row in extra_rows or []:
      yield _coerce_row(row)

  return rows()


DEFAULT_TEMPLATE = '''
-- this file is auto-generated
{}
{} = {{
{}
}}
'''

def templateLuaTable(prefix, objectName, objectFormat, data):
  lines = [objectFormat.format(**data[item]) for item in sorted(data)]
  print(DEFAULT_TEMPLATE.format(prefix, objectName, '\n'.join(lines)).strip())
