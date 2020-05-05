#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset

python manage.py migrate
python manage.py collectstatic --noinput --verbosity 0
gunicorn config.wsgi -w 1 --worker-class gevent -b 0.0.0.0:8000 --chdir=/app

# gunicorn config.wsgi -w 1   -b 0.0.0.0:8000
# to include command initadmin here in future. 2020-05-05 15:44:38