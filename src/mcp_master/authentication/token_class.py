from typing import Optional
from datetime import datetime


class Token:
    def __init__(self, token: str, expiration: Optional[datetime | str | int], permissions: int | str):
        # Type check the token string
        if not isinstance(token, str):
            raise ValueError(f'Attempted to generate token {token} which must be a str, not {type(token)}.')

        # Type check the expiration time and attempt to convert to seconds since epoch
        if isinstance(expiration, datetime):
            expiration = int(expiration.timestamp())
        elif isinstance(expiration, str):
            try:
                expiration = int(expiration)
            except ValueError:
                raise ValueError(f'Attempted to generate token with expiration {expiration}, which is an invalid int() literal.')
        elif expiration is not None and not isinstance(expiration, int):
            raise ValueError(f'Attempted to generate token with expiration {expiration} which must be an int, valid int() literal, or datetime object, not {type(expiration)}.')

        # Type check the permissions level and attempt to convert to int
        if isinstance(permissions, str):
            try:
                permissions = int(permissions)
            except ValueError:
                raise ValueError(
                    f'Attempted to generate token with permissions {permissions}, which is an invalid int() literal.')
        elif not isinstance(permissions, int):
            raise ValueError(f'Attempted to generate token with permissions {permissions} which must be an int, not {type(permissions)}.')

        # Store values
        self.token = token
        self.expiration = expiration or -1
        self.permissions = permissions

    def __str__(self):
        # Return a form ready to be written to .tokens
        return f'{self.token} {self.expiration} {self.permissions}\n'