"""
Article content extractor for Federal Reserve sources.

Safely fetches and parses article content from trusted Federal Reserve
domains only. Returns normalized text for macroeconomic analysis.
"""

import urllib.request
import urllib.error
from html.parser import HTMLParser
from config.settings import ARTICLE_MAX_LENGTH, ARTICLE_FETCH_TIMEOUT

# Whitelist of trusted Federal Reserve domains
TRUSTED_DOMAINS = {
    "federalreserve.gov",
    "www.federalreserve.gov",
}

EXCLUDED_TAGS = {"script", "style", "nav", "footer", "header", "aside"}
"""HTML tags to completely ignore during parsing."""


class ArticleTextExtractor(HTMLParser):
    """
    HTML parser that extracts main text content from Federal Reserve pages.
    
    Strips scripts, styles, navigation, and other chrome.
    Collects clean text from semantic tags and maintains reasonable structure.
    """

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.skip_content = False
        self.in_article_tag = False
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        """Process opening tags."""
        if tag in EXCLUDED_TAGS:
            self.skip_content = True
        elif tag in {"article", "main", "section"}:
            self.in_article_tag = True
        
        self.current_tag = tag

    def handle_endtag(self, tag):
        """Process closing tags."""
        if tag in EXCLUDED_TAGS:
            self.skip_content = False
        elif tag in {"article", "main", "section"}:
            self.in_article_tag = False
        
        if tag in {"p", "div", "li", "blockquote", "h1", "h2", "h3"}:
            if self.text_parts and self.text_parts[-1].strip():
                self.text_parts.append("\n")
        
        self.current_tag = None

    def handle_data(self, data):
        """Process text content."""
        if not self.skip_content:
            text = data.strip()
            if text:
                self.text_parts.append(text + " ")

    def get_text(self):
        """Return extracted and normalized text."""
        if not self.text_parts:
            return ""
        
        raw_text = "".join(self.text_parts)
        # Normalize whitespace
        normalized = " ".join(raw_text.split())
        return normalized


def is_trusted_domain(url):
    """
    Verify URL belongs to Federal Reserve domain.
    
    Args:
        url: Full URL string.
    
    Returns:
        True if domain is in whitelist, False otherwise.
    """
    if not url:
        return False
    
    url_lower = url.lower()
    
    for domain in TRUSTED_DOMAINS:
        if domain in url_lower:
            return True
    
    return False


def extract_article_content(url):
    """
    Fetch and extract article content from a trusted Federal Reserve URL.
    
    SECURITY: Only processes Federal Reserve URLs.
    SAFETY: Network errors do NOT crash the agent.
    
    Args:
        url: Full URL to article (must be federalreserve.gov or www.federalreserve.gov).
    
    Returns:
        Tuple of (success: bool, text: str).
        - If successful: (True, normalized_article_text)
        - If failed: (False, "")
        
        Text is truncated to ARTICLE_MAX_LENGTH characters.
        Empty text on any error (network, parsing, trust check).
    """
    
    # Domain security check
    if not is_trusted_domain(url):
        return (False, "")
    
    try:
        # Create request with user agent
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 Rahul-AI-Team-XAUUSD-Agent/3.0"
            }
        )
        
        # Fetch with timeout
        with urllib.request.urlopen(
            request,
            timeout=ARTICLE_FETCH_TIMEOUT
        ) as response:
            html_bytes = response.read()
        
        # Decode HTML (assume UTF-8, which is standard)
        html_text = html_bytes.decode("utf-8", errors="ignore")
        
        # Parse and extract
        parser = ArticleTextExtractor()
        parser.feed(html_text)
        extracted_text = parser.get_text()
        
        # Return empty if no content extracted
        if not extracted_text.strip():
            return (False, "")
        
        # Truncate to max length
        truncated = extracted_text[:ARTICLE_MAX_LENGTH]
        
        return (True, truncated)
    
    except urllib.error.URLError as e:
        # Network error (connection refused, DNS failure, etc.)
        return (False, "")
    
    except urllib.error.HTTPError as e:
        # HTTP error (404, 403, 500, etc.)
        return (False, "")
    
    except Exception as e:
        # Any other error (parsing, encoding, etc.)
        # Do NOT crash the agent
        return (False, "")
