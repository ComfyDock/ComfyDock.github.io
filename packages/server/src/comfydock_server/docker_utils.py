from comfydock_core.docker_interface import DockerInterface, DockerInterfaceError, DockerInterfaceContainerNotFoundError
from .config import AppConfig
import logging

logger = logging.getLogger(__name__)

class DockerManager:
    def __init__(self, config: AppConfig):
        self.config = config
        self.docker_interface = DockerInterface()
        logger.debug("DockerManager initialized with config: %s", config)

    def start_frontend(self):
        """Start the frontend container using core DockerInterface"""
        image_name = self.config.frontend.image
        logger.info("Starting frontend container with image: %s", image_name)
        
        # First check if the image exists, if not, pull it
        logger.debug("Checking if image %s exists locally or needs to be pulled", image_name)
        self.docker_interface.try_pull_image(image_name)
        logger.debug("Image %s is available", image_name)
        
        try:
            # Use core library's container retrieval
            logger.debug("Checking if container %s already exists", self.config.frontend.container_name)
            container = self.docker_interface.get_container(self.config.frontend.container_name)
            
            # Use core library's status check and start mechanism
            if container.status != 'running':
                logger.info("Container %s exists but is not running. Starting it...", 
                        self.config.frontend.container_name)
                self.docker_interface.start_container(container)
                logger.info("Container %s started successfully", self.config.frontend.container_name)
            else:
                logger.info("Container %s is already running", self.config.frontend.container_name)
                
        except DockerInterfaceContainerNotFoundError:
            # Use core library's container run method
            logger.info("Container %s not found. Creating and starting new container...", 
                    self.config.frontend.container_name)
            self.docker_interface.run_container(
                image=image_name,
                name=self.config.frontend.container_name,
                ports={f'{self.config.frontend.container_port}/tcp': self.config.frontend.default_host_port},
                environment={
                    "VITE_API_BASE_URL": f"http://{self.config.backend.host}:{self.config.backend.port}",
                    "VITE_API_WS_URL": f"ws://{self.config.backend.host}:{self.config.backend.port}/ws",
                },
                detach=True,
                remove=True
            )
            logger.info("Container %s created and started successfully on port %s", 
                    self.config.frontend.container_name, self.config.frontend.default_host_port)

    def stop_frontend(self):
        """Stop the frontend container using core DockerInterface"""
        logger.info("Attempting to stop frontend container: %s", self.config.frontend.container_name)
        try:
            container = self.docker_interface.get_container(self.config.frontend.container_name)
            logger.debug("Container %s found, stopping it...", self.config.frontend.container_name)
            self.docker_interface.stop_container(container)
            logger.info("Container %s stopped successfully", self.config.frontend.container_name)
        except DockerInterfaceContainerNotFoundError:
            logger.info("Container %s not found, nothing to stop", self.config.frontend.container_name)
            pass
        except DockerInterfaceError as e:
            logger.warning("Error stopping frontend container %s: %s", 
                        self.config.frontend.container_name, str(e))
            pass
        except Exception as e:
            logger.error("Error stopping frontend container %s: %s", 
                        self.config.frontend.container_name, str(e))
            raise e
