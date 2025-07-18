from pydantic import BaseModel


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
    OPENAI_BASE_URL: str | None = None

    # Autostart path for locally available servers, defaulted to ../../../examples/demo-servers
    autostart_abspath: str | None = None


global_config = GlobalConfig()


class ConfigError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
