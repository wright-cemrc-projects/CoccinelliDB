import pytest
import json

def test_hello(client):
    response = client.get("/home")
    assert response.json["message"] == "Hello World"

def test_facility(client):
    datas = [{"name": "MCCET"}, {"name": "SCSC"}, {"name": "NCITU"}, {"name": "CCET"}]
    for data in datas:
        resp = client.post("/facility", data=json.dumps(data), headers={"Content-Type": "application/json"})
        assert resp.status_code == 200
        assert json.loads(resp.data)["message"] == "new facility created."
    get_resp = client.get("/facility/1")
    assert json.loads(get_resp.data)["name"] == "MCCET"
    del_resp = client.delete("/facility/4")
    assert json.loads(del_resp.data)["message"] == "<Facility(name=CCET)> got deleted."
    get_list_resp = client.get("/facility")
    assert len(json.loads(get_list_resp.data)) == 3