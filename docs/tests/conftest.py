import uuid
from datetime import timedelta

import pytest

from main import app
from extensions import db
from models import Doc
from tests.utils import generate_token, get_file


@pytest.fixture
def test_app():
    with app.app_context():
        db.create_all()
        yield app
        db.session.close()
        db.drop_all()


@pytest.fixture
def client(test_app):
    with test_app.test_client() as client:
        yield client


@pytest.fixture
def user_id():
    return uuid.uuid4()


@pytest.fixture
def user_id_2():
    return uuid.uuid4()


@pytest.fixture
def auth_headers(user_id):
    return {"Authorization": f"Token {generate_token(user_id)}"}


def create_fixture(instance):
    db.session.add(instance)
    db.session.flush()
    yield instance
    db.session.rollback()


@pytest.fixture
def doc_jpg(user_id):
    return create_fixture(
        Doc(name="test_image", extension=".jpg", path="test_image.jpg", user_id=user_id)
    ).__next__()


@pytest.fixture
def doc_txt(user_id_2):
    doc = create_fixture(
        Doc(name="test_text", extension=".txt", path="test_text.txt", user_id=user_id_2)
    ).__next__()

    doc.created_at += timedelta(seconds=1)
    return doc


@pytest.fixture
def file_jpg():
    return get_file("test.jpg")
