"""Tests for the Mergington High School Activities API"""

import sys
from pathlib import Path

# Add src to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient
from app import app


client = TestClient(app)


class TestActivitiesEndpoint:
    """Test the /activities GET endpoint"""

    def test_get_activities_returns_dict(self):
        """Test that /activities returns a dictionary of activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0

    def test_get_activities_has_expected_fields(self):
        """Test that each activity has the expected fields"""
        response = client.get("/activities")
        activities = response.json()

        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_contains_expected_activities(self):
        """Test that the response contains specific expected activities"""
        response = client.get("/activities")
        activities = response.json()

        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Soccer Team",
            "Basketball Club"
        ]

        for activity in expected_activities:
            assert activity in activities


class TestSignupEndpoint:
    """Test the /activities/{activity_name}/signup POST endpoint"""

    def test_signup_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_adds_participant(self):
        """Test that signup actually adds the participant to the activity"""
        email = "testuser@mergington.edu"
        activity = "Chess Club"

        # Check initial participant count
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])

        # Sign up
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response.status_code == 200

        # Verify participant was added
        response = client.get("/activities")
        final_count = len(response.json()[activity]["participants"])
        assert final_count == initial_count + 1
        assert email in response.json()[activity]["participants"]

    def test_signup_duplicate_participant(self):
        """Test that duplicate signups are rejected"""
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        activity = "Chess Club"

        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity(self):
        """Test that signup to nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestUnregisterEndpoint:
    """Test the /activities/{activity_name}/unregister POST endpoint"""

    def test_unregister_success(self):
        """Test successful unregister from an activity"""
        email = "michael@mergington.edu"  # Already a participant in Chess Club
        activity = "Chess Club"

        response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        # First sign up
        email = "unregister_test@mergington.edu"
        activity = "Programming Class"
        client.post(f"/activities/{activity}/signup?email={email}")

        # Verify participant was added
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]

        # Unregister
        response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response.status_code == 200

        # Verify participant was removed
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]

    def test_unregister_not_registered(self):
        """Test that unregistering someone not signed up returns 400"""
        email = "notregistered@mergington.edu"
        activity = "Soccer Team"

        response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()

    def test_unregister_nonexistent_activity(self):
        """Test that unregister from nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestRootEndpoint:
    """Test the root endpoint"""

    def test_root_redirects_to_static_index(self):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestIntegrationFlow:
    """Test complete user flows"""

    def test_signup_and_unregister_flow(self):
        """Test signing up and then unregistering from an activity"""
        email = "flow_test@mergington.edu"
        activity = "Drama Club"

        # Get initial state
        response = client.get("/activities")
        initial_participants = response.json()[activity]["participants"].copy()

        # Sign up
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200

        # Verify signed up
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]

        # Unregister
        response = client.post(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200

        # Verify back to initial state
        response = client.get("/activities")
        assert response.json()[activity]["participants"] == initial_participants
