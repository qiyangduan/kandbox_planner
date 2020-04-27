kplanner Web
============

The web interface for kandbox planner


:License: Internal


# How to Run

    $ pip install -r requirements/local.txt

    $ ./manage.py makemigrations 
    $ ./manage.py migrate
    $ ./manage.py migrate
    $ ./manage.py createsuperuser
    $ ./manage.py runserver 0.0.0.0:8000





# How to reset Django Migrations.

find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc"  -delete

```shell
pip install -r requirements.txt

./manage.py makemigrations 

./manage.py migrate --fake kpdata zero
./manage.py migrate

./manage.py createsuperuser
./manage.py runserver 0.0.0.0:8000

```
