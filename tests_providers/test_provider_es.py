#-*- coding:utf-8 -*-
import time
import pytest
from pytest_dbfixtures import factories

## How to install elasticsearch :
# $ wget https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-1.3.2.zip
# $ unzip elasticsearch-1.3.2.zip
# $ sudo cp -r elasticsearch-1.3.2 /usr/local/share/
# $ sudo ln -s /usr/local/share/elasticsearch-1.3.2/ /usr/share/elasticsearch

# create es fixture
# see http://pytest-dbfixtures.readthedocs.org/
es_proc = factories.elasticsearch_proc(host='127.0.1', port=9201)
es = factories.elasticsearch("es_proc", hosts='127.0.01:9201')

from cello.providers.es import EsIndex

def test_create_and_delete(es):
    idx = EsIndex("test_idx", es=es)
    assert not idx.exist()
    idx.create()
    assert idx.exist()
    idx.delete()
    assert not idx.exist()

@pytest.fixture
def idx(es):
    schema = {
        "_id": {"path": "docnum"},
        "dynamic": "strict",
        "properties": {
            "docnum": {"type": "string"},
            "message": {
                "type": "string",
                "store": True,
                "index": "analyzed",
                "null_value": "na"
            },
            "user": {
                "type": "string",
                "index": "not_analyzed",
                "norms": {
                    "enabled": False
                }
            }
        }
    }
    idx = EsIndex("test_idx", doc_type="doc", schema=schema, es=es)
    idx.create()
    time.sleep(1)
    return idx


@pytest.fixture
def full_idx(idx):
    doc = {"docnum":"42", "user": "papy", "message": "Salut tout le monde !"}
    res = idx.add_document(doc)
    doc = {"docnum":"666", "user": "evil", "message": "Good bye !"}
    res = idx.add_document(doc)
    return idx


def test_create_and_delete_with_mapping(idx):
    assert idx.exist()
    # test mappings are ok
    idx_schema = idx.get_schema()
    assert 'properties' in idx_schema
    assert 'message' in idx_schema["properties"]
    assert 'user' in idx_schema["properties"]
    idx.delete()
    time.sleep(1)
    assert not idx.exist()

def test_add_get_doc(idx):
    assert len(idx) == 0
    doc = {"docnum":"42", "user": "papy", "message": "Salut tout le monde !"}
    res = idx.add_document(doc)
    assert res["created"]
    assert res["_id"] == "42"
    time.sleep(1)
    # check added
    assert len(idx) == 1
    # get the document
    retriev_doc = idx.get_document("42")
    assert retriev_doc == doc


def test_update(full_idx):
    full_idx.update_document("42", {"message": "Super non ?"})
    time.sleep(1)
    retriev_doc = full_idx.get_document("42")
    assert retriev_doc["message"] == "Super non ?"
