# Capstone Project

## Version Information

* **Python:** 3.13.3
* **FastAPI:** 0.115.12

## Installation

### 1. Create a Virtual Environment

Create a Python virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment:

**Windows (Git Bash):**

```bash
source venv/Scripts/activate
```

**Windows (CMD):**

```cmd
venv\Scripts\activate
```

**Linux / macOS:**

```bash
source venv/bin/activate
```

### 2. Install Dependencies

#### Install FastAPI

```bash
pip install "fastapi[all]"
```

#### Install Sentence Transformers

```bash
pip install -U sentence-transformers
```

#### Install All Project Dependencies

Alternatively, install all project dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3. Database Setup

This project uses **PostgreSQL**.

Create the database:

```sql
CREATE DATABASE cv_evaluator_db;
```

### 4. Test Database Connection

Run the database connection test:

```bash
python -m tests.test_db
```

## Database Migration

### 1. Import Models

Make sure all models are imported in:

```text
alembic/env.py
```

For example:

```python
from app.models import resume, job, evaluation
```

Update the import statement whenever new models are added.

### 2. Create a Migration

Generate a migration based on the current models:

```bash
alembic revision --autogenerate -m "init tables"
```

### 3. Apply Migration

Apply the migration and create or update database tables:

```bash
alembic upgrade head
```

### 4. Check Current Migration

Check the current database migration version:

```bash
alembic current
```

### 5. Update the Database After Modifying Models

Whenever you modify an existing model or add a new model, generate a new migration:

```bash
alembic revision --autogenerate -m "describe your changes"
```

Then apply the migration:

```bash
alembic upgrade head
```

> **Note:** After modifying models, you do not need to manually modify the database schema. Generate and apply an Alembic migration instead.

## Run the Application

Start the FastAPI development server:

```bash
uvicorn app.main:app --reload --port 8080
```

The application will be available at:

* **API:** http://localhost:8080
* **Swagger UI:** http://localhost:8080/docs

## Swagger API Documentation

Open Swagger UI:

**http://localhost:8080/docs**
