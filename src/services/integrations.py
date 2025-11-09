"""
Integration Services
Google Calendar, Outlook Calendar, Jira, and Asana integrations for action item syncing
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from O365 import Account, FileSystemTokenBackend
from jira import JIRA
import asana

from src.config import Config

logger = logging.getLogger(__name__)


class IntegrationError(Exception):
    """Custom exception for integration errors"""
    pass


class GoogleCalendarIntegration:
    """Google Calendar integration for action item reminders"""

    def __init__(self, config: Config):
        self.config = config

        # Initialize Google Calendar API
        if config.GOOGLE_APPLICATION_CREDENTIALS:
            credentials = service_account.Credentials.from_service_account_file(
                config.GOOGLE_APPLICATION_CREDENTIALS,
                scopes=config.GOOGLE_CALENDAR_SCOPES
            )
            self.service = build('calendar', 'v3', credentials=credentials)
        else:
            raise IntegrationError("Google Calendar credentials not configured")

    def create_action_item_events(
        self,
        action_items: List[Dict],
        meeting_title: str,
        calendar_id: str = None
    ) -> List[Dict]:
        """
        Create calendar events for action items with due dates

        Args:
            action_items: List of action item dictionaries
            meeting_title: Title of the meeting
            calendar_id: Calendar ID (default: primary)

        Returns:
            List of created event IDs and links
        """
        if calendar_id is None:
            calendar_id = self.config.GOOGLE_CALENDAR_ID

        created_events = []

        for item in action_items:
            if not item.get('due_date'):
                continue

            try:
                # Parse due date
                due_date = datetime.strptime(item['due_date'], '%Y-%m-%d')

                # Create event
                event = {
                    'summary': f"[Action Item] {item.get('description', 'No description')[:100]}",
                    'description': self._format_action_item_description(item, meeting_title),
                    'start': {
                        'date': due_date.strftime('%Y-%m-%d'),
                        'timeZone': 'UTC',
                    },
                    'end': {
                        'date': due_date.strftime('%Y-%m-%d'),
                        'timeZone': 'UTC',
                    },
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                            {'method': 'popup', 'minutes': 60},  # 1 hour before
                        ],
                    },
                }

                # Add attendee if owner email is available
                if item.get('owner') and '@' in item['owner']:
                    event['attendees'] = [{'email': item['owner']}]

                # Create event
                created_event = self.service.events().insert(
                    calendarId=calendar_id,
                    body=event
                ).execute()

                created_events.append({
                    'action_item': item['description'],
                    'event_id': created_event['id'],
                    'event_link': created_event.get('htmlLink'),
                    'due_date': item['due_date']
                })

                logger.info(f"Created calendar event for action item: {item['description'][:50]}")

            except Exception as e:
                logger.error(f"Error creating calendar event: {str(e)}")
                continue

        return created_events

    def _format_action_item_description(self, item: Dict, meeting_title: str) -> str:
        """Format action item as calendar event description"""
        description = f"Action Item from Meeting: {meeting_title}\n\n"
        description += f"Task: {item.get('description', 'N/A')}\n"
        description += f"Owner: {item.get('owner', 'Unassigned')}\n"
        description += f"Priority: {item.get('priority', 'Medium')}\n"
        description += f"Due Date: {item.get('due_date', 'Not specified')}\n"

        if item.get('context'):
            description += f"\nContext:\n{item['context']}\n"

        return description

    def get_meeting_from_calendar(self, meeting_id: str, calendar_id: str = None) -> Dict:
        """
        Retrieve meeting details from Google Calendar

        Args:
            meeting_id: Calendar event ID
            calendar_id: Calendar ID (default: primary)

        Returns:
            Meeting metadata dictionary
        """
        if calendar_id is None:
            calendar_id = self.config.GOOGLE_CALENDAR_ID

        try:
            event = self.service.events().get(
                calendarId=calendar_id,
                eventId=meeting_id
            ).execute()

            # Extract meeting metadata
            metadata = {
                'title': event.get('summary', 'Untitled Meeting'),
                'date': event['start'].get('dateTime', event['start'].get('date')),
                'location': event.get('location', 'Virtual'),
                'organizer': event.get('organizer', {}).get('email'),
                'participants': [a['email'] for a in event.get('attendees', [])],
                'description': event.get('description', '')
            }

            return metadata

        except HttpError as e:
            logger.error(f"Error retrieving calendar event: {str(e)}")
            raise IntegrationError(f"Failed to retrieve calendar event: {str(e)}")


class OutlookCalendarIntegration:
    """Microsoft Outlook/O365 Calendar integration for action item reminders"""

    def __init__(self, config: Config):
        self.config = config

        # Initialize O365 Account
        if not all([config.OUTLOOK_CLIENT_ID, config.OUTLOOK_CLIENT_SECRET]):
            raise IntegrationError("Outlook Calendar credentials not configured")

        credentials = (config.OUTLOOK_CLIENT_ID, config.OUTLOOK_CLIENT_SECRET)
        
        # Use file-based token storage for persistence
        token_backend = FileSystemTokenBackend(token_path='.', token_filename='o365_token.txt')
        
        self.account = Account(
            credentials,
            tenant_id=config.OUTLOOK_TENANT_ID,
            token_backend=token_backend
        )

        # Authenticate if needed
        if not self.account.is_authenticated:
            # For server-side apps, you'll need to implement OAuth flow
            # This is a placeholder - actual implementation depends on auth method
            if self.account.authenticate(scopes=config.OUTLOOK_SCOPES):
                logger.info("Outlook Calendar authenticated successfully")
            else:
                raise IntegrationError("Failed to authenticate with Outlook Calendar")

    def create_action_item_events(
        self,
        action_items: List[Dict],
        meeting_title: str,
        calendar_name: str = None
    ) -> List[Dict]:
        """
        Create Outlook calendar events for action items with due dates

        Args:
            action_items: List of action item dictionaries
            meeting_title: Title of the meeting
            calendar_name: Calendar name (default: default calendar)

        Returns:
            List of created event IDs and links
        """
        schedule = self.account.schedule()
        calendar = schedule.get_default_calendar() if not calendar_name else schedule.get_calendar(calendar_name=calendar_name)

        if not calendar:
            raise IntegrationError("Could not access Outlook calendar")

        created_events = []

        for item in action_items:
            if not item.get('due_date'):
                continue

            try:
                # Parse due date
                due_date = datetime.strptime(item['due_date'], '%Y-%m-%d')

                # Create event
                event = calendar.new_event()
                event.subject = f"[Action Item] {item.get('description', 'No description')[:100]}"
                event.body = self._format_action_item_description(item, meeting_title)
                
                # Set as all-day event on due date
                event.start = due_date
                event.end = due_date + timedelta(hours=1)  # 1-hour duration
                event.is_all_day = True

                # Set reminder for 24 hours before (1 day = 1440 minutes)
                event.remind_before_minutes = 1440

                # Add attendee if owner email is available
                if item.get('owner') and '@' in item['owner']:
                    event.attendees.add(item['owner'])

                # Save event
                event.save()

                created_events.append({
                    'action_item': item['description'],
                    'event_id': event.object_id,
                    'event_link': event.web_link if hasattr(event, 'web_link') else None,
                    'due_date': item['due_date']
                })

                logger.info(f"Created Outlook calendar event for action item: {item['description'][:50]}")

            except Exception as e:
                logger.error(f"Error creating Outlook calendar event: {str(e)}")
                continue

        return created_events

    def update_event_on_completion(
        self,
        event_id: str,
        completed: bool = True,
        calendar_name: str = None
    ) -> bool:
        """
        Update or delete calendar event when task is completed

        Args:
            event_id: Event ID to update/delete
            completed: If True, mark as completed or delete
            calendar_name: Calendar name (default: default calendar)

        Returns:
            True if successful, False otherwise
        """
        try:
            schedule = self.account.schedule()
            calendar = schedule.get_default_calendar() if not calendar_name else schedule.get_calendar(calendar_name=calendar_name)

            if not calendar:
                logger.error("Could not access Outlook calendar")
                return False

            # Get the event
            event = calendar.get_event(event_id)
            
            if not event:
                logger.warning(f"Event {event_id} not found")
                return False

            if completed:
                # Option 1: Delete the event
                event.delete()
                logger.info(f"Deleted completed event: {event_id}")
                
                # Option 2: Update subject to mark as complete (uncomment to use instead)
                # event.subject = f"[COMPLETED] {event.subject}"
                # event.save()
                # logger.info(f"Marked event as completed: {event_id}")

            return True

        except Exception as e:
            logger.error(f"Error updating Outlook event: {str(e)}")
            return False

    def _format_action_item_description(self, item: Dict, meeting_title: str) -> str:
        """Format action item as calendar event description"""
        description = f"Action Item from Meeting: {meeting_title}\n\n"
        description += f"Task: {item.get('description', 'N/A')}\n"
        description += f"Owner: {item.get('owner', 'Unassigned')}\n"
        description += f"Priority: {item.get('priority', 'Medium')}\n"
        description += f"Due Date: {item.get('due_date', 'Not specified')}\n"

        if item.get('context'):
            description += f"\nContext:\n{item['context']}\n"

        return description


class JiraIntegration:
    """Jira integration for action item tracking"""

    def __init__(self, config: Config):
        self.config = config

        if not all([config.JIRA_SERVER, config.JIRA_EMAIL, config.JIRA_API_TOKEN]):
            raise IntegrationError("Jira credentials not fully configured")

        try:
            self.client = JIRA(
                server=config.JIRA_SERVER,
                basic_auth=(config.JIRA_EMAIL, config.JIRA_API_TOKEN)
            )
            logger.info("Jira client initialized successfully")
        except Exception as e:
            raise IntegrationError(f"Failed to initialize Jira client: {str(e)}")

    def sync_action_items(
        self,
        action_items: List[Dict],
        project_key: str,
        meeting_title: str,
        issue_type: str = 'Task'
    ) -> List[Dict]:
        """
        Sync action items to Jira as issues

        Args:
            action_items: List of action items
            project_key: Jira project key
            meeting_title: Meeting title
            issue_type: Jira issue type (default: Task)

        Returns:
            List of created Jira issues
        """
        created_issues = []

        for item in action_items:
            try:
                # Create issue
                issue_dict = {
                    'project': {'key': project_key},
                    'summary': item.get('description', 'No description')[:255],
                    'description': self._format_jira_description(item, meeting_title),
                    'issuetype': {'name': issue_type},
                }

                # Set priority
                priority_mapping = {
                    'high': 'High',
                    'medium': 'Medium',
                    'low': 'Low'
                }
                if item.get('priority'):
                    issue_dict['priority'] = {'name': priority_mapping.get(item['priority'].lower(), 'Medium')}

                # Set due date
                if item.get('due_date'):
                    issue_dict['duedate'] = item['due_date']

                # Assign to owner if email matches a Jira user
                if item.get('owner'):
                    try:
                        users = self.client.search_users(item['owner'])
                        if users:
                            issue_dict['assignee'] = {'name': users[0].name}
                    except:
                        pass

                # Create the issue
                new_issue = self.client.create_issue(fields=issue_dict)

                created_issues.append({
                    'action_item': item['description'],
                    'jira_key': new_issue.key,
                    'jira_url': f"{self.config.JIRA_SERVER}/browse/{new_issue.key}",
                    'status': 'Created'
                })

                logger.info(f"Created Jira issue: {new_issue.key}")

            except Exception as e:
                logger.error(f"Error creating Jira issue: {str(e)}")
                continue

        return created_issues

    def _format_jira_description(self, item: Dict, meeting_title: str) -> str:
        """Format action item as Jira description"""
        description = f"h3. Action Item from Meeting: {meeting_title}\n\n"
        description += f"*Task:* {item.get('description', 'N/A')}\n"
        description += f"*Owner:* {item.get('owner', 'Unassigned')}\n"
        description += f"*Priority:* {item.get('priority', 'Medium')}\n"
        description += f"*Due Date:* {item.get('due_date', 'Not specified')}\n"

        if item.get('context'):
            description += f"\n*Context:*\n{item['context']}\n"

        if item.get('source_text'):
            description += f"\n*Source Quote:*\n{{quote}}{item['source_text']}{{quote}}\n"

        return description

    def get_project_keys(self) -> List[str]:
        """Get list of accessible Jira project keys"""
        try:
            projects = self.client.projects()
            return [p.key for p in projects]
        except Exception as e:
            logger.error(f"Error retrieving Jira projects: {str(e)}")
            return []


class AsanaIntegration:
    """Asana integration for action item tracking"""

    def __init__(self, config: Config):
        self.config = config

        if not config.ASANA_ACCESS_TOKEN:
            raise IntegrationError("Asana access token not configured")

        try:
            self.client = asana.Client.access_token(config.ASANA_ACCESS_TOKEN)
            logger.info("Asana client initialized successfully")
        except Exception as e:
            raise IntegrationError(f"Failed to initialize Asana client: {str(e)}")

    def sync_action_items(
        self,
        action_items: List[Dict],
        project_gid: str,
        meeting_title: str
    ) -> List[Dict]:
        """
        Sync action items to Asana as tasks

        Args:
            action_items: List of action items
            project_gid: Asana project GID
            meeting_title: Meeting title

        Returns:
            List of created Asana tasks
        """
        created_tasks = []

        for item in action_items:
            try:
                # Create task
                task_data = {
                    'name': item.get('description', 'No description')[:1024],
                    'notes': self._format_asana_notes(item, meeting_title),
                    'projects': [project_gid],
                }

                # Set due date
                if item.get('due_date'):
                    task_data['due_on'] = item['due_date']

                # Create the task
                result = self.client.tasks.create_task(task_data)

                created_tasks.append({
                    'action_item': item['description'],
                    'asana_gid': result['gid'],
                    'asana_url': result.get('permalink_url'),
                    'status': 'Created'
                })

                logger.info(f"Created Asana task: {result['gid']}")

            except Exception as e:
                logger.error(f"Error creating Asana task: {str(e)}")
                continue

        return created_tasks

    def _format_asana_notes(self, item: Dict, meeting_title: str) -> str:
        """Format action item as Asana task notes"""
        notes = f"Action Item from Meeting: {meeting_title}\n\n"
        notes += f"Owner: {item.get('owner', 'Unassigned')}\n"
        notes += f"Priority: {item.get('priority', 'Medium')}\n"
        notes += f"Due Date: {item.get('due_date', 'Not specified')}\n"

        if item.get('context'):
            notes += f"\nContext:\n{item['context']}\n"

        if item.get('source_text'):
            notes += f"\nSource Quote:\n\"{item['source_text']}\"\n"

        return notes

    def get_workspaces(self) -> List[Dict]:
        """Get list of accessible Asana workspaces"""
        try:
            workspaces = self.client.workspaces.get_workspaces()
            return [{'gid': w['gid'], 'name': w['name']} for w in workspaces]
        except Exception as e:
            logger.error(f"Error retrieving Asana workspaces: {str(e)}")
            return []

    def get_projects(self, workspace_gid: str) -> List[Dict]:
        """Get list of projects in a workspace"""
        try:
            projects = self.client.projects.get_projects({'workspace': workspace_gid})
            return [{'gid': p['gid'], 'name': p['name']} for p in projects]
        except Exception as e:
            logger.error(f"Error retrieving Asana projects: {str(e)}")
            return []
