#!/bin/sh
find . -path "*/migrations/*.pyc" -delete
find . -path "*/migrations/*.py" \
  ! -name "__init__.py" \
  -delete