"""
Integration tests for Calendar integrations (Google and Outlook)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.services.integrations import (
    GoogleCalendarIntegration,
    OutlookCalendarIntegration,
    IntegrationError
)
from src.config import DevelopmentConfig


@pytest.fixture
def config():
    """Create test configuration"""
    config = DevelopmentConfig
    config.GOOGLE_APPLICATION_CREDENTIALS = 'test-credentials.json'
    config.GOOGLE_CALENDAR_ID = 'primary'
    config.OUTLOOK_CLIENT_ID = 'test-client-id'
    config.OUTLOOK_CLIENT_SECRET = 'test-client-secret'
    config.OUTLOOK_TENANT_ID = 'common'
    return config


@pytest.fixture
def sample_action_items():
    """Sample action items for testing"""
    return [
        {
            'description': 'Complete project documentation',
            'owner': 'john@example.com',
            'due_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'priority': 'high',
            'context': 'Discussed in project meeting'
        },
        {
            'description': 'Review pull request #123',
            'owner': 'sarah@example.com',
            'due_date': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
            'priority': 'medium',
            'context': 'Code review needed'
        },
        {
            'description': 'Schedule team retrospective',
            'owner': 'mike@example.com',
            'due_date': None,  # No due date - should be skipped
            'priority': 'low'
        }
    ]


class TestGoogleCalendarIntegration:
    """Test cases for Google Calendar integration"""

    @patch('src.services.integrations.service_account')
    @patch('src.services.integrations.build')
    def test_initialization_success(self, mock_build, mock_service_account, config):
        """Test successful Google Calendar initialization"""
        mock_credentials = MagicMock()
        mock_service_account.Credentials.from_service_account_file.return_value = mock_credentials
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        integration = GoogleCalendarIntegration(config)

        assert integration.config == config
        mock_service_account.Credentials.from_service_account_file.assert_called_once()
        mock_build.assert_called_once_with('calendar', 'v3', credentials=mock_credentials)

    def test_initialization_no_credentials(self):
        """Test initialization without credentials"""
        config = DevelopmentConfig
        config.GOOGLE_APPLICATION_CREDENTIALS = None

        with pytest.raises(IntegrationError, match="Google Calendar credentials not configured"):
            GoogleCalendarIntegration(config)

    @patch('src.services.integrations.service_account')
    @patch('src.services.integrations.build')
    def test_create_action_item_events(self, mock_build, mock_service_account, config, sample_action_items):
        """Test creating calendar events for action items"""
        # Setup mocks
        mock_credentials = MagicMock()
        mock_service_account.Credentials.from_service_account_file.return_value = mock_credentials
        
        mock_service = MagicMock()
        mock_events = MagicMock()
        mock_insert = MagicMock()
        
        # Mock successful event creation
        mock_created_event = {
            'id': 'event123',
            'htmlLink': 'https://calendar.google.com/event/123'
        }
        mock_insert.execute.return_value = mock_created_event
        mock_events.insert.return_value = mock_insert
        mock_service.events.return_value = mock_events
        mock_build.return_value = mock_service

        integration = GoogleCalendarIntegration(config)
        result = integration.create_action_item_events(
            sample_action_items,
            meeting_title="Team Standup"
        )

        # Should create 2 events (third item has no due date)
        assert len(result) == 2
        assert result[0]['event_id'] == 'event123'
        assert result[0]['event_link'] == 'https://calendar.google.com/event/123'
        assert 'action_item' in result[0]
        assert 'due_date' in result[0]

    @patch('src.services.integrations.service_account')
    @patch('src.services.integrations.build')
    def test_get_meeting_from_calendar(self, mock_build, mock_service_account, config):
        """Test retrieving meeting details from calendar"""
        mock_credentials = MagicMock()
        mock_service_account.Credentials.from_service_account_file.return_value = mock_credentials
        
        mock_service = MagicMock()
        mock_events = MagicMock()
        mock_get = MagicMock()
        
        mock_event = {
            'summary': 'Team Meeting',
            'start': {'dateTime': '2025-11-09T10:00:00Z'},
            'location': 'Conference Room A',
            'organizer': {'email': 'organizer@example.com'},
            'attendees': [{'email': 'attendee1@example.com'}, {'email': 'attendee2@example.com'}],
            'description': 'Weekly team sync'
        }
        mock_get.execute.return_value = mock_event
        mock_events.get.return_value = mock_get
        mock_service.events.return_value = mock_events
        mock_build.return_value = mock_service

        integration = GoogleCalendarIntegration(config)
        metadata = integration.get_meeting_from_calendar('meeting123')

        assert metadata['title'] == 'Team Meeting'
        assert metadata['organizer'] == 'organizer@example.com'
        assert len(metadata['participants']) == 2


class TestOutlookCalendarIntegration:
    """Test cases for Outlook Calendar integration"""

    @patch('src.services.integrations.Account')
    @patch('src.services.integrations.FileSystemTokenBackend')
    def test_initialization_success(self, mock_token_backend, mock_account_class, config):
        """Test successful Outlook Calendar initialization"""
        mock_account = MagicMock()
        mock_account.is_authenticated = True
        mock_account_class.return_value = mock_account

        integration = OutlookCalendarIntegration(config)

        assert integration.config == config
        mock_account_class.assert_called_once()

    def test_initialization_no_credentials(self):
        """Test initialization without credentials"""
        config = DevelopmentConfig
        config.OUTLOOK_CLIENT_ID = None
        config.OUTLOOK_CLIENT_SECRET = None

        with pytest.raises(IntegrationError, match="Outlook Calendar credentials not configured"):
            OutlookCalendarIntegration(config)

    @patch('src.services.integrations.Account')
    @patch('src.services.integrations.FileSystemTokenBackend')
    def test_create_action_item_events(self, mock_token_backend, mock_account_class, config, sample_action_items):
        """Test creating Outlook calendar events for action items"""
        # Setup mocks
        mock_account = MagicMock()
        mock_account.is_authenticated = True
        
        mock_schedule = MagicMock()
        mock_calendar = MagicMock()
        
        # Mock event creation
        mock_event = MagicMock()
        mock_event.object_id = 'outlook-event-123'
        mock_event.web_link = 'https://outlook.office.com/calendar/event/123'
        
        mock_calendar.new_event.return_value = mock_event
        mock_schedule.get_default_calendar.return_value = mock_calendar
        mock_account.schedule.return_value = mock_schedule
        mock_account_class.return_value = mock_account

        integration = OutlookCalendarIntegration(config)
        result = integration.create_action_item_events(
            sample_action_items,
            meeting_title="Project Review"
        )

        # Should create 2 events (third item has no due date)
        assert len(result) == 2
        assert result[0]['event_id'] == 'outlook-event-123'
        assert 'action_item' in result[0]
        assert 'due_date' in result[0]

    @patch('src.services.integrations.Account')
    @patch('src.services.integrations.FileSystemTokenBackend')
    def test_update_event_on_completion(self, mock_token_backend, mock_account_class, config):
        """Test updating/deleting event when task is completed"""
        mock_account = MagicMock()
        mock_account.is_authenticated = True
        
        mock_schedule = MagicMock()
        mock_calendar = MagicMock()
        mock_event = MagicMock()
        
        mock_calendar.get_event.return_value = mock_event
        mock_schedule.get_default_calendar.return_value = mock_calendar
        mock_account.schedule.return_value = mock_schedule
        mock_account_class.return_value = mock_account

        integration = OutlookCalendarIntegration(config)
        result = integration.update_event_on_completion('event-123', completed=True)

        assert result is True
        mock_event.delete.assert_called_once()


class TestCalendarIntegrationComparison:
    """Compare Google and Outlook calendar integrations"""

    @patch('src.services.integrations.service_account')
    @patch('src.services.integrations.build')
    @patch('src.services.integrations.Account')
    @patch('src.services.integrations.FileSystemTokenBackend')
    def test_both_integrations_create_events(
        self,
        mock_token_backend,
        mock_outlook_account_class,
        mock_google_build,
        mock_service_account,
        config,
        sample_action_items
    ):
        """Test that both Google and Outlook can create events from same data"""
        # Setup Google mocks
        mock_google_credentials = MagicMock()
        mock_service_account.Credentials.from_service_account_file.return_value = mock_google_credentials
        mock_google_service = MagicMock()
        mock_google_events = MagicMock()
        mock_google_insert = MagicMock()
        mock_google_insert.execute.return_value = {'id': 'google-123', 'htmlLink': 'https://google.com/cal'}
        mock_google_events.insert.return_value = mock_google_insert
        mock_google_service.events.return_value = mock_google_events
        mock_google_build.return_value = mock_google_service

        # Setup Outlook mocks
        mock_outlook_account = MagicMock()
        mock_outlook_account.is_authenticated = True
        mock_outlook_schedule = MagicMock()
        mock_outlook_calendar = MagicMock()
        mock_outlook_event = MagicMock()
        mock_outlook_event.object_id = 'outlook-456'
        mock_outlook_event.web_link = 'https://outlook.com/cal'
        mock_outlook_calendar.new_event.return_value = mock_outlook_event
        mock_outlook_schedule.get_default_calendar.return_value = mock_outlook_calendar
        mock_outlook_account.schedule.return_value = mock_outlook_schedule
        mock_outlook_account_class.return_value = mock_outlook_account

        # Create both integrations
        google_integration = GoogleCalendarIntegration(config)
        outlook_integration = OutlookCalendarIntegration(config)

        # Create events with both
        google_result = google_integration.create_action_item_events(
            sample_action_items,
            meeting_title="Test Meeting"
        )
        outlook_result = outlook_integration.create_action_item_events(
            sample_action_items,
            meeting_title="Test Meeting"
        )

        # Both should create same number of events
        assert len(google_result) == len(outlook_result) == 2
        
        # Both should have event IDs
        assert all('event_id' in event for event in google_result)
        assert all('event_id' in event for event in outlook_result)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
