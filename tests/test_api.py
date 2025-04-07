from fastapi.testclient import TestClient
from app.main import app
from app.models import database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.models import Base

client = TestClient(app)

# Set up an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(TEST_DATABASE_URL, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[database.SessionLocal] = override_get_db

@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=test_engine)

@app.on_event("shutdown")
async def shutdown():
    Base.metadata.drop_all(bind=test_engine)

def test_create_function():
    response = client.post(
        "/functions/",
        json={
            "name": "test_function",
            "route": "/test",
            "language": "python",
            "code": "def handler(event, context): return {'message': 'Hello'}",
            "timeout": 5
        },
    )
    assert response.status_code == 201
    assert response.json()["name"] == "test_function"

def test_read_functions():
    response = client.get("/functions/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_read_function():
    response = client.get("/functions/1")  # Assuming function with ID 1 exists
    assert response.status_code == 200
    assert response.json()["name"] == "test_function"

def test_update_function():
    response = client.put(
        "/functions/1",  # Assuming function with ID 1 exists
        json={
            "name": "updated_function",
            "route": "/updated",
            "language": "python",
            "code": "def handler(event, context): return {'message': 'Updated'}",
            "timeout": 10
        },
    )
    assert response.status_code == 200
    assert response.json()["name"] == "updated_function"

def test_delete_function():
    response = client.delete("/functions/1")  # Assuming function with ID 1 exists
    assert response.status_code == 200
    assert response.json() == {"message": "Function deleted"}

def test_execute_function():
    # First, create a function
    create_response = client.post(
        "/functions/",
        json={
            "name": "exec_test",
            "route": "/exec",
            "language": "python",
            "code": "def handler(event, context):\n    return {'message': f'Hello, {event.get(\"name\", \"World\")}'}",
            "timeout": 5
        },
    )
    assert create_response.status_code == 201

    # Then, execute it
    execute_response = client.post(
        "/execute/exec_test",
        json={"event": {"name": "Test"}},
    )
    assert execute_response.status_code == 200
    assert "Hello, Test" in execute_response.json()["result"]

def test_execute_function_gvisor():
    # First, create a function
    create_response = client.post(
        "/functions/",
        json={
            "name": "exec_test_gvisor",
            "route": "/exec_gvisor",
            "language": "python",
            "code": "def handler(event, context):\n    return {'message': f'Hello from gVisor, {event.get(\"name\", \"World\")}'}",
            "timeout": 5
        },
    )
    assert create_response.status_code == 201

    # Then, execute it with gVisor
    execute_response = client.post(
        "/execute_gvisor/exec_test_gvisor",
        json={"event": {"name": "gVisorTest"}},
    )
    assert execute_response.status_code == 200
    assert "Hello from gVisor, gVisorTest" in execute_response.json()["result"]

def test_read_metrics():
    # Assuming metrics are being created during function execution tests
    response = client.get("/metrics/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
