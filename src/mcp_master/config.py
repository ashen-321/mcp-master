import os
from pydantic import BaseModel
from typing import Optional


class GlobalConfig(BaseModel):
    # Tool selection model ID
    selector_model_id: str = ''

    # Selection judge model ID
    judge_model_id: str = ''

    # Judge service URL
    judge_model_service_url: str = ''

    # OpenAI API Key
    OPENAI_API_KEY: str = ''

    # OpenAI Base URL
    OPENAI_BASE_URL: Optional[str] = None

    # Autostart path for locally available servers, defaulted to ../../../examples/demo-servers
    autostart_abspath: str = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', '..', 'examples', 'demo-servers')
    )

    # Whether a token is required for access
    private: bool = False


global_config = GlobalConfig()


class ConfigError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
