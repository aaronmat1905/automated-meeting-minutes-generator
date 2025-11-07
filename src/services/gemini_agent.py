"""
Gemini AI Agent Service
Extracts action items, decisions, and insights from meeting transcripts
"""

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import re

import google.generativeai as genai

from src.config import Config

logger = logging.getLogger(__name__)


class GeminiAgentError(Exception):
    """Custom exception for Gemini agent errors"""
    pass


class GeminiAgent:
    """AI Agent for analyzing meeting transcripts using Google Gemini"""

    def __init__(self, config: Config):
        self.config = config

        # Configure Gemini API
        if not config.GEMINI_API_KEY:
            raise GeminiAgentError("GEMINI_API_KEY not configured")

        genai.configure(api_key=config.GEMINI_API_KEY)

        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=config.GEMINI_MODEL,
            generation_config={
                'temperature': config.GEMINI_TEMPERATURE,
                'max_output_tokens': config.GEMINI_MAX_OUTPUT_TOKENS,
            }
        )

    def analyze_transcript(
        self,
        transcript: str,
        meeting_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Perform comprehensive analysis of meeting transcript

        Args:
            transcript: Full meeting transcript
            meeting_metadata: Optional meeting metadata (title, agenda, participants)

        Returns:
            Dictionary containing analysis results
        """
        try:
            logger.info("Starting transcript analysis with Gemini...")

            # Extract different components in parallel for efficiency
            action_items = self.extract_action_items(transcript, meeting_metadata)
            decisions = self.extract_decisions(transcript)
            key_topics = self.extract_key_topics(transcript)
            questions = self.extract_open_questions(transcript)
            commitments = self.extract_implicit_commitments(transcript)
            summary = self.generate_executive_summary(transcript, meeting_metadata)

            result = {
                'action_items': action_items,
                'decisions': decisions,
                'key_topics': key_topics,
                'open_questions': questions,
                'implicit_commitments': commitments,
                'executive_summary': summary,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }

            logger.info("Transcript analysis completed successfully")
            return result

        except Exception as e:
            logger.error(f"Error analyzing transcript: {str(e)}")
            raise GeminiAgentError(f"Failed to analyze transcript: {str(e)}")

    def extract_action_items(
        self,
        transcript: str,
        meeting_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Extract action items with owners and due dates

        Args:
            transcript: Meeting transcript
            meeting_metadata: Optional meeting metadata

        Returns:
            List of action item dictionaries
        """
        context = self._build_context(meeting_metadata)

        prompt = f"""
{context}

Analyze the following meeting transcript and extract ALL action items. An action item is a specific task
that someone needs to complete after the meeting.

For each action item, provide:
1. **description**: Clear, actionable description of the task
2. **owner**: Person responsible (extract from context like "John will...", "Can Sarah...", etc.)
3. **due_date**: Due date if mentioned (extract from phrases like "by Friday", "end of month", "next week")
4. **priority**: Estimated priority (high/medium/low) based on context and urgency
5. **context**: Relevant context or discussion that led to this action item
6. **confidence**: Your confidence score (0.0-1.0) in this extraction
7. **source_text**: The exact quote from the transcript that indicates this action item

Return ONLY a valid JSON array of action items. Do not include any explanatory text.

TRANSCRIPT:
{transcript}

JSON OUTPUT:
"""

        try:
            response = self.model.generate_content(prompt)
            action_items = self._parse_json_response(response.text)

            # Auto-assign owners when missing using transcript heuristics
            action_items = self._assign_owners(action_items, transcript, meeting_metadata)

            # Auto-assign due dates for items without explicit dates
            action_items = self._infer_due_dates(action_items)

            # Filter by confidence threshold
            action_items = [item for item in action_items if item.get('confidence', 0) >= 0.7]

            logger.info(f"Extracted {len(action_items)} action items")
            return action_items

        except Exception as e:
            logger.error(f"Error extracting action items: {str(e)}")
            return []

    def extract_decisions(self, transcript: str) -> List[Dict]:
        """
        Extract key decisions made during the meeting

        Args:
            transcript: Meeting transcript

        Returns:
            List of decision dictionaries
        """
        prompt = f"""
Analyze the following meeting transcript and extract all KEY DECISIONS that were made.

For each decision, provide:
1. **decision**: Clear statement of what was decided
2. **rationale**: Why this decision was made (if discussed)
3. **impact**: Potential impact or implications
4. **stakeholders**: People or teams affected by this decision
5. **source_text**: The exact quote from the transcript

Return ONLY a valid JSON array. No explanatory text.

TRANSCRIPT:
{transcript}

JSON OUTPUT:
"""

        try:
            response = self.model.generate_content(prompt)
            decisions = self._parse_json_response(response.text)
            logger.info(f"Extracted {len(decisions)} decisions")
            return decisions

        except Exception as e:
            logger.error(f"Error extracting decisions: {str(e)}")
            return []

    def extract_key_topics(self, transcript: str) -> List[Dict]:
        """
        Extract key topics discussed in the meeting

        Args:
            transcript: Meeting transcript

        Returns:
            List of topic dictionaries
        """
        prompt = f"""
Analyze the following meeting transcript and identify the KEY TOPICS that were discussed.

For each topic, provide:
1. **topic**: Name of the topic
2. **summary**: Brief summary of the discussion (2-3 sentences)
3. **duration**: Estimated time spent on this topic (if discernible)
4. **participants**: Key participants in this discussion
5. **outcome**: What was resolved or next steps for this topic

Return ONLY a valid JSON array. No explanatory text.

TRANSCRIPT:
{transcript}

JSON OUTPUT:
"""

        try:
            response = self.model.generate_content(prompt)
            topics = self._parse_json_response(response.text)
            logger.info(f"Extracted {len(topics)} key topics")
            return topics

        except Exception as e:
            logger.error(f"Error extracting key topics: {str(e)}")
            return []

    def extract_open_questions(self, transcript: str) -> List[Dict]:
        """
        Extract open questions and unresolved issues

        Args:
            transcript: Meeting transcript

        Returns:
            List of open question dictionaries
        """
        prompt = f"""
Analyze the following meeting transcript and identify OPEN QUESTIONS and UNRESOLVED ISSUES
that need follow-up.

For each open question/issue, provide:
1. **question**: The question or issue that remains open
2. **context**: Context or discussion around this question
3. **who_needs_to_answer**: Person or team who should address this
4. **urgency**: Urgency level (high/medium/low)
5. **source_text**: The exact quote from the transcript

Return ONLY a valid JSON array. No explanatory text.

TRANSCRIPT:
{transcript}

JSON OUTPUT:
"""

        try:
            response = self.model.generate_content(prompt)
            questions = self._parse_json_response(response.text)
            logger.info(f"Extracted {len(questions)} open questions")
            return questions

        except Exception as e:
            logger.error(f"Error extracting open questions: {str(e)}")
            return []

    def extract_implicit_commitments(self, transcript: str) -> List[Dict]:
        """
        Extract implicit commitments (e.g., "I'll look into that", "Let me check")

        Args:
            transcript: Meeting transcript

        Returns:
            List of implicit commitment dictionaries
        """
        prompt = f"""
Analyze the following meeting transcript and identify IMPLICIT COMMITMENTS - phrases where
someone verbally commits to doing something but it wasn't formalized as an action item.

Look for phrases like:
- "I'll look into that"
- "Let me check"
- "I can take care of that"
- "I'll get back to you"
- "I'll follow up"

For each implicit commitment, provide:
1. **commitment**: What the person committed to do
2. **person**: Who made the commitment
3. **source_text**: The exact quote from the transcript
4. **confidence**: Your confidence score (0.0-1.0)

Return ONLY a valid JSON array. No explanatory text.

TRANSCRIPT:
{transcript}

JSON OUTPUT:
"""

        try:
            response = self.model.generate_content(prompt)
            commitments = self._parse_json_response(response.text)

            # Filter by confidence
            commitments = [c for c in commitments if c.get('confidence', 0) >= 0.8]

            logger.info(f"Extracted {len(commitments)} implicit commitments")
            return commitments

        except Exception as e:
            logger.error(f"Error extracting implicit commitments: {str(e)}")
            return []

    def generate_executive_summary(
        self,
        transcript: str,
        meeting_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Generate executive summary of the meeting

        Args:
            transcript: Meeting transcript
            meeting_metadata: Optional meeting metadata

        Returns:
            Dictionary containing executive summary components
        """
        context = self._build_context(meeting_metadata)

        prompt = f"""
{context}

Create a concise EXECUTIVE SUMMARY of this meeting suitable for leadership review.

Provide the following in JSON format:
1. **overview**: 2-3 sentence overview of the meeting (what was discussed and why)
2. **key_outcomes**: List of 3-5 most important outcomes or takeaways
3. **critical_action_items**: Top 3-5 most critical action items with owners
4. **risks_or_blockers**: Any risks, concerns, or blockers mentioned
5. **next_meeting**: Information about next steps or follow-up meetings if mentioned

Keep the summary professional, concise (100-150 words for overview), and focused on
what executives need to know.

Return ONLY valid JSON. No explanatory text.

TRANSCRIPT:
{transcript}

JSON OUTPUT:
"""

        try:
            response = self.model.generate_content(prompt)
            summary = self._parse_json_response(response.text)

            logger.info("Generated executive summary")
            return summary

        except Exception as e:
            logger.error(f"Error generating executive summary: {str(e)}")
            return {
                'overview': 'Summary generation failed',
                'key_outcomes': [],
                'critical_action_items': [],
                'risks_or_blockers': [],
                'next_meeting': None
            }

    def analyze_sentiment(self, transcript: str) -> Dict:
        """
        Analyze overall sentiment and tone of the meeting

        Args:
            transcript: Meeting transcript

        Returns:
            Sentiment analysis results
        """
        prompt = f"""
Analyze the overall SENTIMENT and TONE of this meeting.

Provide:
1. **overall_sentiment**: Overall sentiment (positive/neutral/negative)
2. **tone**: Tone of the meeting (collaborative/confrontational/productive/chaotic/etc.)
3. **engagement_level**: Perceived engagement level (high/medium/low)
4. **concerns**: Any notable concerns or tensions
5. **highlights**: Positive highlights or moments

Return ONLY valid JSON.

TRANSCRIPT:
{transcript}

JSON OUTPUT:
"""

        try:
            response = self.model.generate_content(prompt)
            sentiment = self._parse_json_response(response.text)
            return sentiment

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {}

    def _build_context(self, meeting_metadata: Optional[Dict]) -> str:
        """Build context string from meeting metadata"""
        if not meeting_metadata:
            return "CONTEXT: General meeting"

        context_parts = ["CONTEXT:"]

        if meeting_metadata.get('title'):
            context_parts.append(f"Meeting: {meeting_metadata['title']}")

        if meeting_metadata.get('participants'):
            participants = ', '.join(meeting_metadata['participants'])
            context_parts.append(f"Participants: {participants}")

        if meeting_metadata.get('agenda'):
            context_parts.append(f"Agenda: {meeting_metadata['agenda']}")

        if meeting_metadata.get('date'):
            context_parts.append(f"Date: {meeting_metadata['date']}")

        return '\n'.join(context_parts)

    def _parse_json_response(self, response_text: str) -> any:
        """
        Parse JSON from Gemini response, handling common formatting issues

        Args:
            response_text: Raw response text from Gemini

        Returns:
            Parsed JSON object
        """
        # Remove markdown code blocks if present
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)

        # Remove any leading/trailing whitespace
        response_text = response_text.strip()

        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            logger.debug(f"Response text: {response_text[:500]}")

            # Try to extract JSON from response
            json_match = re.search(r'\[.*\]|\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass

            # Return empty structure based on expected type
            if response_text.strip().startswith('['):
                return []
            else:
                return {}

    def _infer_due_dates(self, action_items: List[Dict]) -> List[Dict]:
        """
        Infer due dates for action items that don't have explicit dates

        Args:
            action_items: List of action items

        Returns:
            Action items with inferred due dates
        """
        for item in action_items:
            if not item.get('due_date') or item['due_date'] == 'Not specified':
                # Default to 7 days from now if no due date specified
                priority = item.get('priority', 'medium').lower()

                if priority == 'high':
                    days_ahead = 3
                elif priority == 'low':
                    days_ahead = 14
                else:
                    days_ahead = 7

                due_date = datetime.now() + timedelta(days=days_ahead)
                item['due_date'] = due_date.strftime('%Y-%m-%d')
                item['due_date_inferred'] = True
            else:
                item['due_date_inferred'] = False

        return action_items

    def _assign_owners(
        self,
        action_items: List[Dict],
        transcript: str,
        meeting_metadata: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Try to infer owners for action items when the owner field is missing or unassigned.

        Heuristics used (in order):
        - If source_text includes an email, use that as owner
        - Match speaker lines in the transcript like 'Sarah: I'll do X' and map that speaker
          to action items whose source_text appears in the same line
        - Use simple regexes to find patterns like 'Can Sarah', 'Sarah will', 'assign to Mike'
        - Match against meeting participants (if provided)

        This function sets `owner` and `owner_inferred` flags when it infers an owner.
        """

        participants = []
        if meeting_metadata and meeting_metadata.get('participants'):
            participants = meeting_metadata.get('participants')

        # Pre-scan transcript lines for speaker: content patterns
        lines = [l.strip() for l in transcript.splitlines() if l.strip()]

        for item in action_items:
            owner = item.get('owner')
            if owner and str(owner).strip() and str(owner).lower() not in ('unassigned', 'none', 'not specified'):
                item['owner_inferred'] = False
                continue

            source_text = (item.get('source_text') or '').strip()
            text_blob = (source_text + '\n' + transcript).strip()

            # 1) email address in source_text or transcript
            email_match = re.search(r"[\w\.-]+@[\w\.-]+", text_blob)
            if email_match:
                item['owner'] = email_match.group(0)
                item['owner_inferred'] = True
                continue

            # 2) match speaker lines like 'Sarah: I'll do X' and that line contains the source_text
            matched = False
            for line in lines:
                m = re.match(r"^([A-Z][A-Za-z0-9_\-]+)\s*:\s*(.*)$", line)
                if m:
                    speaker = m.group(1)
                    content = m.group(2)
                    # if the source_text appears verbatim in the speaker's content, attribute to speaker
                    if source_text and source_text in content:
                        item['owner'] = speaker
                        item['owner_inferred'] = True
                        matched = True
                        break
                    # if content contains common ownership verbs and the speaker is mentioned, attribute
                    if re.search(r"\b(will|can you|i'll|i will|let me|assign|i can)\b", content, re.I):
                        # if source_text shares words with content (simple overlap), attribute
                        if source_text and len(set(source_text.lower().split()) & set(content.lower().split())) >= 2:
                            item['owner'] = speaker
                            item['owner_inferred'] = True
                            matched = True
                            break
            if matched:
                continue

            # 3) check participants list
            for p in participants:
                if re.search(r"\b" + re.escape(p) + r"\b", text_blob, re.I):
                    item['owner'] = p
                    item['owner_inferred'] = True
                    matched = True
                    break
            if matched:
                continue

            # 4) regex patterns in source_text / transcript
            name_patterns = [
                r"\b([A-Z][a-z]{2,}(?:\s[A-Z][a-z]{2,})?)\s+(?:will|shall|can|to|is going to|is going)\b",
                r"\bcan\s+([A-Z][a-z]{2,})\b",
                r"assign(?:ed)? to\s+([A-Z][a-z]{2,})\b",
            ]

            for pat in name_patterns:
                m = re.search(pat, text_blob)
                if m:
                    candidate = m.group(1)
                    item['owner'] = candidate
                    item['owner_inferred'] = True
                    matched = True
                    break

            if matched:
                continue

            # if no owner found, leave as Unassigned and mark inferred False
            item['owner'] = item.get('owner') or 'Unassigned'
            item['owner_inferred'] = False

        return action_items

    def generate_custom_query(self, transcript: str, query: str) -> str:
        """
        Answer a custom query about the meeting transcript

        Args:
            transcript: Meeting transcript
            query: User's question about the meeting

        Returns:
            Answer to the query
        """
        prompt = f"""
Based on the following meeting transcript, please answer this question:

QUESTION: {query}

Provide a clear, concise answer based only on information in the transcript.
If the information is not in the transcript, say so.

TRANSCRIPT:
{transcript}

ANSWER:
"""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()

        except Exception as e:
            logger.error(f"Error processing custom query: {str(e)}")
            return f"Error processing query: {str(e)}"
