#!/usr/bin/env python3

import os
import csv
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
  # cache file to disk
  url = f'https://wago.tools/db2/{file}/csv?build={os.environ["DBC_BUILD"]}'
  file = f'{os.environ["RUNNER_TEMP"]}/{file}.csv'
  urllib.request.urlretrieve(url, file)

  # return it as a CSV object
  return CSVReader(open(file, 'r'))
