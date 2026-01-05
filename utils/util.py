#!/usr/bin/env python3

import os
import sys
import csv
import tempfile
import urllib.request

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


def dbc(file, extra_rows=None):
  # it would be highly preferable if we just had access to all of the csv files in a repo
  # just because of this collision crap, also downloading can be slow

  # we'll need to avoid collisions
  tempfile.tempdir = os.environ.get('RUNNER_TEMP', tempfile.gettempdir())
  tmp = tempfile.mkdtemp()

  # cache file to disk
  url = f'https://wago.tools/db2/{file}/csv?build={os.environ.get("DBC_BUILD")}'
  file = f'{tmp}/{file}.csv'
  urllib.request.urlretrieve(url, file)

  # return it as a CSV object
  return CSVReader(open(file, 'r'), extra_rows)


def bail(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)
  sys.exit(1)


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
