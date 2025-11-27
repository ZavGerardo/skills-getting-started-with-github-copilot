"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        }
    })


def test_root_redirect(client):
    """Test that root redirects to static page"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test retrieving all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert data["Chess Club"]["max_participants"] == 12


def test_signup_for_activity_success(client):
    """Test successfully signing up for an activity"""
    response = client.post(
        "/activities/Chess Club/signup?email=new-student@mergington.edu"
    )
    assert response.status_code == 200
    data = response.json()
    assert "Signed up" in data["message"]
    assert "new-student@mergington.edu" in activities["Chess Club"]["participants"]


def test_signup_for_nonexistent_activity(client):
    """Test signing up for an activity that doesn't exist"""
    response = client.post(
        "/activities/Nonexistent Club/signup?email=student@mergington.edu"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate_participant(client):
    """Test that a student cannot sign up twice for the same activity"""
    email = "michael@mergington.edu"  # Already in Chess Club
    response = client.post(f"/activities/Chess Club/signup?email={email}")
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]


def test_unregister_from_activity_success(client):
    """Test successfully unregistering from an activity"""
    email = "michael@mergington.edu"
    response = client.delete(
        f"/activities/Chess Club/unregister?email={email}"
    )
    assert response.status_code == 200
    data = response.json()
    assert "Unregistered" in data["message"]
    assert email not in activities["Chess Club"]["participants"]


def test_unregister_from_nonexistent_activity(client):
    """Test unregistering from an activity that doesn't exist"""
    response = client.delete(
        "/activities/Nonexistent Club/unregister?email=student@mergington.edu"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_participant_not_registered(client):
    """Test unregistering a student who is not registered"""
    response = client.delete(
        "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
    )
    assert response.status_code == 400
    assert "not registered" in response.json()["detail"]


def test_signup_and_unregister_workflow(client):
    """Test complete workflow: signup and then unregister"""
    email = "workflow-test@mergington.edu"
    activity = "Programming Class"
    
    # Sign up
    signup_response = client.post(f"/activities/{activity}/signup?email={email}")
    assert signup_response.status_code == 200
    assert email in activities[activity]["participants"]
    
    # Unregister
    unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert unregister_response.status_code == 200
    assert email not in activities[activity]["participants"]


def test_participants_list_updated_after_signup(client):
    """Test that participants list is updated after signup"""
    email = "test@mergington.edu"
    activity = "Chess Club"
    
    initial_count = len(activities[activity]["participants"])
    
    client.post(f"/activities/{activity}/signup?email={email}")
    
    # Get updated activities
    response = client.get("/activities")
    data = response.json()
    
    assert len(data[activity]["participants"]) == initial_count + 1
    assert email in data[activity]["participants"]


def test_participants_list_updated_after_unregister(client):
    """Test that participants list is updated after unregister"""
    email = "michael@mergington.edu"
    activity = "Chess Club"
    
    initial_count = len(activities[activity]["participants"])
    
    client.delete(f"/activities/{activity}/unregister?email={email}")
    
    # Get updated activities
    response = client.get("/activities")
    data = response.json()
    
    assert len(data[activity]["participants"]) == initial_count - 1
    assert email not in data[activity]["participants"]
