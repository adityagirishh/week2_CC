import docker
import tempfile
import os
import asyncio
import logging
from fastapi import HTTPException

client = docker.from_env()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

container_pool = {
    "python": [],
    "javascript": []
}
POOL_SIZE = 2

async def initialize_container_pool():
    for language in container_pool:
        for _ in range(POOL_SIZE):
            container = await _create_container(language)
            container_pool[language].append(container)
            logging.info(f"Pre-warmed {language} container created.")

async def _create_container(language: str):
    if language == "python":
        image_name = "python-base"
    elif language == "javascript":
        image_name = "nodejs-base"
    else:
        raise ValueError(f"Unsupported language: {language}")

    container = client.containers.create(
        image=image_name,
        command=["sleep", "3600"],
        working_dir="/app",
        detach=True,
        mem_limit="128m"
    )
    container.start()
    return container

async def _execute_in_container(container, function_code: str, language: str, timeout: int):
    suffix = ".py" if language == "python" else ".js"
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as temp_file:
            temp_file.write(function_code)
            temp_filepath = temp_file.name

        filename = os.path.basename(temp_filepath)
        container.put_archive('/app', _pack_code_to_tar(temp_filepath, filename))

        cmd = ["python", f"/app/{filename}"] if language == "python" else ["node", f"/app/{filename}"]

        exec_id = container.client.api.exec_create(container.id, cmd, workdir="/app")
        output = container.client.api.exec_start(exec_id, detach=False, tty=False, stream=False, demux=False)

        exec_info = container.client.api.exec_inspect(exec_id)
        if exec_info['ExitCode'] != 0:
            raise RuntimeError(f"Function execution failed: {output.decode('utf-8')}")

        return output.decode('utf-8')

    except Exception as e:
        logging.error(f"Error executing in container: {e}")
        raise
    finally:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)

def _pack_code_to_tar(filepath, filename):
    import tarfile
    import io

    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode='w') as tar:
        tar.add(filepath, arcname=filename)
    tar_stream.seek(0)
    return tar_stream.read()

async def execute_function(function_code: str, language: str, timeout: int):
    container = None
    try:
        if not container_pool[language]:
            container = await _create_container(language)
            logging.warning("No pre-warmed container available. Created a new one.")
        else:
            container = container_pool[language].pop(0)
            logging.info("Using a pre-warmed container.")

        result = await asyncio.wait_for(
            _execute_in_container(container, function_code, language, timeout),
            timeout=timeout
        )

        container_pool[language].append(container)
        return result

    except asyncio.TimeoutError:
        if container:
            container.kill()
        raise HTTPException(status_code=408, detail="Function execution timed out.")
    except docker.errors.ImageNotFound as e:
        raise ValueError(f"Base image not found: {e}")
    except docker.errors.APIError as e:
        raise RuntimeError(f"Docker API error: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {e}")
    finally:
        if container and container.status != "running":
            try:
                container.remove()
            except Exception:
                pass

# Attach this to your FastAPI app
# app.add_event_handler("startup", startup_event)

async def startup_event():
    await initialize_container_pool()
