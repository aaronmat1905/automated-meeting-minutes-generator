"""
Sample test file for the Automated Meeting Minutes Generator project.
This ensures pytest can run successfully in the CI/CD pipeline.
"""

import pytest


def test_sample():
    """
    A basic test to ensure the test suite is working.
    Replace this with actual tests as you develop the project.
    """
    assert True


def test_basic_math():
    """
    Another sample test demonstrating basic assertions.
    """
    assert 1 + 1 == 2
    assert 2 * 3 == 6


class TestSampleClass:
    """
    Sample test class demonstrating test organization.
    """

    def test_string_operations(self):
        """Test basic string operations."""
        test_string = "Meeting Minutes"
        assert test_string.lower() == "meeting minutes"
        assert len(test_string) == 15

    def test_list_operations(self):
        """Test basic list operations."""
        test_list = [1, 2, 3, 4, 5]
        assert len(test_list) == 5
        assert sum(test_list) == 15
        assert max(test_list) == 5
