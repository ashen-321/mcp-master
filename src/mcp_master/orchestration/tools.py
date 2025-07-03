from openai import OpenAI
from config import ConfigError


# --------------------------------------------------------------------------------------------
# Helper Functions ---------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------


def openai_url_invoke(model_id: str, user_query: str, prompt: str,
                      system_prompt: str = 'You are a seasoned expert.', service_url: str = '', max_token: int = 10240,
                      temperature: float = 0.05, top_p: float = 0.9):
    if model_id is None:
        raise ConfigError('Ensure your judge_model_id is properly configured via set_config().')
    if service_url is None:
        raise ConfigError('Ensure your judge_model_service_url is properly configured via set_config().')


    print(f'Invoking model "{model_id}" from "{service_url}"...')

    client = OpenAI(
        base_url=service_url,
    )

    chat_response = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": f'{system_prompt} Question: {user_query}'},
            {"role": "user", "content": prompt}
        ],
        stream=False,
        temperature=temperature,
        max_tokens=max_token,
        top_p=top_p
    )

    footer = f'Completion_tokens: {chat_response.usage.completion_tokens}, Prompt_tokens: {chat_response.usage.prompt_tokens},  Total_tokens:{chat_response.usage.total_tokens}'
    return chat_response.choices[0].message.content, footer
