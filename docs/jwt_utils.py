from functools import wraps
from http import HTTPStatus

from flask import current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

from http_utils import ResponseError


def jwt_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            if not user_id:
                raise ResponseError(status=HTTPStatus.FORBIDDEN, message="No user_id in token")
            kwargs["user_id"] = user_id
            return current_app.ensure_sync(fn)(*args, **kwargs)

        return decorator

    return wrapper
