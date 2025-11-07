"""
Unit tests for Gemini AI Agent
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from src.services.gemini_agent import GeminiAgent, GeminiAgentError
from src.config import DevelopmentConfig


@pytest.fixture
def config():
    """Create test configuration"""
    config = DevelopmentConfig
    config.GEMINI_API_KEY = 'test-api-key'
    return config


@pytest.fixture
def gemini_agent(config):
    """Create GeminiAgent instance"""
    with patch('src.services.gemini_agent.genai'):
        return GeminiAgent(config)


@pytest.fixture
def sample_transcript():
    """Sample meeting transcript for testing"""
    return """
    John: Good morning everyone. Let's start with the project status.
    Sarah: The frontend is 80% complete. I'll finish it by Friday.
    John: Great. What about the backend API?
    Mike: I need to implement the authentication module. Can we schedule a review session?
    John: Sure, let's meet on Wednesday. Sarah, can you help Mike with the API integration?
    Sarah: Yes, I'll look into that tomorrow.
    John: Perfect. One more thing - we need to decide on the deployment platform.
    Mike: I recommend using Google Cloud Platform.
    John: Agreed. Let's go with GCP. Meeting adjourned.
    """


class TestGeminiAgent:
    """Test cases for GeminiAgent"""

    def test_initialization_success(self, config):
        """Test successful GeminiAgent initialization"""
        with patch('src.services.gemini_agent.genai') as mock_genai:
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model

            agent = GeminiAgent(config)

            assert agent.config == config
            mock_genai.configure.assert_called_once_with(api_key='test-api-key')

    def test_initialization_no_api_key(self):
        """Test initialization without API key"""
        config = DevelopmentConfig
        config.GEMINI_API_KEY = None

        with pytest.raises(GeminiAgentError, match="GEMINI_API_KEY not configured"):
            GeminiAgent(config)

    @patch('src.services.gemini_agent.genai')
    def test_extract_action_items(self, mock_genai, config, sample_transcript):
        """Test action item extraction"""
        # Setup mock
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps([
            {
                "description": "Finish frontend by Friday",
                "owner": "Sarah",
                "due_date": "2025-11-10",
                "priority": "high",
                "confidence": 0.95,
                "context": "Frontend is 80% complete",
                "source_text": "I'll finish it by Friday"
            },
            {
                "description": "Implement authentication module",
                "owner": "Mike",
                "due_date": "Not specified",
                "priority": "high",
                "confidence": 0.90,
                "context": "Backend API work",
                "source_text": "I need to implement the authentication module"
            }
        ])
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        agent = GeminiAgent(config)
        action_items = agent.extract_action_items(sample_transcript)

        assert len(action_items) == 2
        assert action_items[0]['owner'] == 'Sarah'
        assert action_items[1]['owner'] == 'Mike'
        assert all(item['confidence'] >= 0.7 for item in action_items)

    @patch('src.services.gemini_agent.genai')
    def test_extract_decisions(self, mock_genai, config, sample_transcript):
        """Test decision extraction"""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps([
            {
                "decision": "Use Google Cloud Platform for deployment",
                "rationale": "Team agreement on cloud infrastructure",
                "impact": "Sets deployment architecture",
                "stakeholders": ["John", "Mike"],
                "source_text": "Agreed. Let's go with GCP"
            }
        ])
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        agent = GeminiAgent(config)
        decisions = agent.extract_decisions(sample_transcript)

        assert len(decisions) == 1
        assert 'Google Cloud Platform' in decisions[0]['decision']

    @patch('src.services.gemini_agent.genai')
    def test_extract_implicit_commitments(self, mock_genai, config, sample_transcript):
        """Test implicit commitment extraction"""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps([
            {
                "commitment": "Help with API integration",
                "person": "Sarah",
                "source_text": "Yes, I'll look into that tomorrow",
                "confidence": 0.88
            }
        ])
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        agent = GeminiAgent(config)
        commitments = agent.extract_implicit_commitments(sample_transcript)

        assert len(commitments) == 1
        assert commitments[0]['person'] == 'Sarah'
        assert commitments[0]['confidence'] >= 0.8

    @patch('src.services.gemini_agent.genai')
    def test_generate_executive_summary(self, mock_genai, config, sample_transcript):
        """Test executive summary generation"""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "overview": "Project status meeting discussing frontend completion, backend work, and deployment decisions.",
            "key_outcomes": [
                "Frontend 80% complete, finishing by Friday",
                "Decided on Google Cloud Platform for deployment",
                "API integration help arranged"
            ],
            "critical_action_items": [
                "Sarah: Complete frontend by Friday",
                "Mike: Implement authentication module"
            ],
            "risks_or_blockers": [],
            "next_meeting": "Wednesday for review session"
        })
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        agent = GeminiAgent(config)
        summary = agent.generate_executive_summary(sample_transcript)

        assert 'overview' in summary
        assert 'key_outcomes' in summary
        assert len(summary['key_outcomes']) > 0

    @patch('src.services.gemini_agent.genai')
    def test_analyze_transcript(self, mock_genai, config, sample_transcript):
        """Test full transcript analysis"""
        mock_model = MagicMock()

        # Mock responses for all extraction methods
        def mock_generate(prompt):
            response = MagicMock()
            if 'action items' in prompt.lower():
                response.text = json.dumps([{"description": "Test action", "confidence": 0.9}])
            elif 'decisions' in prompt.lower():
                response.text = json.dumps([{"decision": "Test decision"}])
            elif 'topics' in prompt.lower():
                response.text = json.dumps([{"topic": "Test topic"}])
            elif 'questions' in prompt.lower():
                response.text = json.dumps([{"question": "Test question"}])
            elif 'implicit' in prompt.lower():
                response.text = json.dumps([{"commitment": "Test commitment", "confidence": 0.85}])
            elif 'summary' in prompt.lower():
                response.text = json.dumps({"overview": "Test overview"})
            else:
                response.text = json.dumps({})
            return response

        mock_model.generate_content = mock_generate
        mock_genai.GenerativeModel.return_value = mock_model

        agent = GeminiAgent(config)
        analysis = agent.analyze_transcript(sample_transcript)

        assert 'action_items' in analysis
        assert 'decisions' in analysis
        assert 'key_topics' in analysis
        assert 'open_questions' in analysis
        assert 'implicit_commitments' in analysis
        assert 'executive_summary' in analysis

    @patch('src.services.gemini_agent.genai')
    def test_parse_json_response_with_markdown(self, mock_genai, config):
        """Test JSON parsing with markdown code blocks"""
        agent = GeminiAgent(config)

        # Test with markdown code blocks
        response_text = """```json
        [{"test": "value"}]
        ```"""

        result = agent._parse_json_response(response_text)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['test'] == 'value'

    @patch('src.services.gemini_agent.genai')
    def test_infer_due_dates(self, mock_genai, config):
        """Test due date inference for action items"""
        agent = GeminiAgent(config)

        action_items = [
            {"description": "High priority task", "priority": "high", "due_date": "Not specified"},
            {"description": "Low priority task", "priority": "low"},
            {"description": "Medium priority task", "priority": "medium"},
        ]

        result = agent._infer_due_dates(action_items)

        # High priority should get 3 days
        assert result[0]['due_date_inferred'] is True
        # All should have due dates
        assert all('due_date' in item for item in result)

    @patch('src.services.gemini_agent.genai')
    def test_custom_query(self, mock_genai, config, sample_transcript):
        """Test custom query about transcript"""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "The meeting discussed project status and deployment platform."
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        agent = GeminiAgent(config)
        answer = agent.generate_custom_query(sample_transcript, "What was discussed in the meeting?")

        assert len(answer) > 0
        assert isinstance(answer, str)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
