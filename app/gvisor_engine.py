import docker
import tempfile
import os
import asyncio
import logging
from fastapi import HTTPException

client = docker.from_env()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def execute_function_gvisor(function_code: str, language: str, timeout: int):
    """
    Executes the given function code inside a gVisor sandbox.
    """
    try:
        if language == "python":
            image_name = "python-base"
            suffix = ".py"
            cmd = ["python", "/app/user_function.py"]
        elif language == "javascript":
            image_name = "nodejs-base"
            suffix = ".js"
            cmd = ["node", "/app/user_function.js"]
        else:
            raise ValueError(f"Unsupported language: {language}")

        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=True) as temp_file:
            temp_file.write(function_code)
            temp_file.flush()  # Ensure the file is written before Docker mounts it
            temp_filepath = temp_file.name

            container = client.containers.run(
                image=image_name,
                command=cmd,
                runtime="runsc",  # Use gVisor runtime
                volumes={temp_filepath: {
                    'bind': '/app/user_function.py' if language == "python" else '/app/user_function.js',
                    'mode': 'ro'
                }},
                working_dir="/app",
                detach=True,
                mem_limit="128m"
            )

            start_time = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start_time < timeout:
                container.reload()
                if container.status == 'exited':
                    break
                await asyncio.sleep(0.1)

            if container.status != 'exited':
                container.stop()
                container.remove()
                raise TimeoutError(f"Function execution timed out after {timeout} seconds")

            result = container.logs().decode('utf-8')
            container.remove()
            return result

    except docker.errors.ImageNotFound as e:
        raise ValueError(f"Base image not found: {e}")
    except docker.errors.ContainerError as e:
        raise RuntimeError(f"Container execution failed: {e}")
    except docker.errors.APIError as e:
        raise RuntimeError(f"Docker API error: {e}")
    except TimeoutError as e:
        raise HTTPException(status_code=408, detail=str(e))
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {e}")
