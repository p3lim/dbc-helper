#!/bin/bash

set -e

# check inputs
if test "$INPUT_FILES" = ''; then
  echo 'no files to process'
  exit 1
fi

# strip empty lines
INPUT_FILES="$(sed '/^[[:space:]]*$/d' <<< "$INPUT_FILES")"

product='wow' # the default
if [[ "${INPUT_FLAVOR,,}" =~ (retail|mainline) ]]; then
  product='wow'
elif [[ "${INPUT_FLAVOR,,}" =~ (classic_era|vanilla) ]]; then
  product='wow_classic_era'
elif [[ "${INPUT_FLAVOR,,}" = 'classic' ]]; then
  product='wow_classic'
elif test "$INPUT_FLAVOR" != ''; then
  echo "invalid flavor '$INPUT_FLAVOR', must be one of: retail, mainline, classic, classic_era, vanilla."
  exit 1
fi

# download builds
builds="$(curl -sSL 'https://wago.tools/api/builds')"

# shorthand for querying builds
function get_version {
  jq -r --arg product "$1" '.[$product] | sort_by(.version) | last | .version' <<< "$builds"
}

# get latest version and build number for product
latest_version="$(get_version "$product")"
latest_build="${latest_version##*.}"

# go through ptr and beta versions of the product to check if they have a newer build
if [ -n "$INPUT_PTR" ]; then
  if [ "$product" = 'wow' ]; then
    version="$(get_version 'wowt')"
    build="${version##*.}"
    if ((build > latest_build)); then
      latest_version="$version"
      latest_build="$build"
    fi
    version="$(get_version 'wowxptr')"
    build="${version##*.}"
    if ((build > latest_build)); then
      latest_version="$version"
      latest_build="$build"
    fi
  else
    version="$(get_version "${product}_ptr")"
    build="${version##*.}"
    if ((build > latest_build)); then
      latest_version="$version"
      latest_build="$build"
    fi
  fi
fi

if [ -n "$INPUT_BETA" ]; then
  if [ "$product" != 'wow_classic_era' ]; then
    version="$(get_version "${product}_beta")"
    build="${version##*.}"
    if ((build > latest_build)); then
      latest_version="$version"
      latest_build="$build"
    fi
  fi
fi

# action output
{
  echo "flavor=$INPUT_FLAVOR"
  echo "version=$latest_version"
  echo "build=$latest_build"
} >> "$GITHUB_OUTPUT"

# export version for the util
export DBC_BUILD="$latest_version"

# expose our utility "library"
export PYTHONPATH="${GITHUB_ACTION_PATH}/utils:${PYTHONPATH}"

# loop over input mapping
pids=()
while read -r script output; do
  # clean up names and prefix paths
  script="${script%:}"
  script="${script%.py}.py"

  # run script async
  echo "Running '$script' > '$output'"
  python3 "${GITHUB_WORKSPACE}/${script}" > "${GITHUB_WORKSPACE}/${output}" &

  # store script pid
  pids+=($!)
done <<< "${INPUT_FILES}"

# wait for all scripts to finish
for pid in "${pids[@]}"; do
  wait "$pid" || exit
done
