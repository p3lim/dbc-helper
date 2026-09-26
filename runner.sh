#!/bin/bash

set -euo pipefail

if test "${GITHUB_WORKSPACE:-}" = ''; then
  RUNNER_TEMP="/tmp/dbc-helper"
  export RUNNER_TEMP
  mkdir -p "$RUNNER_TEMP"

  GITHUB_ACTION_PATH="$(dirname "$0")"
  export GITHUB_ACTION_PATH

  GITHUB_WORKSPACE="$(pwd)"
  export GITHUB_WORKSPACE

  GITHUB_OUTPUT="$(mktemp)"
  export GITHUB_OUTPUT
  trap 'rm -rf -- "$GITHUB_OUTPUT"' EXIT

  # make it a little easier to run locally too
  INPUT_FILES="$1: $2"
fi

# check inputs
if test "$INPUT_FILES" = ''; then
  echo 'no files to process'
  exit 1
fi

# strip empty lines
INPUT_FILES="$(sed '/^[[:space:]]*$/d' <<< "$INPUT_FILES")"

# set defaults
INPUT_FLAVOR="${INPUT_FLAVOR:-retail}"
INPUT_PTR="${INPUT_PTR:-false}"
INPUT_BETA="${INPUT_BETA:-false}"

product='wow' # the default
if [[ "${INPUT_FLAVOR,,}" =~ (retail|standard) ]]; then
  product='wow'
elif [[ "${INPUT_FLAVOR,,}" =~ (forever|camelot) ]]; then
  product='wow_classic_beta' # temp
elif [[ "${INPUT_FLAVOR,,}" =~ (classic_era|vanilla) ]]; then
  product='wow_classic_era'
elif [[ "${INPUT_FLAVOR,,}" =~ (anniversary|tbc) ]]; then
  product='wow_anniversary'
elif [[ "${INPUT_FLAVOR,,}" =~ (titan|wrath) ]]; then
  product='wow_classic_titan'
elif [[ "${INPUT_FLAVOR,,}" =~ (classic|mists) ]]; then
  product='wow_classic'
elif test "$INPUT_FLAVOR" != ''; then
  echo "invalid flavor '$INPUT_FLAVOR'"
  exit 1
fi

# download builds
if [ -f "$RUNNER_TEMP/builds" ]; then
  builds="$(cat "$RUNNER_TEMP/builds")"
else
  builds="$(curl -sSL --max-time 60 'https://wago.tools/api/builds/latest')"
  echo "$builds" > "$RUNNER_TEMP/builds"
fi

# shorthand for querying builds
function get_version {
  if jq -e -r --arg product "$1" '.[$product]' <<< "$builds" > /dev/null; then
    jq -r --arg product "$1" '.[$product].version' <<< "$builds"
  fi
}

function is_newer_version {
  printf '%s\n' "$1" "$2" | sort -C -V -r
}

# get latest version and build number for product
latest_version="$(get_version "$product")"

if [ -z "$latest_version" ]; then
    echo "unable to get latest version for '$product'"
    exit 1
fi

# go through ptr and beta versions of the product to check if they have a newer build
if [ "${INPUT_PTR,,}" = 'true' ]; then
  if [ "$product" = 'wow' ]; then
    version="$(get_version 'wowt')"
    if is_newer_version "${version}" "${latest_version}"; then
      latest_version="$version"
    fi
    version="$(get_version 'wowxptr')"
    if is_newer_version "${version}" "${latest_version}"; then
      latest_version="$version"
    fi
  else
    version="$(get_version "${product}_ptr")"
    if is_newer_version "${version}" "${latest_version}"; then
      latest_version="$version"
    fi
  fi
fi

if [ "${INPUT_BETA,,}" = 'true' ]; then
  if [ "$product" != 'wow_classic_era' ]; then
    version="$(get_version "${product}_beta")"
    if is_newer_version "${version}" "${latest_version}"; then
      latest_version="$version"
    fi
  fi
fi

# action output
{
  echo "flavor=$INPUT_FLAVOR"
  echo "version=$latest_version"
  echo "build=${latest_version##*.}"
} >> "$GITHUB_OUTPUT"

# export version for the util
export DBC_BUILD="$latest_version"
echo "DBC $product $latest_version"

# export flavor and classic for the util
export INPUT_FLAVOR

# expose our utility "library"
export PYTHONPATH="${GITHUB_ACTION_PATH}/utils:${PYTHONPATH}"

# loop over input mapping
pids=()
while read -r script output; do
  # clean up names and prefix paths
  script="${script%:}"
  script="${script%.py}.py"

  # ensure directory exists first
  mkdir -p "$(dirname "$output")"

  # run script async
  echo "Running '$script' > '$output'"
  python3 "${GITHUB_WORKSPACE}/${script}" > "${GITHUB_WORKSPACE}/${output}" &

  # store script pid
  pids+=($!)
done <<< "${INPUT_FILES}"

# wait for all scripts to finish
for pid in "${pids[@]}"; do
  wait "$pid" || exit 1
done
