kpdjango
========

kandbox planner

<a href="https://github.com/vchaptsev/cookiecutter-django-vue">
    <img src="https://img.shields.io/badge/built%20with-Cookiecutter%20Django%20Vue-blue.svg" />
</a>


## Development

Install [Docker](https://docs.docker.com/install/) and [Docker-Compose](https://docs.docker.com/compose/). Start your virtual machines with the following shell command:

`docker-compose up --build`

If all works well, you should be able to create an admin account with:

`docker-compose run backend python manage.py createsuperuser`




POSTGRES_DB=kpdjango
POSTGRES_PASSWORD=mysecretpass
POSTGRES_USER=postgresuser
POSTGRES_PORT=5432
POSTGRES_HOST=localhost
export DATABASE_URL="postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
env |grep DATA



export DEBUG=True
export SECRET_KEY=tVNdCqDzzEjWbHaH 

export DOMAIN=http://localhost:8000
export ALLOWED_HOSTS=*


~/Documents/qduan/git/work_git/temp/4/vuecookie/kpdjango/backend

./manage.py runserver

python ./kandbox_planner/fsm_adapter/toy_generator/london_service_generator.py 	a32c2eba70abc042d40da1f471b334bff4ae23a7
