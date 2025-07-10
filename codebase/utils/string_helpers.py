import re
import unicodedata
from typing import List, Optional, Union
import hashlib
import base64


class StringProcessor:
    """String processing utilities with potential refactoring opportunities"""
    
    def __init__(self, default_encoding: str = 'utf-8'):
        self.default_encoding = default_encoding
        self.cache = {}
    
    def clean_text(self, text: str) -> str:
        """Clean text by removing extra whitespace and normalizing"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Normalize unicode
        text = unicodedata.normalize('NFKD', text)
        
        # Remove control characters
        text = ''.join(char for char in text if not unicodedata.category(char).startswith('C'))
        
        return text
    
    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text"""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(pattern, text)
    
    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text"""
        pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(pattern, text)
    
    def slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug"""
        text = text.lower()
        text = re.sub(r'[^a-z0-9]+', '-', text)
        text = text.strip('-')
        return text
    
    def truncate_text(self, text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text to maximum length"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    def count_words(self, text: str) -> int:
        """Count words in text"""
        return len(text.split()) if text else 0
    
    def remove_html_tags(self, text: str) -> str:
        """Remove HTML tags from text"""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)
    
    def capitalize_words(self, text: str) -> str:
        """Capitalize first letter of each word"""
        return ' '.join(word.capitalize() for word in text.split())
    
    def reverse_words(self, text: str) -> str:
        """Reverse the order of words in text"""
        return ' '.join(reversed(text.split()))
    
    def hash_string(self, text: str, algorithm: str = 'sha256') -> str:
        """Generate hash of string"""
        if algorithm == 'md5':
            return hashlib.md5(text.encode(self.default_encoding)).hexdigest()
        elif algorithm == 'sha1':
            return hashlib.sha1(text.encode(self.default_encoding)).hexdigest()
        elif algorithm == 'sha256':
            return hashlib.sha256(text.encode(self.default_encoding)).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    def encode_base64(self, text: str) -> str:
        """Encode string to base64"""
        return base64.b64encode(text.encode(self.default_encoding)).decode('ascii')
    
    def decode_base64(self, encoded: str) -> str:
        """Decode base64 string"""
        return base64.b64decode(encoded).decode(self.default_encoding)


# Standalone utility functions (potential candidates for class consolidation)
def is_email_valid(email: str) -> bool:
    """Validate email address format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def format_phone_number(phone: str) -> str:
    """Format phone number to standard format"""
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    return phone


def extract_numbers(text: str) -> List[float]:
    """Extract numbers from text"""
    pattern = r'-?\d+\.?\d*'
    return [float(match) for match in re.findall(pattern, text)]


def remove_duplicates_preserve_order(text_list: List[str]) -> List[str]:
    """Remove duplicates while preserving order"""
    seen = set()
    result = []
    for item in text_list:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


class TextAnalyzer:
    """Advanced text analysis utilities"""
    
    def __init__(self):
        self.stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    
    def word_frequency(self, text: str) -> dict:
        """Calculate word frequency in text"""
        words = text.lower().split()
        words = [word.strip('.,!?;:"()[]{}') for word in words]
        words = [word for word in words if word and word not in self.stop_words]
        
        frequency = {}
        for word in words:
            frequency[word] = frequency.get(word, 0) + 1
        
        return frequency
    
    def reading_time(self, text: str, wpm: int = 200) -> float:
        """Estimate reading time in minutes"""
        word_count = len(text.split())
        return word_count / wpm
    
    def sentiment_score(self, text: str) -> float:
        """Simple sentiment analysis (positive/negative word counting)"""
        positive_words = {'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'awesome'}
        negative_words = {'bad', 'terrible', 'awful', 'horrible', 'hate', 'disgusting', 'worst', 'annoying'}
        
        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            return 0.0
        
        return (positive_count - negative_count) / total_sentiment_words 