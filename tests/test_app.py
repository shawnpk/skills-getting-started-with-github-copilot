"""
Test suite for Mergington High School API endpoints

Uses the AAA (Arrange-Act-Assert) pattern for test organization:
- Arrange: Set up test data and preconditions
- Act: Execute the code being tested
- Assert: Verify the results meet expectations
"""

import pytest


class TestRootEndpoint:
    """Tests for the root endpoint (GET /)"""

    def test_root_redirects_to_static_index(self, client):
        """
        Arrange: No setup needed
        Act: GET request to root path
        Assert: Should redirect to /static/index.html
        """
        # Arrange
        # (no additional setup needed)

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesListing:
    """Tests for activities listing endpoint (GET /activities)"""

    def test_get_all_activities_success(self, client):
        """
        Arrange: No setup needed (activities pre-loaded)
        Act: GET request to /activities
        Assert: Should return all activities with correct structure
        """
        # Arrange
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Tennis Club",
            "Art Studio",
            "Music Ensemble",
            "Debate Team",
            "Science Club",
        ]

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == len(expected_activities)
        for activity_name in expected_activities:
            assert activity_name in data
            assert "description" in data[activity_name]
            assert "schedule" in data[activity_name]
            assert "max_participants" in data[activity_name]
            assert "participants" in data[activity_name]

    def test_activity_has_required_fields(self, client):
        """
        Arrange: Retrieve activities data
        Act: Check structure of an activity
        Assert: Activity should have all required fields with correct types
        """
        # Arrange
        # (no additional setup needed)

        # Act
        response = client.get("/activities")
        activities = response.json()
        chess_club = activities["Chess Club"]

        # Assert
        assert isinstance(chess_club["description"], str)
        assert isinstance(chess_club["schedule"], str)
        assert isinstance(chess_club["max_participants"], int)
        assert isinstance(chess_club["participants"], list)
        assert all(isinstance(email, str) for email in chess_club["participants"])


class TestSignupForActivity:
    """Tests for signup functionality (POST /activities/{activity_name}/signup)"""

    def test_signup_new_student_success(self, client):
        """
        Arrange: Prepare new student email that isn't already signed up
        Act: POST signup request for an available activity
        Assert: Should successfully add student to participants
        """
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"activity_name": activity_name, "email": new_email},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert new_email in data["message"]
        assert activity_name in data["message"]

        # Verify student was actually added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert new_email in activities[activity_name]["participants"]

    def test_signup_with_nonexistent_activity_fails(self, client):
        """
        Arrange: Prepare email and non-existent activity name
        Act: POST signup request with invalid activity
        Assert: Should return 404 error
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"activity_name": activity_name, "email": email},
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_signup_duplicate_student_fails(self, client):
        """
        Arrange: Identify a student already signed up for an activity
        Act: POST signup request with duplicate student
        Assert: Should return 400 error
        """
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"activity_name": activity_name, "email": existing_email},
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student already signed up"

    def test_signup_multiple_students_for_different_activities(self, client):
        """
        Arrange: Prepare multiple students and activities
        Act: Sign up different students for different activities
        Assert: All signups should succeed and students appear in correct activities
        """
        # Arrange
        signups = [
            ("Programming Class", "alice@mergington.edu"),
            ("Tennis Club", "bob@mergington.edu"),
            ("Science Club", "charlie@mergington.edu"),
        ]

        # Act
        responses = []
        for activity_name, email in signups:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"activity_name": activity_name, "email": email},
            )
            responses.append((activity_name, email, response))

        # Assert
        for activity_name, email, response in responses:
            assert response.status_code == 200
            assert email in response.json()["message"]

        # Verify all students are registered in their activities
        activities_response = client.get("/activities")
        activities = activities_response.json()
        for activity_name, email in signups:
            assert email in activities[activity_name]["participants"]


class TestUnregisterFromActivity:
    """Tests for unregister functionality (DELETE /activities/{activity_name}/participants)"""

    def test_unregister_existing_student_success(self, client):
        """
        Arrange: First sign up a student, then prepare to unregister them
        Act: DELETE request to remove student from activity
        Assert: Student should be removed from participants
        """
        # Arrange
        activity_name = "Basketball Team"
        email = "testunregister@mergington.edu"
        # First sign up
        client.post(
            f"/activities/{activity_name}/signup",
            params={"activity_name": activity_name, "email": email},
        )

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"activity_name": activity_name, "email": email},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert email in data["message"]
        assert activity_name in data["message"]

        # Verify student was actually removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity_name]["participants"]

    def test_unregister_from_nonexistent_activity_fails(self, client):
        """
        Arrange: Prepare non-existent activity name
        Act: DELETE request with invalid activity
        Assert: Should return 404 error
        """
        # Arrange
        activity_name = "Fake Activity"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"activity_name": activity_name, "email": email},
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_unregister_nonexistent_student_fails(self, client):
        """
        Arrange: Identify a student not registered for an activity
        Act: DELETE request with non-participating student
        Assert: Should return 404 error
        """
        # Arrange
        activity_name = "Art Studio"
        email = "notregistered@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"activity_name": activity_name, "email": email},
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Student is not signed up"

    def test_unregister_multiple_students_from_same_activity(self, client):
        """
        Arrange: Sign up multiple students for the same activity
        Act: Unregister each student from the activity
        Assert: All students should be successfully removed
        """
        # Arrange
        activity_name = "Music Ensemble"
        students = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu",
        ]

        # Sign up all students
        for email in students:
            client.post(
                f"/activities/{activity_name}/signup",
                params={"activity_name": activity_name, "email": email},
            )

        # Act
        unregister_responses = []
        for email in students:
            response = client.delete(
                f"/activities/{activity_name}/participants",
                params={"activity_name": activity_name, "email": email},
            )
            unregister_responses.append(response)

        # Assert
        for response in unregister_responses:
            assert response.status_code == 200

        # Verify all students were removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        for email in students:
            assert email not in activities[activity_name]["participants"]


class TestDataPersistence:
    """Tests for data persistence across multiple requests"""

    def test_signup_persists_across_requests(self, client):
        """
        Arrange: Sign up a student for an activity
        Act: Perform multiple GET requests to verify data persists
        Assert: Student should remain registered across all requests
        """
        # Arrange
        activity_name = "Debate Team"
        email = "persistent@mergington.edu"

        # Act & Assert - Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"activity_name": activity_name, "email": email},
        )
        assert signup_response.status_code == 200

        # Act & Assert - Verify persistence with multiple GET requests
        for _ in range(3):
            response = client.get("/activities")
            activities = response.json()
            assert email in activities[activity_name]["participants"]

    def test_unregister_persists_across_requests(self, client):
        """
        Arrange: Sign up a student, then unregister them
        Act: Perform multiple GET requests to verify unregistration persists
        Assert: Student should remain unregistered across all requests
        """
        # Arrange
        activity_name = "Gym Class"
        email = "unregister_persist@mergington.edu"

        # Sign up first
        client.post(
            f"/activities/{activity_name}/signup",
            params={"activity_name": activity_name, "email": email},
        )

        # Act - Unregister
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"activity_name": activity_name, "email": email},
        )
        assert response.status_code == 200

        # Assert - Verify persistence with multiple GET requests
        for _ in range(3):
            response = client.get("/activities")
            activities = response.json()
            assert email not in activities[activity_name]["participants"]