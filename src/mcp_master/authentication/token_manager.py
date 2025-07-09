import secrets
from typing import Optional
import logging
from datetime import datetime, timedelta, UTC
from time import time, sleep
from token_class import Token


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class TokenManager:
    env_path: str
    tokens: dict

    def __init__(self, env_path: Optional[str] = None):
        # File to read tokens from, defaulted to ../../../.tokens
        self.env_path = env_path or '../../../.tokens'

        # Dictionary of all tokens
        self.tokens = {}

        # Read tokens to sync self.tokens to all saved tokens
        self.read_tokens()

    def generate_token(self, time_until_expired: Optional[dict] = None, permissions: int = 0):
        expiry_date = None
        if time_until_expired is not None:
            now = datetime.now(UTC)
            expiry_date = now + timedelta(**time_until_expired)

            logging.info(f'Generated token wth permission level {permissions} that will expire on {expiry_date} UTC.')
        else:
            logging.info(f'Generated token wth permission level {permissions} that will not expire.')

        token_str = f'mcpm_{secrets.token_urlsafe()}'
        token = Token(token_str, expiry_date, permissions)
        self.tokens[token_str] = token

    def validate_token(self, token: Token):
        if token.token not in self.tokens:
            logging.warning(f'User attempted to validate with nonexistent token {token.token}.')
            return

        if 0 <= token.expiration < time():
            logging.warning(f'User attempted to validate with expired token {token.token}.')
            self.tokens.pop(token.token)
            return

    def read_tokens(self):
        # Read all tokens from .tokens
        with open(self.env_path, 'r') as env:
            for token in env.readlines():
                token_data = token.split()

                # Discard tokens that are expired
                expiration_seconds = int(token_data[1])
                if 0 <= expiration_seconds < time():
                    logging.info(f'Token {token_data[0]} has expired.')
                    continue

                # Save non-expired tokens as Token objects
                self.tokens[token_data[0]] = Token(*token_data)

    def write_tokens(self):
        # Write all tokens to .tokens
        with open(self.env_path, 'w') as env:
            for token in self.tokens.values():
                env.write(str(token))


tm = TokenManager()
tm.generate_token({'minutes': 1})
tm.write_tokens()
print(tm.tokens)
