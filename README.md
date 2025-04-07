# Serverless Function Execution Platform

This project implements a serverless function execution platform, similar to AWS Lambda, allowing users to deploy and execute functions on-demand via HTTP requests. It supports Python and JavaScript functions and utilizes Docker and gVisor for virtualization.

## Prerequisites

* **Python:** Python 3.6 or later is required.
    * Check your version: `python3 --version` or `python --version`
* **Docker:** Docker must be installed and running.
    * Installation: [https://www.docker.com/get-started/](https://www.docker.com/get-started/)
* **gVisor (Optional, for full functionality):**
    * Follow the official installation guide: [https://gvisor.dev/docs/user\_guide/install/](https://gvisor.dev/docs/user_guide/install/)
    * Ensure the `runsc` runtime is correctly configured.

## Setup Instructions

1.  **Clone the Repository:**

    ```bash
    git clone https://github.com/adityagirishh/week2_CC.git
    cd https://github.com/adityagirishh/week2_CC.git
    ```

2.  **Create and Activate a Virtual Environment (Recommended):**

    ```bash
    python3 -m venv venv  # Create the virtual environment
    source venv/bin/activate  # Activate on Linux/macOS
    # venv\Scripts\activate  # Activate on Windows
    ```

3.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Build Docker Base Images:**

    ```bash
    docker build -t python-base ./docker/python/
    docker build -t nodejs-base ./docker/nodejs/
    ```

## Running the Application

1.  **Start the API Server:**

    ```bash
    python app/main.py
    # Or, for automatic reloading on changes (development):
    # uvicorn app.main:app --reload
    ```

    The server will typically start at `http://localhost:8000`.

## API Usage

You can interact with the API using tools like `curl`, Postman, or any HTTP client.

### Function Management

* **Create a Function:**

    * `POST /functions/`
    * Request Body (JSON):

        ```json
        {
            "name": "my_function",
            "route": "/my-function",
            "language": "python",
            "code": "def handler(event, context):\n    return {'message': f'Hello, {event.get(\"name\", \"World\")}'}",
            "timeout": 5
        }
        ```

    * Response: JSON representation of the created function.

* **Get All Functions:**

    * `GET /functions/`
    * Response: JSON array of function objects.

* **Get a Function by ID:**

    * `GET /functions/{function_id}` (e.g., `/functions/1`)
    * Response: JSON representation of the function.

* **Update a Function:**

    * `PUT /functions/{function_id}` (e.g., `/functions/1`)
    * Request Body (JSON):

        ```json
        {
            "name": "updated_function",
            "route": "/updated-function",
            "language": "python",
            "code": "def handler(event, context):\n    return {'message': 'Updated function'}",
            "timeout": 10
        }
        ```

    * Response: JSON representation of the updated function.

* **Delete a Function:**

    * `DELETE /functions/{function_id}` (e.g., `/functions/1`)
    * Response: `{"message": "Function deleted"}`

### Function Execution

* **Execute Function (Docker):**

    * `POST /execute/{function_name}` (e.g., `/execute/my_function`)
    * Request Body (JSON):

        ```json
        {
            "event": {"name": "User"}
        }
        ```

    * Response: `{"result": "Function output"}`

* **Execute Function (gVisor):**

    * `POST /execute_gvisor/{function_name}` (e.g., `/execute_gvisor/my_function`)
    * Request Body (JSON):

        ```json
        {
            "event": {"name": "gVisorUser"}
        }
        ```

    * Response: `{"result": "Function output"}`

### Metrics

* **Get All Metrics:**

    * `GET /metrics/`
    * Response: JSON array of metric objects.

### Example Usage (curl)

```bash
    # Create a function
    curl -X POST -H "Content-Type: application/json" -d \
    '{
        "name": "test_curl_func",
        "route": "/curl_test",
        "language": "python",
        "code": "def handler(event, context):\n    return {\"message\": \"Hello from curl\"}",
        "timeout": 5
    }' http://localhost:8000/functions/

    # Execute the function (Docker)
    curl -X POST -H "Content-Type: application/json" -d \
    '{"event": {}}' http://localhost:8000/execute/test_curl_func

    # Execute the function (gVisor)
    curl -X POST -H "Content-Type: application/json" -d \
    '{"event": {}}' http://localhost:8000/execute_gvisor/test_curl_func

    # Get metrics
    curl http://localhost:8000/metrics/
