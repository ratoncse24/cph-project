# Project Structure

This document outlines the directory and file structure of the FastAPI application.

## Root Directory

*   **`.env`**: Stores environment variables for configuration (e.g., database credentials, API keys, AWS settings). Not version controlled.
*   **`.gitignore`**: Specifies intentionally untracked files that Git should ignore (e.g., `.env`, `__pycache__/`, `*.pyc`, virtual environment directories).
*   **`alembic.ini`**: Configuration file for Alembic, the database migration tool.
*   **`docker-compose.yml`**: Defines and configures multi-container Docker applications. Used to orchestrate services like the FastAPI app and database.
*   **`Dockerfile`**: Contains instructions to build the Docker image for the FastAPI application.
*   **`README.MD`**: Provides an overview of the project, setup instructions, and how to run the application and migrations.
*   **`requirements.txt`**: Lists all Python package dependencies for the project.

## `alembic/`

This directory contains Alembic database migration scripts and configurations.

*   **`env.py`**: Alembic's runtime environment configuration script. It's used to set up the database connection and define how migrations are run.
*   **`README`**: A brief description of the `alembic/` directory's purpose.
*   **`script.py.mako`**: A Mako template file used by Alembic to generate new migration scripts.
*   **`versions/`**: This subdirectory holds all the individual database migration scripts. Each file represents a version of the database schema.
    *   `xxxxxxxxxxxx_description.py`: Individual migration files, named with a revision ID and a short description.

## `app/`

This is the main application directory containing the core logic of the FastAPI application.

*   **`main.py`**: The entry point for the FastAPI application. It initializes the FastAPI app instance and includes API routers.

### `app/api/`

Contains API endpoint definitions (routers).

*   **`__init__.py`**: Makes the `api` directory a Python package.
*   **`v1/`**: Subdirectory for version 1 of the API. This allows for API versioning.
    *   **`product.py`**: Defines API routes related to product management (e.g., `/products`).
    *   **`user.py`**: Defines API routes related to user management (e.g., user registration `/register`, login `/login`).

### `app/core/`

Contains core application settings, configurations, and utility modules.

*   **`__init__.py`**: Makes the `core` directory a Python package.
*   **`config.py`**: Defines application settings, often loaded from environment variables using Pydantic's `BaseSettings`. Includes database URLs, JWT secrets, AWS configurations, and SNS Topic ARNs.
*   **`logger.py`**: Configures application-wide logging.
*   **`roles.py`**: Defines user roles or permissions used for authorization (e.g., `UserRole.ADMIN`).

### `app/db/`

Handles database setup, session management, and base model definitions.

*   **`__init__.py`**: Makes the `db` directory a Python package.
*   **`base.py`**: Potentially contains the declarative base for SQLAlchemy models, or common database utility functions.
*   **`session.py`**: Manages database sessions, including setup for asynchronous sessions (`AsyncSession`) and dependency injection for FastAPI routes (`get_db`).

### `app/dependencies/`

Contains FastAPI dependency functions used for common tasks like authentication, authorization, or getting database sessions.

*   **`__init__.py`**: Makes the `dependencies` directory a Python package.
*   **`auth.py`**: Likely contains general authentication-related dependencies or utilities.
*   **`authorization.py`**: Contains dependency functions for role-based authorization (e.g., `require_roles`).
*   **`jwt.py`**: Handles JWT (JSON Web Token) creation, verification, and password hashing/verification.

### `app/integrations/`

Contains modules for integrating with external services.

*   **`__init__.py`**: Makes the `integrations` directory a Python package.
*   **`aws/`**: Subdirectory for AWS service integrations.
    *   **`__init__.py`**: Makes the `aws` subdirectory a Python package.
    *   **`service_communicator.py`**: Contains the `AWSServiceCommunicator` class for interacting with AWS services like S3, SQS, and SNS.

### `app/models/`

Defines SQLAlchemy ORM models, representing database tables.

*   **`__init__.py`**: Makes the `models` directory a Python package.
*   **`user.py`**: Defines the SQLAlchemy model for the `User` table, including its columns and relationships.

### `app/repository/`

Contains data access logic (CRUD operations). These modules interact directly with the database via SQLAlchemy models and sessions.

*   **`__init__.py`**: Makes the `repository` directory a Python package.
*   **`user.py`**: Implements database operations for the `User` model (e.g., `create_user`, `get_user_by_email`).

### `app/schemas/`

Defines Pydantic models used for data validation, serialization, and API request/response bodies.

*   **`__init__.py`**: Makes the `schemas` directory a Python package.
*   **`user.py`**: Defines Pydantic schemas for user-related data (e.g., `UserCreate` for registration, `UserRead` for responses, `UserLogin`, `Token`).

### `app/services/`

Contains business logic modules. Services orchestrate operations by using repositories and other services.

*   **`__init__.py`**: Makes the `services` directory a Python package.
*   **`user.py`**: Likely contains business logic related to user operations, potentially calling methods from `app/repository/user.py`.

## `logs/`

Directory for storing application log files.

*   **`app.log`**: The main application log file where runtime information, errors, and debug messages are written. (This file might be gitignored in a production setup).

---

This structure promotes separation of concerns and modularity, making the application easier to understand, maintain, and scale.