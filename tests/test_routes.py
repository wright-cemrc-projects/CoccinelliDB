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

def test_group(client):
    client.post("/facility", data=json.dumps({"name": "MCCET"}), headers={"Content-Type": "application/json"})
    facility_resp = client.get("/facility")
    assert len(json.loads(facility_resp.data)) == 1
    datas = [{"name": "matt_group"}, {"name": "liz_group"}]
    for data in datas:
        resp = client.post("/groups", data=json.dumps(data), headers={"Content-Type": "application/json"})
        assert resp.status_code == 200
        assert json.loads(resp.data)["message"] == f"new group {data['name']} created."
    get_resp = client.get("/groups/1")
    assert json.loads(get_resp.data)["name"] == "matt_group"
    del_resp = client.delete("/groups/2")
    assert json.loads(del_resp.data)["message"] == "<FacilityGroup(name=liz_group)> got deleted."
    update_resp = client.post("/groups/1", data=json.dumps({"name": "Matt_group"}), headers={"Content-Type": "application/json"})
    update_get_resp = client.get("/groups/1")
    assert json.loads(update_get_resp.data)["name"] == "Matt_group"

def test_person(client):
    client.post("/facility", data=json.dumps({"name": "MCCET"}), headers={"Content-Type": "application/json"})
    client.post("/groups", data=json.dumps({"name": "matt_group", "facility_id": 1}))
    create_person_resp = client.post("/person", data=json.dumps({"first_name": "Yan", "last_name": "Zhuang", "email": "yzhuang63@wisc.edu", "group_id": 1, "net_id": "9084938471"}), headers={"Content-Type": "application/json"})
    assert create_person_resp.status_code == 200
    assert json.loads(create_person_resp.data)["message"] == f"FacilityPerson(name=Yan Zhuang, email=yzhuang63@wisc.edu) created."
    get_person_resp = client.get("/person/1")
    assert json.loads(get_person_resp.data)["email"] == "yzhuang63@wisc.edu"
    update_person_resp = client.post("/person/1", data=json.dumps({"organization": "UW Madison"}), headers={"Content-Type": "application/json"})
    assert update_person_resp.status_code == 200
    assert json.loads(update_person_resp.data)["message"] == "FacilityPerson(name=Yan Zhuang, email=yzhuang63@wisc.edu) got updated."
    update_get_person_resp = client.get("/person/1")
    assert json.loads(update_get_person_resp.data)["organization"] == "UW Madison"
    delete_person_resp = client.delete("/person/1")
    assert json.loads(delete_person_resp.data)["message"] == "FacilityPerson(name=Yan Zhuang, email=yzhuang63@wisc.edu) got deleted."
