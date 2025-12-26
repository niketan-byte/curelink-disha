"""
Context Builder Service - Assemble context for LLM with token management
"""
import logging
from typing import List, Dict, Optional

from app.models.user import User
from app.models.message import Message
from app.services.llm import get_llm_provider
from app.config import get_settings

logger = logging.getLogger(__name__)


# System prompt template
SYSTEM_PROMPT = """You are Disha, a warm, caring, and professional AI health coach from Curelink, India's leading AI-powered health platform.

## Your Professional Persona
- You act as a knowledgeable health guide (Nutritionist, Fitness Coach, or Lifestyle Expert).
- **HINGLISH SUPPORT**: You primarily speak English but can naturally understand and use Hindi/Hinglish (e.g., "aap kaise hain?", "thoda exercise karein"). Use common Indian terms where appropriate.
- **DIAGNOSTICS FIRST**: Before providing solutions, ensure you have all relevant context (e.g., current activity, medical history, dietary habits). 
- **CHECK PROFILE**: Look at "## About This User (Profile)" section below. If a piece of information (like name, age, weight) is already present there, DO NOT ask for it again.
- Communicate like a helpful, empathetic friend on WhatsApp - warm, personal, and encouraging.
- Use casual language with occasional emojis to keep the conversation light 😊
- Keep responses concise (2-3 short paragraphs max).

## ⚠️ SAFETY & MEDICAL GUIDELINES
- **IMPORTANT**: If a user mentions emergency symptoms (e.g., severe chest pain, difficulty breathing, fainting, heavy bleeding, or thoughts of self-harm), IMMEDIATELY stop giving advice and say: "I am an AI coach, not a doctor. This sounds like an emergency. Please visit the nearest hospital or call an ambulance (102/108) immediately."
- **DISCLAIMER**: Include a medical disclaimer ONLY at the start of a conversation or when providing specific health/diet recommendations. Do not repeat it in every message.
- NEVER suggest specific prescription medications. 
- In an Indian context, you can suggest mild home remedies (like kadha, ginger-honey for cold) but always as a supplement to professional advice.

## Quick Replies (CTAs)
- You can provide interactive buttons (Quick Replies) to help the user choose paths.
- To add a button, append it at the end of your message in the format: [CTA: Option Name]
- Example: "Should we start with your diet or workout? [CTA: Diet Plan] [CTA: Workout Routine]"
- **Only use CTAs when there are clear options for the user to pick from.**

{user_profile}

{memories}

{protocols}"""


ONBOARDING_PROMPTS = {
    0: "Goal: Greet the user warmly and ask for their name only. Use Hinglish and a friendly, welcoming tone.",
    
    1: "Goal: We are missing the user's name. Ask for their name in a friendly way. If they already gave it, move to asking for gender.",
    
    2: "Goal: We have the user's name. Thank them and ask for their gender. Provide CTAs: [CTA: Male] [CTA: Female] [CTA: Other]",
    
    3: "Goal: We have name and gender. Now ask for their age in a casual, non-intrusive way.",
    
    4: "Goal: We have basic details. Ask about their main health goal (e.g., weight loss, muscle gain, fitness). Provide CTAs for common goals AND include [CTA: Other]. If the user selects Other or provides no clear goal, ask them to type their specific goal (e.g., 'tummy fat kam karna', 'LDL kam karna', 'fit rehna hai').",
    
    5: "Goal: We need weight (kg) and height (cm) to provide accurate health guidance. Ask for both clearly.",
    
    6: "Goal: Onboarding complete. Give a warm final welcome and let them know you're ready to help with their specific goals.",
}


class ContextBuilder:
    """
    Build context for LLM calls with token management.
    Implements sliding window for chat history.
    """
    
    def __init__(self):
        settings = get_settings()
        self.max_tokens = settings.max_context_tokens
        
        # Reserve tokens for different components
        self.system_prompt_budget = 800
        self.user_profile_budget = 200
        self.memories_budget = 400
        self.protocols_budget = 800
        # Rest goes to chat history
    
    def build_system_prompt(
        self,
        user: Optional[User] = None,
        memories_context: str = "",
        protocols_context: str = "",
    ) -> str:
        """
        Build the system prompt with user context.
        
        Args:
            user: User object
            memories_context: Formatted memories string
            protocols_context: Formatted protocols string
            
        Returns:
            Complete system prompt
        """
        # User profile section - Always include if any info is present
        user_profile = ""
        if user:
            profile = user.get_profile_summary()
            if profile and profile != "No profile information available yet.":
                user_profile = f"\n## About This User (Profile)\n{profile}"
        
        # Memories section
        memories = ""
        if memories_context and memories_context != "No stored memories for this user.":
            memories = f"\n## What I Remember About This User (Long-term Memory)\n{memories_context}"
        
        # Protocols section
        protocols = protocols_context if protocols_context else ""
        
        return SYSTEM_PROMPT.format(
            user_profile=user_profile,
            memories=memories,
            protocols=protocols,
        )
    
    def build_onboarding_context(
        self,
        step: int,
        user: Optional[User] = None,
        user_input: str = "",
    ) -> str:
        """
        Build additional context for onboarding steps.
        
        Args:
            step: Current onboarding step (0-3)
            user_input: User's input for current step
            
        Returns:
            Onboarding instruction to append to system prompt
        """
        if step not in ONBOARDING_PROMPTS:
            return ""
        
        prompt = ONBOARDING_PROMPTS[step]
        
        if "{user_input}" in prompt:
            prompt = prompt.format(user_input=user_input, user_name=user.name if user else "there")
        elif "{user_name}" in prompt:
            prompt = prompt.format(user_name=user.name if user else "there")
        
        return f"\n\n## CURRENT TASK\n{prompt}"
    
    def build_messages(
        self,
        system_prompt: str,
        chat_history: List[Message],
        current_message: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Build messages list for LLM with sliding window.
        
        Args:
            system_prompt: System prompt to use
            chat_history: List of previous messages
            current_message: Optional current user message
            
        Returns:
            List of message dicts for LLM
        """
        llm = get_llm_provider()
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Calculate tokens used by system prompt
        system_tokens = llm.count_tokens(system_prompt)
        
        # Calculate remaining budget for chat
        remaining_tokens = self.max_tokens - system_tokens - 500  # Reserve for response
        
        if current_message:
            current_tokens = llm.count_tokens(current_message)
            remaining_tokens -= current_tokens
        
        # Add chat history with sliding window (newest first for selection)
        history_messages = []
        history_tokens = 0
        
        for msg in reversed(chat_history):
            msg_tokens = llm.count_tokens(msg.content) + 4  # Overhead
            
            if history_tokens + msg_tokens > remaining_tokens:
                logger.debug(f"Sliding window: truncated history at {len(history_messages)} messages")
                break
            
            history_messages.append(msg.to_llm_format())
            history_tokens += msg_tokens
        
        # Reverse to get chronological order
        history_messages.reverse()
        messages.extend(history_messages)
        
        # Add current message
        if current_message:
            messages.append({"role": "user", "content": current_message})
        
        logger.debug(
            f"Built context: {len(messages)} messages, "
            f"~{system_tokens + history_tokens} tokens"
        )
        
        return messages
    
    def estimate_tokens(
        self,
        system_prompt: str,
        chat_history: List[Message],
    ) -> int:
        """Estimate total tokens for context."""
        llm = get_llm_provider()
        
        total = llm.count_tokens(system_prompt)
        
        for msg in chat_history:
            total += llm.count_tokens(msg.content) + 4
        
        return total
