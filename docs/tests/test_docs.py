import json
from http import HTTPStatus

import pytest


def test_get_docs_list_unauthorized(client):
    response = client.get('/docs/')
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_docs_list(client, doc_jpg, auth_headers):
    response = client.get("/docs/", headers=auth_headers)
    assert response.status_code == HTTPStatus.OK
    assert response.json["results"] == [doc_jpg.serialize]


def test_get_doc_by_id(client, doc_jpg, auth_headers):
    response = client.get(f"/docs/{doc_jpg.id}", headers=auth_headers)
    assert response.status_code == HTTPStatus.OK
    assert response.json == doc_jpg.serialize


def test_upload_doc(client, file_jpg, auth_headers):
    response = client.post(
        "/docs/",
        headers=auth_headers,
        content_type="multipart/form-data",
        data={"file": file_jpg}
    )
    assert response.status_code == HTTPStatus.CREATED
    result = json.loads(response.json["result"])
    assert "id" in result


def test_delete_doc(client, doc_jpg, auth_headers):
    response = client.delete(f"/docs/{doc_jpg.id}", headers=auth_headers)
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert doc_jpg.deleted


def test_filter_by_extension_jpg(client, doc_jpg, doc_txt, auth_headers):
    response = client.get(f"/docs/?extension={doc_jpg.extension}", headers=auth_headers)
    assert response.status_code == HTTPStatus.OK
    assert response.json["results"] == [doc_jpg.serialize]


def test_filter_by_extension_txt(client, doc_jpg, doc_txt, auth_headers):
    response = client.get(f"/docs/?extension={doc_txt.extension}", headers=auth_headers)
    assert response.status_code == HTTPStatus.OK
    assert response.json["results"] == [doc_txt.serialize]


def test_filter_by_user_id(client, doc_jpg, auth_headers):
    ...


def test_sort_by_name_desc(client, doc_jpg, doc_txt, auth_headers):
    response = client.get(f"/docs/?order=name", headers=auth_headers)
    assert response.status_code == HTTPStatus.OK
    assert response.json["results"] == [doc_jpg.serialize, doc_txt.serialize]


def test_sort_by_name_desc(client, doc_jpg, doc_txt, auth_headers):
    response = client.get(f"/docs/?order=-name", headers=auth_headers)
    assert response.status_code == HTTPStatus.OK
    assert response.json["results"] == [doc_txt.serialize, doc_jpg.serialize]


def test_sort_by_created_at(client, doc_jpg, doc_txt, auth_headers):
    response = client.get(f"/docs/?order=created_at", headers=auth_headers)
    assert response.status_code == HTTPStatus.OK
    assert response.json["results"] == [doc_jpg.serialize, doc_txt.serialize]


def test_sort_by_created_at_desc(client, doc_jpg, doc_txt, auth_headers):
    response = client.get(f"/docs/?order=-created_at", headers=auth_headers)
    assert response.status_code == HTTPStatus.OK
    assert response.json["results"] == [doc_txt.serialize, doc_jpg.serialize]
