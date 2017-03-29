#!/bin/sh
echo 'Activating python virtualenv'
. venv/bin/activate
echo 'creating or updating the db'
export FLASK_APP=wotdapp
python -m flask db upgrade
echo 'Starting the app server'
gunicorn --log-file gunicorn.log --log-level info -p app.pid wotdapp:app