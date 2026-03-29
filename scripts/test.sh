#!/usr/bin/env bash

set -ex

uv run pytest -n auto --cov --cov-report=term ${@}
