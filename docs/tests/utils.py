import uuid
from datetime import datetime, timedelta

import jwt

from app import get_config


def generate_token(pk: uuid.UUID, expires: int = 24 * 3_600):
    dt = datetime.now() + timedelta(seconds=expires)
    token = jwt.encode(
        {
            "id": str(pk),
            "action": "login",
            "exp": int(dt.strftime("%s")),
        },
        open(get_config()["JWT_PRIVATE_KEY_PATH"]).read(),
        algorithm="RS256",
    )
    return token


def get_file(filename: str):
    return open(f'static/tests/{filename}', 'rb'), filename  # TODO create image
