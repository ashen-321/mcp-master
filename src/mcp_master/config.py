gconfig = {
    'judge_model_id': None,
    'judge_model_service_url': None,
    'OPENAI_API_KEY': None,
    'OPENAI_BASE_URL': None,
}


def set_config(options: dict):
    for key in options:
        gconfig[key] = options[key]


class ConfigError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
