import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_activities():
    original_activities = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(copy.deepcopy(original_activities))


def test_get_activities_returns_all_activities():
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert expected_activity in payload
    assert "description" in payload[expected_activity]
    assert "participants" in payload[expected_activity]
    assert "max_participants" in payload[expected_activity]


def test_signup_for_activity_adds_participant():
    # Arrange
    email = "newstudent@mergington.edu"
    activity_name = "Chess Club"
    url = f"/activities/{quote(activity_name, safe='')}/signup?email={quote(email, safe='')}"

    # Act
    response = client.post(url)

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    assert email in activities[activity_name]["participants"]


def test_signup_duplicate_returns_bad_request():
    # Arrange
    email = "duplicate@mergington.edu"
    activity_name = "Chess Club"
    signup_url = f"/activities/{quote(activity_name, safe='')}/signup?email={quote(email, safe='')}"

    # Act
    first_response = client.post(signup_url)
    duplicate_response = client.post(signup_url)

    # Assert
    assert first_response.status_code == 200
    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == "Student already signed up for this activity"


def test_remove_participant_unsubscribes_user():
    # Arrange
    email = "remove-test@mergington.edu"
    activity_name = "Chess Club"
    signup_url = f"/activities/{quote(activity_name, safe='')}/signup?email={quote(email, safe='')}"
    delete_url = f"/activities/{quote(activity_name, safe='')}/participants?email={quote(email, safe='')}"

    client.post(signup_url)

    # Act
    response = client.delete(delete_url)

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email} from {activity_name}"
    assert email not in activities[activity_name]["participants"]


def test_remove_missing_participant_returns_404():
    # Arrange
    email = "missing@mergington.edu"
    activity_name = "Chess Club"
    delete_url = f"/activities/{quote(activity_name, safe='')}/participants?email={quote(email, safe='')}"

    # Act
    response = client.delete(delete_url)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
