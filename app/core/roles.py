# app/core/roles.py
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    MODEL = "model"
    PROJECT = "project"
