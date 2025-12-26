"""
Onboarding Service - Handles the conversational onboarding flow
"""
import logging
import re
from datetime import datetime
from typing import Tuple, Optional, List

from app.models.user import User
from app.api.routes.websocket import send_typing_indicator

logger = logging.getLogger(__name__)


class OnboardingService:
    """
    Handles extracting information during the onboarding flow.
    """
    
    @staticmethod
    def extract_name(text: str) -> Optional[str]:
        """Extract name from user input with Hinglish awareness."""
        text = text.strip()
        # Avoid common greetings being mis-read as names
        stopwords = {"hi", "hello", "hey", "yo", "hola", "hii"}
        if text.lower() in stopwords:
            return None
        
        # Hinglish/Hindi patterns
        hindi_patterns = [
            r"(?:mera naam|my name is|i am|i'm|call me|it's|its|iam)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"(?:naam hai)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        ]
        
        for pattern in hindi_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip().title()

        # Common patterns
        patterns = [
            r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)$",
            r"^([A-Za-z]+)$",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip().title()
                if 2 <= len(name) <= 50:
                    return name
        
        # Fallback for short alphabetical input (only if it's 1-2 words)
        words = text.split()
        if len(words) <= 2 and all(w.isalpha() for w in words):
            return text.title()
            
        return None

    @staticmethod
    def extract_gender(text: str) -> Optional[str]:
        """Extract gender from user input."""
        text_lower = text.lower()
        if any(w in text_lower for w in ["male", "man", "boy", "guy"]):
            return "male"
        if any(w in text_lower for w in ["female", "woman", "girl", "lady"]):
            return "female"
        if "other" in text_lower or "prefer not to say" in text_lower:
            return "other"
        return None

    @staticmethod
    def extract_weight_height(text: str) -> Tuple[Optional[float], Optional[float]]:
        """Extract weight (kg) and height (cm) from user input with validation."""
        weight, height = None, None
        
        # Look for weight (kg)
        weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:kg|kilo|kilogram)', text, re.IGNORECASE)
        if weight_match:
            val = float(weight_match.group(1))
            if 20 <= val <= 300: # Valid range for humans
                weight = val
            
        # Look for height (cm)
        height_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:cm|centimeter)', text, re.IGNORECASE)
        if height_match:
            val = float(height_match.group(1))
            if 50 <= val <= 250: # Valid range for humans
                height = val
        
        # Fallback: if two numbers are found, assume first is weight if > 30 and second is height if > 100
        if weight is None or height is None:
            nums = re.findall(r'(\d+(?:\.\d+)?)', text)
            if len(nums) >= 2:
                n1, n2 = float(nums[0]), float(nums[1])
                # Check for weight/height pair
                if 30 <= n1 <= 200 and 100 <= n2 <= 250:
                    weight, height = n1, n2
                    
        return weight, height

    @staticmethod
    def extract_age(text: str) -> Optional[int]:
        """Extract age from user input with validation and Hinglish awareness."""
        # Common Hinglish/English patterns for age
        patterns = [
            r"(\d{1,3})\s*(?:year|yr|saal|age)",
            r"(?:i am|i'm|age is|age hai)\s*(\d{1,3})",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                age = int(match.group(1))
                if 5 <= age <= 100:
                    return age

        # Find any numbers as fallback
        numbers = re.findall(r'\b(\d{1,3})\b', text)
        for num in numbers:
            age = int(num)
            if 5 <= age <= 100: # Practical range for a health coach
                return age
                
        return None

    @staticmethod
    def extract_goals(text: str) -> List[str]:
        """Extract goals from user input."""
        goals = []
        text_lower = text.lower()
        
        # Explicit "other" detection
        if "other" in text_lower.strip():
            return ["other_custom"]

        goal_map = {
            "weight loss": ["lose weight", "weight loss", "slim", "fat loss", "weight reduction"],
            "muscle gain": ["gain weight", "muscle", "bulk", "bodybuilding", "strength"],
            "diabetes management": ["diabetes", "sugar", "blood sugar", "hba1c"],
            "pcos management": ["pcos", "pcod", "periods", "hormonal"],
            "fitness": ["fitness", "gym", "workout", "active", "stamina"],
            "healthy diet": ["diet", "nutrition", "healthy food", "eating habits"],
            "stress management": ["stress", "anxiety", "mental health", "meditation"],
            "sleep improvement": ["sleep", "insomnia", "sleeping"],
        }
        
        for goal, keywords in goal_map.items():
            if any(kw in text_lower for kw in keywords):
                goals.append(goal)
                
        if not goals:
            goals.append("general wellness")
            
        return goals[:3]
