## Run the application

### Run manually using local python environment
``uvicorn app.main:app --reload``


### Run using docker
``docker-compose up --build``

### Run database migration
``
docker exec -it fastapi_project_app alembic revision --autogenerate -m "Last name added to user model"
``

``docker exec -it fastapi_project_app alembic upgrade head``

### Run tests

``docker exec -it fastapi_project_app pytest tests/ -v``