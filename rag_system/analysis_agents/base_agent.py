"""
Base Analysis Agent
===================

Base class for all section-specific analysis agents.
Provides common functionality for Grok-4 integration and structured output.
"""

from typing import Dict, Optional
import json
import time
from openai import OpenAI
import config


class BaseAnalysisAgent:
    """Base class for all section analysis agents"""

    def __init__(self, agent_name: str, section_name: str):
        """
        Initialize base agent

        Args:
            agent_name: Name of the agent (e.g., "AbstractAgent")
            section_name: Name of the section to analyze (e.g., "Abstract")
        """
        self.agent_name = agent_name
        self.section_name = section_name
        self.status = "initialized"

        # Initialize Grok client
        self.client = OpenAI(
            api_key=config.GROK_SETTINGS['api_key'],
            base_url="https://api.x.ai/v1"
        )

    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.
        Should be overridden by subclasses.

        Returns:
            System prompt string
        """
        raise NotImplementedError("Subclasses must implement get_system_prompt()")

    def get_user_prompt(self, section_text: str, paper_metadata: Dict) -> str:
        """
        Get the user prompt for this agent.
        Should be overridden by subclasses.

        Args:
            section_text: Text of the section to analyze
            paper_metadata: Dictionary with title, authors, year, etc.

        Returns:
            User prompt string
        """
        raise NotImplementedError("Subclasses must implement get_user_prompt()")

    def parse_response(self, response_text: str) -> Dict:
        """
        Parse the LLM response into structured data.
        Default implementation assumes JSON response.

        Args:
            response_text: Raw response from LLM

        Returns:
            Parsed dictionary
        """
        try:
            # Try to parse as JSON
            # Handle markdown code blocks
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]  # Remove ```json
            if text.startswith("```"):
                text = text[3:]  # Remove ```
            if text.endswith("```"):
                text = text[:-3]  # Remove trailing ```
            text = text.strip()

            return json.loads(text)
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return raw text
            return {
                "raw_response": response_text,
                "parse_error": str(e),
                "section": self.section_name
            }

    def analyze(
        self,
        section_text: str,
        paper_metadata: Optional[Dict] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000
    ) -> Dict:
        """
        Analyze a section of the paper using Grok-4

        Args:
            section_text: Text of the section to analyze
            paper_metadata: Optional metadata (title, authors, year, etc.)
            temperature: LLM temperature (0.0-1.0)
            max_tokens: Maximum tokens in response

        Returns:
            Dictionary with analysis results:
            {
                'success': bool,
                'agent_name': str,
                'section_name': str,
                'analysis': Dict (parsed response),
                'raw_response': str,
                'elapsed_time': float,
                'message': str
            }
        """
        start_time = time.time()
        self.status = "analyzing"

        try:
            # Prepare metadata
            if paper_metadata is None:
                paper_metadata = {}

            # Get prompts
            system_prompt = self.get_system_prompt()
            user_prompt = self.get_user_prompt(section_text, paper_metadata)

            # Call Grok-4
            response = self.client.chat.completions.create(
                model="grok-2-latest",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Extract response
            raw_response = response.choices[0].message.content

            # Parse response
            parsed_analysis = self.parse_response(raw_response)

            elapsed_time = time.time() - start_time
            self.status = "completed"

            return {
                'success': True,
                'agent_name': self.agent_name,
                'section_name': self.section_name,
                'analysis': parsed_analysis,
                'raw_response': raw_response,
                'elapsed_time': elapsed_time,
                'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else None,
                'message': f'{self.section_name} analysis completed successfully'
            }

        except Exception as e:
            elapsed_time = time.time() - start_time
            self.status = "failed"

            return {
                'success': False,
                'agent_name': self.agent_name,
                'section_name': self.section_name,
                'analysis': {},
                'raw_response': '',
                'elapsed_time': elapsed_time,
                'tokens_used': None,
                'message': f'Error analyzing {self.section_name}: {str(e)}'
            }

    def get_metrics(self) -> Dict:
        """Get agent performance metrics"""
        return {
            'agent_name': self.agent_name,
            'section_name': self.section_name,
            'status': self.status
        }
