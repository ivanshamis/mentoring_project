import json
import os
from datetime import datetime
from http import HTTPStatus
from typing import Optional
from uuid import UUID

from PIL import Image, UnidentifiedImageError

from flask import request, current_app as app
from flask.views import MethodView
from flask_pydantic import validate
from flask_rest_api import Blueprint
from pydantic import BaseModel

from api_utils import paginate, parse_query, generate_response_error, generate_response_message
from extensions import db

from jwt_utils import jwt_required
from models import Doc

docs_bp = Blueprint("docs_bp", __name__)

IMG_EXTENSIONS = [".gif", ".jpg", ".jpeg", ".png"]
DOC_EXTENSIONS = [".doc", ".docx", ".html", ".pdf", ".txt", ".xsl", ".xlsx"]
VIDEO_EXTENSIONS = [".mp4", ".mov", ".wmv", ".flv", ".avi"]  # TODO validate file size

ALLOWED_EXTENSIONS = IMG_EXTENSIONS + DOC_EXTENSIONS + VIDEO_EXTENSIONS


def save_thumbnail(main_path, doc_id, extension):
    thumbnail_path = None

    if extension in IMG_EXTENSIONS:
        square_fit_size = 100
        try:
            image = Image.open(main_path)
        except UnidentifiedImageError:
            image = None

        if image:
            image.thumbnail((square_fit_size, square_fit_size))
            thumbnail_path = os.path.join(app.config["UPLOAD_FOLDER"], str(doc_id) + "_thumb" + extension)
            image.save(thumbnail_path)

    return thumbnail_path


class DocsGetArgsSchema(BaseModel):
    limit: Optional[int]
    offset: Optional[int]
    extension: Optional[str]
    user_id: Optional[UUID]
    order: Optional[str]


@docs_bp.route("/docs/")
class Docs(MethodView):
    model = Doc
    path = "/docs/"
    filter_fields = ["extension", "user_id"]
    default_filter = {"deleted": False}
    ordering_fields = ["created_at", "name"]

    @jwt_required()
    @validate()
    def get(self, query: DocsGetArgsSchema, *args, **kwargs):
        parsed_query = parse_query(
            query=query,
            model=self.model,
            ordering_fields=self.ordering_fields,
        )

        results = self.model.query.filter_by(
            **({
                **parsed_query["filtering"],
                **self.default_filter,
            })
        ).order_by(
            *parsed_query["ordering"]
        )

        return paginate(
            query=results,
            url=self.path,
            parsed_query=parsed_query,
        )

    @jwt_required()
    def post(self, user_id):
        file = request.files.get('file')
        if not file:
            return generate_response_error(status=HTTPStatus.BAD_REQUEST, message="Please provide a file")
        filename, extension = os.path.splitext(file.filename)
        extension = extension.lower()

        if extension not in ALLOWED_EXTENSIONS:
            return generate_response_error(status=HTTPStatus.BAD_REQUEST, message="The file type is not allowed")

        # TODO validate images

        doc = self.model(
            name=filename,
            extension=extension,
            path="/",  # will setup the path later
            user_id=user_id,
            created_at=datetime.now()
        )
        db.session.add(doc)
        db.session.flush()
        doc.path = os.path.join(app.config["UPLOAD_FOLDER"], str(doc.id) + extension)
        file.save(doc.path)
        doc.thumbnail = save_thumbnail(doc.path, doc.id, extension)
        db.session.commit()

        return generate_response_message(status=HTTPStatus.CREATED, message=json.dumps({"id": str(doc.id)}))


@docs_bp.route("/docs/<item_id>")
class DocsById(MethodView):
    @jwt_required()
    def get(self, item_id, *args, **kwargs):
        return Doc.query.filter_by(id=item_id).first().serialize

    @jwt_required()
    def delete(self, item_id, user_id, *args, **kwargs):
        doc = Doc.query.get_or_404(item_id)
        if doc.deleted:
            return generate_response_error(status=HTTPStatus.NOT_FOUND, message="File not found")
        if str(doc.user_id) != str(user_id):
            return generate_response_error(status=HTTPStatus.FORBIDDEN, message="User is not owner of the document")
        doc.deleted = True
        db.session.commit()
        return generate_response_message(status=HTTPStatus.NO_CONTENT)
