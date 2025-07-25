from fastapi import APIRouter, Depends, HTTPException
from comfydock_core.user_settings import UserSettings, UserSettingsNotFoundError
from .dependencies import get_user_settings_manager, get_env_manager, get_config
from ..config import AppConfig
router = APIRouter(prefix="/user-settings", tags=["user_settings"])

import logging

logger = logging.getLogger(__name__)

@router.get("", response_model=UserSettings)
def get_user_settings(user_settings_manager=Depends(get_user_settings_manager)):
    try:
        logger.debug("Getting user settings")
        return user_settings_manager.load()
    except UserSettingsNotFoundError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))


@router.put("")
def update_user_settings(
    settings: UserSettings, user_settings_manager=Depends(get_user_settings_manager)
):
    try:
        logger.debug("Updating user settings")
        user_settings_manager.save(settings)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/folders")
def create_folder(
    folder_data: dict,
    user_settings_manager=Depends(get_user_settings_manager),
    config: AppConfig = Depends(get_config),
):
    """
    Create a new folder. Expects a JSON payload with a "name" key.
    """
    try:
        folder_name = folder_data["name"]
        logger.debug(f"Creating folder: {folder_name}")
        settings = user_settings_manager.load()
        updated_settings = user_settings_manager.create_folder(settings, folder_name)
        user_settings_manager.save(updated_settings)
        new_folder = next(f for f in updated_settings.folders if f.name == folder_name)
        logger.debug(f"Folder created: {new_folder.id}, {new_folder.name}")
        return {"id": new_folder.id, "name": new_folder.name}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))


@router.put("/folders/{folder_id}")
def update_folder(
    folder_id: str,
    folder_data: dict,
    user_settings_manager=Depends(get_user_settings_manager),
    config: AppConfig = Depends(get_config),
):
    """
    Update a folder's name.
    """
    try:
        logger.debug(f"Updating folder: {folder_id}")
        new_name = folder_data["name"]
        settings = user_settings_manager.load()
        updated_settings = user_settings_manager.update_folder(
            settings, folder_id, new_name
        )
        user_settings_manager.save(updated_settings)
        updated_folder = next(f for f in updated_settings.folders if f.id == folder_id)
        logger.debug(f"Folder updated: {updated_folder.id}, {updated_folder.name}")
        return {"id": updated_folder.id, "name": updated_folder.name}
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(404, str(e))
        else:
            raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))


@router.delete("/folders/{folder_id}")
def delete_folder(
    folder_id: str,
    user_settings_manager=Depends(get_user_settings_manager),
    env_manager=Depends(get_env_manager),
):
    """
    Delete a folder. Will fail if any environment is still using this folder.
    """
    try:
        logger.debug(f"Deleting folder: {folder_id}")
        settings = user_settings_manager.load()
        envs = env_manager.load_environments()
        updated_settings = user_settings_manager.delete_folder(settings, folder_id, envs)
        user_settings_manager.save(updated_settings)
        logger.debug(f"Folder deleted: {folder_id}")
        return {"status": "deleted"}
    except ValueError as e:
        raise HTTPException(404, str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(500, str(e))
