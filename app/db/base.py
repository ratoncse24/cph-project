from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import all models here to ensure they are registered with this Base instance
# The # noqa comments are to prevent linters from complaining about unused imports,
# as their import here is for the side effect of registration.
from app.models import *  # noqa
