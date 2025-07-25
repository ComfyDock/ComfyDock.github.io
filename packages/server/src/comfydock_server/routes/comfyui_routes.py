from fastapi import APIRouter, HTTPException
from comfydock_core.comfyui_integration import check_comfyui_path, try_install_comfyui
import logging

router = APIRouter(prefix="/comfyui", tags=["comfyui"])
logger = logging.getLogger(__name__)


@router.post("/validate-path")
def validate_path_endpoint(obj: dict):
    """
    Check if the provided path contains a valid ComfyUI installation.
    """
    try:
        logger.info(f"Validating path: {obj['path']}")
        valid_path = check_comfyui_path(obj["path"])
        logger.info(f"Valid path: {valid_path}")
        return {"valid_comfyui_path": str(valid_path)}
    except Exception as e:
        logger.error(f"Error validating path: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Path validation failed",
                "error": str(e),
                "path": obj.get("path", "")
            }
        )


@router.post("/install")
def install_comfyui_endpoint(obj: dict):
    """
    Attempt to install (clone) ComfyUI into the given path if no valid installation exists.
    """
    try:
        if "branch" not in obj:
            obj["branch"] = "master"
        path = try_install_comfyui(obj["path"], obj["branch"])
        return {"status": "success", "path": path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))