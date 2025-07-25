from fastapi import APIRouter, Depends, HTTPException, Query
from comfydock_core.environment import Environment, EnvironmentUpdate
from comfydock_core.docker_interface import DockerInterfaceContainerNotFoundError
from .dependencies import get_env_manager, get_user_settings_manager
from dateutil import parser as dateutil_parser
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/environments", tags=["environments"])


@router.post("", response_model=dict)
async def create_environment(env: Environment, env_manager=Depends(get_env_manager)):
    try:
        new_env = env_manager.create_environment(env)
        return {"status": "success", "container_id": new_env.id}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/{env_id}/duplicate")
async def duplicate_environment(
    env_id: str, env: Environment, env_manager=Depends(get_env_manager)
):
    """
    Duplicate an environment – note that duplication is only allowed after activation.
    """
    try:
        new_env = env_manager.duplicate_environment(env_id, env)
        return {"status": "success", "container_id": new_env.id}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.delete("/{env_id}")
async def delete_environment(
    env_id: str,
    env_manager=Depends(get_env_manager),
    user_settings_manager=Depends(get_user_settings_manager),
):
    """
    Delete an environment. If it’s not already soft-deleted (i.e. in the "deleted" folder)
    then it will be soft-deleted; otherwise it will be removed completely.
    """
    try:
        user_settings = user_settings_manager.load()
        deleted_id = env_manager.delete_environment(
            env_id, user_settings.max_deleted_environments
        )
        return {"status": "success", "id": deleted_id}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/{env_id}/status")
def get_environment_status(env_id: str, env_manager=Depends(get_env_manager)):
    """
    Get the current status of an environment.
    """
    try:

        env = env_manager.get_environment(env_id)
        return {"status": env.status}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("", response_model=list)
def list_environments(
    folderId: str = Query(None), env_manager=Depends(get_env_manager)
):
    try:
        return env_manager.load_environments(folderId)
    except Exception as e:
        raise HTTPException(500, str(e))


@router.put("/{env_id}")
async def update_environment(
    env_id: str, update: EnvironmentUpdate, env_manager=Depends(get_env_manager)
):
    """
    Update an environment’s name and/or folderIds.
    """
    try:
        env = env_manager.update_environment(env_id, update)
        return {"status": "success", "container_id": env.id}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/{env_id}/activate")
async def activate_environment(
    env_id: str,
    allow_multiple: bool = Query(
        False, description="Allow multiple environments running concurrently"
    ),
    env_manager=Depends(get_env_manager),
):
    """
    Activate an environment (start its Docker container). By default, this stops any
    other running containers unless allow_multiple is set to True.
    """
    try:
        env = env_manager.activate_environment(env_id, allow_multiple)
        return {"status": "success", "container_id": env.id}
    except Exception as e:
        print(f"Error activating environment {env_id}: {e}")
        raise HTTPException(500, str(e))


@router.post("/{env_id}/deactivate")
async def deactivate_environment(env_id: str, env_manager=Depends(get_env_manager)):
    """
    Deactivate (stop) an environment’s Docker container.
    """
    try:
        env = env_manager.deactivate_environment(env_id)
        return {"status": "success", "container_id": env.id}
    except Exception as e:
        print(f"Error deactivating environment {env_id}: {e}")
        raise HTTPException(500, str(e))


@router.get("/{env_id}/logs")
def stream_container_logs(env_id: str, env_manager=Depends(get_env_manager)):
    """
    Stream logs from a running container.
    """
    try:
        container = env_manager.docker_iface.get_container(env_id)
        if container.status != "running":
            raise HTTPException(400, "Container is not running.")
        container_start_time = dateutil_parser.parse(
            container.attrs["State"]["StartedAt"]
        )

        def log_generator():
            for log in container.logs(stream=True, since=container_start_time):
                yield f"data: {log.decode('utf-8')}\n\n"

        return StreamingResponse(log_generator(), media_type="text/event-stream")
    except DockerInterfaceContainerNotFoundError:
        raise HTTPException(404, "Container not found.")
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/{env_id}/commit")
async def commit_environment(env_id: str,
                            repo_name: str = Query(..., description="The name of the repository to commit to"), 
                            tag_name: str = Query(..., description="The tag name to commit to"), 
                            env_manager=Depends(get_env_manager)):
    """
    Commit an environment to a new image.
    """
    try:
        print(f"Committing environment {env_id} to {repo_name}:{tag_name}")
        container = env_manager.docker_iface.get_container(env_id)
        print(f"Container: {container}")
        env = env_manager.docker_iface.commit_container(container, repo_name, tag_name)
        return {"status": "success", "container_id": env.id}
    except DockerInterfaceContainerNotFoundError:
        raise HTTPException(404, "Container not found.")
    except Exception as e:
        raise HTTPException(500, str(e))
