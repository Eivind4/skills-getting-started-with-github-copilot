from src.app import activities

NEW_EMAIL = "new.student@mergington.edu"


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_all_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert set(data) == set(activities)
    for details in data.values():
        assert {"description", "schedule", "max_participants", "participants"} <= set(details)


def test_signup_success(client):
    response = client.post("/activities/Chess Club/signup", params={"email": NEW_EMAIL})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {NEW_EMAIL} for Chess Club"}
    assert NEW_EMAIL in activities["Chess Club"]["participants"]


def test_signup_unknown_activity_returns_404(client):
    response = client.post("/activities/Unknown Club/signup", params={"email": NEW_EMAIL})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate_returns_400(client):
    existing = activities["Chess Club"]["participants"][0]

    response = client.post("/activities/Chess Club/signup", params={"email": existing})

    assert response.status_code == 400
    assert activities["Chess Club"]["participants"].count(existing) == 1


def test_signup_full_activity_returns_400(client):
    activity = activities["Chess Club"]
    activity["participants"] = [f"s{i}@mergington.edu" for i in range(activity["max_participants"])]

    response = client.post("/activities/Chess Club/signup", params={"email": NEW_EMAIL})

    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"
    assert NEW_EMAIL not in activity["participants"]


def test_unregister_success(client):
    existing = activities["Chess Club"]["participants"][0]

    response = client.delete("/activities/Chess Club/unregister", params={"email": existing})

    assert response.status_code == 200
    assert existing not in activities["Chess Club"]["participants"]


def test_unregister_unknown_activity_returns_404(client):
    response = client.delete("/activities/Unknown Club/unregister", params={"email": NEW_EMAIL})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_not_signed_up_returns_404(client):
    response = client.delete("/activities/Chess Club/unregister", params={"email": NEW_EMAIL})

    assert response.status_code == 404


def test_signup_then_unregister_round_trip(client):
    original = list(activities["Chess Club"]["participants"])

    client.post("/activities/Chess Club/signup", params={"email": NEW_EMAIL})
    client.delete("/activities/Chess Club/unregister", params={"email": NEW_EMAIL})

    assert client.get("/activities").json()["Chess Club"]["participants"] == original
