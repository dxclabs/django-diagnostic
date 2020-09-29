#! /bin/sh
set -ex
export CUSTOM_COMPILE_COMMAND="./scripts/pip_compile.sh"

# for requirements
# python -m piptools compile --generate-hashes requirements/requirements.in -o requirements/requirements.txt
python3 -m piptools compile --upgrade requirements/requirements.in -o requirements/requirements.txt
# python3.5 -m piptools compile --generate-hashes -P 'Django>=1.11,<2.0' "$@" -o requirements/requirements.txt

# for requirements-dev
# python -m piptools compile --generate-hashes requirements/requirements-dev.in -o requirements/requirements-dev.txt
python3 -m piptools compile --upgrade requirements/requirements-dev.in -o requirements/requirements-dev.txt
# python3.5 -m piptools compile --generate-hashes -P 'Django>=1.11,<2.0' "$@" -o requirements/requirements.txt
