# DBC Helper

This is a tool to make it easier to scrape DBC/DB2 files from World of Warcraft, using provided CSV files from [Wago Tools](https://wago.tools/db2).

## Usage

It is intended to be run as a GitHub Action (see below), defining Python script file(s) that generate output.

The action comes with some Python utilities for downloading the CSV file(s) and structuring them. An example use-case can be as follows:

```python
import util # provided by this action

# output the spell ID of every spell that is considered a shapeshift
for row in util.dbc('spells'):
  if row.NameSubtext_lang == 'Shapeshift':
    print(row.ID)
```

The mapping of scripts to run and the files they should output to is as follows:

```
script1: output1
script2: output2
```

## GitHub Action

You can use this in a GitHub workflow by referencing `p3lim/dbc-helper@master`.  
There will probably never be any tags, so if you prefer stability you should consider forking this project, or pinning by commit hash.

Options:
- `flavor` - sets the game version to scrape data from, must be one of:
  - `retail` (aliases: `mainline`)
  - `classic`
  - `classic_era` (aliases: `vanilla`)
- `beta` - set to true to prefer beta versions of the game, if they are more recent
- `ptr` - set to true to prefer ptr versions of the game, if they are more recent
- `files` - script/output mapping, separated by lines, see example below

#### Example

This example workflow will do the following:
- check out the project
- use this action to run two scripts
- create a pull request if there were changes to the output files

This will occur every day at 12:00, or when triggered manually.

```yaml
name: Scrape

on:
  schedule:
    - cron: 0 12 * * *
  workflow_dispatch:

permissions:
  pull-requests: write
  contents: write

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - name: Clone project
        uses: actions/checkout@v4

      - name: Run scripts
        uses: p3lim/dbc-helper@master
        id: scraper
        with:
          flavor: retail # this is the default
          beta: true
          ptr: true
          files: |
            scripts/spells.py: data/spells.lua
            scripts/items.py: data/items.lua

      - name: Create pull request
        uses: peter-evans/create-pull-request@v7
        # requires permissions, see https://github.com/peter-evans/create-pull-request#workflow-permissions
        with:
          title: Update ${{ steps.scraper.outputs.flavor }} data to ${{ steps.scraper.outputs.version }}
          commit-message: Update ${{ steps.scraper.outputs.flavor }} data to ${{ steps.scraper.outputs.version }}
          body: ''
          branch: update-data-${{ steps.scraper.outputs.flavor }}
          delete-branch: true
```
