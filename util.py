#!/usr/bin/env python3

import os
import csv
import tempfile
import urllib.request

from types import SimpleNamespace
class CSVReader(csv.DictReader):
  def __next__(self):
    row = super().__next__()
    for key in self.fieldnames:
      try:
        row[key] = int(row[key])
      except:
        pass
    return SimpleNamespace(**row)


def dbc(file):
  # we'll need to avoid collisions
  tempfile.tempdir = os.environ["RUNNER_TEMP"]
  tmp = tempfile.mkdtemp()

  # cache file to disk
  url = f'https://wago.tools/db2/{file}/csv?build={os.environ["DBC_BUILD"]}'
  file = f'{tmp}/{file}.csv'
  urllib.request.urlretrieve(url, file)

  # return it as a CSV object
  return CSVReader(open(file, 'r'))


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
