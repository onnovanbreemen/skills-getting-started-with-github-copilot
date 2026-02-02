"""
Tests for the FastAPI application endpoints.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test."""
    original_activities = {
        "Basketball": {
            "description": "Team sport focusing on basketball skills and competition",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["alex@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Learn tennis techniques and participate in friendly matches",
            "schedule": "Saturdays, 10:00 AM - 12:00 PM",
            "max_participants": 10,
            "participants": ["lucas@mergington.edu"]
        },
        "Drama Club": {
            "description": "Perform in theatrical productions and develop acting skills",
            "schedule": "Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 25,
            "participants": ["isabella@mergington.edu", "noah@mergington.edu"]
        },
    }
    
    # Clear current activities
    activities.clear()
    # Restore original
    activities.update(original_activities)
    
    yield
    
    # Reset after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Basketball" in data
        assert "Tennis Club" in data
        assert "Drama Club" in data
    
    def test_get_activities_returns_activity_details(self, client, reset_activities):
        """Test that activities include all required fields."""
        response = client.get("/activities")
        data = response.json()
        basketball = data["Basketball"]
        
        assert "description" in basketball
        assert "schedule" in basketball
        assert "max_participants" in basketball
        assert "participants" in basketball
    
    def test_get_activities_includes_participants(self, client, reset_activities):
        """Test that activities include participant information."""
        response = client.get("/activities")
        data = response.json()
        
        assert "alex@mergington.edu" in data["Basketball"]["participants"]
        assert "lucas@mergington.edu" in data["Tennis Club"]["participants"]


class TestSignUpForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_for_activity_success(self, client, reset_activities):
        """Test successfully signing up for an activity."""
        response = client.post(
            "/activities/Basketball/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
    
    def test_signup_adds_participant_to_activity(self, client, reset_activities):
        """Test that signup actually adds the participant to the activity."""
        client.post(
            "/activities/Basketball/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        response = client.get("/activities")
        data = response.json()
        assert "newstudent@mergington.edu" in data["Basketball"]["participants"]
    
    def test_signup_for_nonexistent_activity_returns_404(self, client):
        """Test that signing up for a non-existent activity returns 404."""
        response = client.post(
            "/activities/NonExistentActivity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_email_returns_400(self, client, reset_activities):
        """Test that signing up with duplicate email returns 400."""
        response = client.post(
            "/activities/Basketball/signup",
            params={"email": "alex@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_multiple_students_to_same_activity(self, client, reset_activities):
        """Test that multiple students can sign up for the same activity."""
        client.post(
            "/activities/Basketball/signup",
            params={"email": "student1@mergington.edu"}
        )
        client.post(
            "/activities/Basketball/signup",
            params={"email": "student2@mergington.edu"}
        )
        
        response = client.get("/activities")
        participants = response.json()["Basketball"]["participants"]
        assert "student1@mergington.edu" in participants
        assert "student2@mergington.edu" in participants


class TestUnregisterFromActivity:
    """Tests for POST /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_success(self, client, reset_activities):
        """Test successfully unregistering from an activity."""
        response = client.post(
            "/activities/Basketball/unregister",
            params={"email": "alex@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "alex@mergington.edu" in data["message"]
    
    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the participant."""
        client.post(
            "/activities/Basketball/unregister",
            params={"email": "alex@mergington.edu"}
        )
        
        response = client.get("/activities")
        data = response.json()
        assert "alex@mergington.edu" not in data["Basketball"]["participants"]
    
    def test_unregister_from_nonexistent_activity_returns_404(self, client):
        """Test that unregistering from non-existent activity returns 404."""
        response = client.post(
            "/activities/NonExistentActivity/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_nonexistent_participant_returns_400(self, client, reset_activities):
        """Test that unregistering non-existent participant returns 400."""
        response = client.post(
            "/activities/Basketball/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
    
    def test_unregister_multiple_participants(self, client, reset_activities):
        """Test unregistering multiple participants."""
        # Add two new participants
        client.post(
            "/activities/Basketball/signup",
            params={"email": "student1@mergington.edu"}
        )
        client.post(
            "/activities/Basketball/signup",
            params={"email": "student2@mergington.edu"}
        )
        
        # Unregister one
        client.post(
            "/activities/Basketball/unregister",
            params={"email": "student1@mergington.edu"}
        )
        
        response = client.get("/activities")
        participants = response.json()["Basketball"]["participants"]
        assert "student1@mergington.edu" not in participants
        assert "student2@mergington.edu" in participants


class TestWorkflow:
    """Integration tests for complete workflows."""
    
    def test_signup_and_unregister_workflow(self, client, reset_activities):
        """Test complete signup and unregister workflow."""
        email = "workflow@mergington.edu"
        activity = "Basketball"
        
        # Sign up
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify participant was added
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify participant was removed
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
