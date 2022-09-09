from urllib import parse

from flask import request
from flask_sqlalchemy import BaseQuery
from pydantic import BaseModel

from extensions import db


def paginate(query: BaseQuery, url: str, parsed_query: dict) -> dict:
    count = query.count()
    limit = parsed_query["limit"]
    offset = parsed_query["offset"]
    order = parsed_query["order"]
    other_params = {
        **parsed_query["filtering"],
        **({"order": order} if order else {}),
    }

    previous_offset = max(0, offset - limit)
    previous_params = {
        **({"offset": previous_offset} if previous_offset else {}),
        "limit": limit,
        **other_params,
    } if offset else {}

    next_offset = offset + limit
    next_params = {
        "offset": next_offset,
        "limit": limit,
        **other_params,
    } if next_offset < count else {}

    full_url = f"{request.scheme}://{request.host}{url}"
    return {
        "count": count,
        "next": f"{full_url}?{parse.urlencode(next_params)}" if next_params else None,
        "previous": f"{full_url}?{parse.urlencode(previous_params)}" if previous_params else None,
        "results": [i.serialize for i in query.limit(limit).offset(offset).all()],
    }


def get_ordering(order_request, ordering_fields: list, model):
    ordering = []
    if order_request:
        for field in ordering_fields:
            if f"-{field}" in order_request:
                ordering.append(getattr(model, field).desc())
            elif field in order_request:
                ordering.append(getattr(model, field))
    return ordering


def parse_query(query: BaseModel, model: db.Model, ordering_fields: list) -> dict:
    query_dict = {key: value for key, value in query.dict().items() if value}
    order_request = query_dict.pop("order", "")
    offset = query_dict.pop("offset", 0)
    limit = query_dict.pop("limit", 10)
    filtering = {key: value for key, value in query_dict.items() if value}
    return {
        "ordering": get_ordering(
            order_request=order_request,
            ordering_fields=ordering_fields,
            model=model,
        ),
        "order": order_request,
        "offset": offset,
        "limit": limit,
        "filtering": filtering
    }


def generate_response_message(status: int, message: str = "", key: str = "result"):
    return {key: message} if message else "", status


def generate_response_error(status: int, message: str):
    return generate_response_message(status=status, message=message, key="error")
