# WinOfTheDay
Celebrate your win of the day, big or small!

### Deployment Notes
create a new NFS site
clone into the 'protected' folder
virtualenv -p python2.7 venv
source venv/bin/activate
(venv) pip install -r requirements.txt
run tests
failed, missing static things
add bower_comonents/<item>/<dist> folders
run tests: pass!
try the startup script from ssh failed. no gunicorn
pip install gunicorn
try startup again, verify it's working from another ssh window
configure the startup script and proxy and in NFS GUI
startup fails
make sure startapp.sh has 775 permissions (execute)
make sure there is no prod db file
make sure the instance folder (or wherever the db is going to live) has web group and 775
run python -m flask db upgrade to create the db, it will be owned by user and permissions 644
BEFORE starting the daemon change the db file to group web and permissions 664 (allow web to write)
start it up!
