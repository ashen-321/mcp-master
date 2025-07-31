import os
from openai import OpenAI
import logging
from asyncio import gather
from pydantic import BaseModel
from typing import Any

from .agent_protocol import MultiAgentState
from ..config import global_config as gconfig
from ..config import ConfigError

# --------------------------------------------------------------------------------------------
# Config -------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Config(BaseModel):
    model_id: str = '',
    tools: list = [],
    master_server_client: Any = None,
    dispatcher_system_message: str = '',


config = Config()

# OpenAI chat client
openai_client = None


# --------------------------------------------------------------------------------------------
# Helper Functions ---------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------


def openai_url_invoke(
        model_id: str,
        user_query: str,
        prompt: str,
        system_prompt: str = 'You are a seasoned expert.',
        service_url: str = '',
        max_token: int = 10240,
        temperature: float = 0.05,
        top_p: float = 0.9
):
    if model_id is None or len(model_id) == 0:
        raise ConfigError('Ensure your judge_model_id is properly configured via set_config().')
    if service_url is None or len(service_url) == 0:
        raise ConfigError('Ensure your judge_model_service_url is properly configured via set_config().')

    logging.info(f'Invoking model "{model_id}" from "{service_url}"...')

    client = OpenAI(base_url=service_url)

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

    return chat_response.choices[0].message.content


# --------------------------------------------------------------------------------------------
# Deployment Nodes ---------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------


async def tools_selector_node(state: MultiAgentState):
    global openai_client

    logging.info(f'Selecting tools from {[tool['function']['name'] for tool in config.tools]}...')

    # Exit for invalid selector_model_id values
    config.model_id = gconfig.selector_model_id
    if config.model_id is None or len(config.model_id) == 0:
        raise ConfigError(f'Ensure your selector_model_id is properly configured via set_config(). It is currently {config.model_id}.')

    # Exit for invalid API key
    if gconfig.OPENAI_API_KEY is None or len(gconfig.OPENAI_API_KEY) == 0:
        raise ConfigError(f'Ensure your OPENAI_API_KEY is properly configured via set_config(). It is currently {gconfig.OPENAI_API_KEY}.')
    os.environ["OPENAI_API_KEY"] = gconfig.OPENAI_API_KEY

    # Exit for empty API key
    if gconfig.OPENAI_BASE_URL is not None:
        if len(gconfig.OPENAI_BASE_URL) == 0:
            raise ConfigError(f'Ensure your OPENAI_BASE_URL is properly configured via set_config(). It is currently empty.')

        # Save API key to environment variables
        os.environ["OPENAI_BASE_URL"] = gconfig.OPENAI_BASE_URL

    # Exit for no tools available
    if len(config.tools) == 0:
        raise Exception('No tools available to make selections from. Ensure sub-servers exist and are functioning properly.')

    # Initialize openAI chat client on first run
    if openai_client is None:
        openai_client = OpenAI()

    # Initialize message history on each new query
    if len(state.messages) == 0:
        state.messages = [
            {"role": "system", "content": config.dispatcher_system_message},
            {"role": "user", "content": state.question},
        ]

    # Select tools
    response = openai_client.chat.completions.create(
        model=config.model_id,
        max_tokens=3000,
        messages=state.messages,
        tools=config.tools
    )

    tool_calls = response.choices[0].message.tool_calls
    logging.info(f'Selected tools: {tool_calls}')

    # Call selected tools
    if tool_calls:
        tool_callables = [
            config.master_server_client.call_tool(
                tool.function.name, eval(tool.function.arguments)
            )
            for tool in tool_calls
        ]

        results = await gather(*tool_callables)
        external_data = [result.content[0].text for result in results]

        # Save tool response to messages
        state.messages.append({"role": "assistant", "content": str(external_data)})

        logging.info(f'Tool results: {external_data}')
        return {'tools_requested': tool_calls, 'external_data': external_data}

    # Safety in case the model chooses to generate its own response
    response = response.choices[0].message.content

    # Save AI response to messages
    state.messages.append({"role": "assistant", "content": response})

    logging.info(f'Model-generated response: {response}')
    return {'tools_requested': None, 'external_data': [response]}


def judge_node(state: MultiAgentState):
    logging.info(f'Judging response...')
    # Answers:
    # GOOD - send to client
    # BAD - try again

    decision = openai_url_invoke(
        gconfig.judge_model_id,
        state.question,
        str(state.external_data),
        'You are a seasoned expert. Your role is to determine the quality of the answer generated by '
        'a team of other AI models. Output "GOOD" if the response answers the question and matches '
        'real world consensus, otherwise output "BAD". Do not output anything else besides those two '
        'options. Output in all capital letters.',
        gconfig.judge_model_service_url,
    )
    decision = decision.strip().upper()
    logging.info(f'Judge decision: {decision}')

    # Exit if the answer is good
    if 'GOOD' in decision.upper():
        return {'qa_assessment': decision}

    # Give judge feedback if the answer is bad
    feedback = openai_url_invoke(
        gconfig.judge_model_id,
        state.question,
        str(state.external_data),
        'You are a seasoned expert. Your role is to determine the quality of the answer generated by a team of other '
        'AI models. You have decided that the provided answer was BAD. Provide detailed and specific examples as to '
        'why you made this decision, so other AI models can try again to produce a more accurate result.',
        gconfig.judge_model_service_url,
    )

    # Save judge feedback to message history (no need to save if it's good)
    state.messages.append({"role": "assistant", "content": f"Bad answer - {feedback}"})

    logging.info(f'Judge feedback: {feedback}')
    return {'qa_assessment': decision, 'qa_feedback': feedback}


def judge_decision(state: MultiAgentState):
    logging.info(f'Routing judge decision...')

    return state.qa_assessment
