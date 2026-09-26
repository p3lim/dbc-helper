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

def log(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)

def bail(*args, **kwargs):
  log(*args, **kwargs)
  sys.exit(1)

from types import SimpleNamespace
class CSVReader(csv.DictReader):
  def __init__(self, file, extra_rows=None, *args, **kwargs):
    super().__init__(file, *args, **kwargs)
    self.extra_rows = extra_rows or []
    self.extra_iterator = None

  def __next__(self):
    # override iterator to return extra rows once the csv file is exhausted
    try:
      row = super().__next__()
    except StopIteration:
      if self.extra_iterator is None:
        self.extra_iterator = iter(self.extra_rows)
      try:
        row = next(self.extra_iterator)
      except StopIteration:
        raise StopIteration

    # try convert number values to integers
    for key in self.fieldnames:
      if key in row:
        try:
          row[key] = int(row[key])
        except:
          pass

    # convert dict to SimpleNamespace so it's nicer to work with
    return SimpleNamespace(**row)


# let wago track requests
opener = urllib.request.build_opener()
opener.addheaders = [('User-agent', 'actions/dbc-helper')]
urllib.request.install_opener(opener)

# set timeout
socket.setdefaulttimeout(60)

def dbc(file, extra_rows=None):
  # it would be highly preferable if we just had access to all of the csv files in a repo
  # just because of this collision crap, also downloading can be slow

  # cache file to disk
  file_path = Path(f'{os.environ.get("RUNNER_TEMP")}/{build}/{file}.csv')
  file_path.parent.mkdir(parents=True, exist_ok=True)

  if not file_path.is_file():
    url = f'https://wago.tools/db2/{file}/csv?build={build}'
    try:
      urllib.request.urlretrieve(url, file_path)
    except urllib.error.HTTPError as e:
      cfray = e.headers.get('CF-RAY', '')
      bail(f'Failed to download "{file_path.stem}": {e} (CF-RAY={cfray})')
    except urllib.error.URLError as e:
      bail(f'Failed to download "{file_path.stem}": {e}')

  # return it as a CSV object
  return CSVReader(open(file, 'r'), extra_rows)


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
