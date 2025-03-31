import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import random
import cloudinary
import cloudinary.uploader
from cloudinary.uploader import upload
from cloudinary.utils import cloudinary_url
import re
from difflib import SequenceMatcher

class QuoteScraper:
    def __init__(self):
        self.sources = [
            'https://www.brainyquote.com/topics/',
            'https://www.goodreads.com/quotes/tag/',
            'https://www.quoteslyfe.com/search?q=',
            'https://www.azquotes.com/search_results.html?q=',
            'https://wisdomquotes.com/tag/'
        ]
        
        # Google search parameters for quotes
        self.google_search_enabled = True
        
        # Cache to store previously fetched quotes and reduce duplicate returns
        self.quote_cache = {}
        
        # Basic list of terms to filter - can be expanded
        self.filtered_terms = {
            'slurs': ['n-word', 'f-word'],
            'explicit': ['xxx', 'porn'],
            'offensive': ['hate', 'kill']
        }
        
        # Maximum quotes to return by default
        self.default_max_quotes = 10
        self.max_possible_quotes = 30
    
    def _should_filter_term(self, term: str) -> bool:
        """
        Check if a term should be filtered using fuzzy matching
        Returns True if term should be filtered out
        """
        term = term.lower()
        
        # Direct match check
        for category in self.filtered_terms.values():
            for filtered_term in category:
                # Exact match
                if filtered_term == term:
                    return True
                
                # Fuzzy match if terms are very similar
                similarity = SequenceMatcher(None, filtered_term, term).ratio()
                if similarity > 0.85:  # 85% similarity threshold
                    return True
                
                # Check for common obfuscation (like adding numbers or special chars)
                clean_term = re.sub(r'[^a-zA-Z]', '', term)
                clean_filtered = re.sub(r'[^a-zA-Z]', '', filtered_term)
                if clean_term == clean_filtered:
                    return True
        
        return False

    def search_quotes(self, topic: str, max_quotes: int = None, news_ratio: float = 0.4) -> List[Dict]:
        """
        Search for quotes on a topic
        
        Args:
            topic: The topic to search for
            max_quotes: Maximum number of quotes to return (default is self.default_max_quotes)
            news_ratio: Ratio of news sources quotes to include (0.0 to 1.0)
            
        Returns:
            List of quote dictionaries
        """
        if max_quotes is None:
            max_quotes = self.default_max_quotes
        
        # Limit max quotes to reasonable number
        max_quotes = min(max_quotes, self.max_possible_quotes)
        
        # Check if topic should be filtered
        if self._should_filter_term(topic):
            # Return appropriate fallback quotes only if we're not in 100% news mode
            if news_ratio < 1.0:
                return self._get_safe_fallback_quotes()[:max_quotes]
            else:
                # For 100% news mode, return news-focused fallbacks
                return self._get_safe_news_fallbacks(topic)[:max_quotes]
        
        # Initialize quotes lists
        quotes_regular = []
        quotes_news = []
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Only fetch regular quotes if news_ratio is less than 1.0 (not 100% news)
        if news_ratio < 1.0:
            try:
                cache_key = f"{topic.lower()}_regular"
                if cache_key in self.quote_cache and random.random() > 0.3:
                    quotes_regular = self.quote_cache[cache_key].copy()
                    random.shuffle(quotes_regular)
                else:
                    for source in self.sources:
                        try:
                            source_quotes = self._scrape_from_source(source, topic, headers)
                            quotes_regular.extend(source_quotes)
                        except Exception as e:
                            print(f"Error processing {source}: {str(e)}")
                            continue
                    
                    if quotes_regular:
                        self.quote_cache[cache_key] = quotes_regular.copy()
            except Exception as e:
                print(f"Error fetching regular quotes: {str(e)}")
        
        # Always fetch news quotes if news_ratio > 0.0 (not 0% news)
        if news_ratio > 0.0:
            try:
                cache_key = f"{topic.lower()}_news"
                if cache_key in self.quote_cache and random.random() > 0.5:
                    quotes_news = self.quote_cache[cache_key].copy()
                    random.shuffle(quotes_news)
                else:
                    google_quotes = self._get_quotes_from_google(topic, headers)
                    news_quotes = self._get_quotes_from_news(topic, headers)
                    quotes_news = google_quotes + news_quotes
                    
                    if quotes_news:
                        self.quote_cache[cache_key] = quotes_news.copy()
            except Exception as e:
                print(f"Error fetching news quotes: {str(e)}")
        
        # Clean and deduplicate quotes
        cleaned_regular = self._clean_and_deduplicate_quotes(quotes_regular)
        cleaned_news = self._clean_and_deduplicate_quotes(quotes_news)
        
        # For 100% news mode, if no news quotes found, try harder or use news-like fallbacks
        if news_ratio == 1.0 and not cleaned_news:
            # Try alternative news sources or generate news-like quotes
            cleaned_news = self._get_safe_news_fallbacks(topic)
        
        # If no quotes found at all and not in 100% news mode, return fallback quotes
        if not cleaned_regular and not cleaned_news:
            from app.routes import get_fallback_quotes
            fallback_quotes = get_fallback_quotes(topic)
            
            # Split fallbacks between regular quotes and news quotes based on ratio
            if news_ratio == 1.0:
                # Only use news fallbacks for 100% news mode
                return [q for q in fallback_quotes if q.get('source') == 'Recent News'][:max_quotes]
            elif news_ratio == 0.0:
                # Only use regular fallbacks for 0% news mode
                return [q for q in fallback_quotes if q.get('source') != 'Recent News'][:max_quotes]
            else:
                # Use mixed fallbacks based on the ratio
                return fallback_quotes[:max_quotes]
        
        # For 100% news mode, only return news quotes
        if news_ratio == 1.0:
            return cleaned_news[:max_quotes]
        
        # For 0% news mode, only return regular quotes
        if news_ratio == 0.0:
            return cleaned_regular[:max_quotes]
        
        # Calculate how many of each type based on news_ratio
        news_count = int(max_quotes * news_ratio)
        regular_count = max_quotes - news_count
        
        # Make sure we have at least 1 of each type if ratio is between 0.0 and 1.0
        if 0.0 < news_ratio < 1.0:
            if news_count == 0:
                news_count = 1
                regular_count = max_quotes - news_count
            if regular_count == 0:
                regular_count = 1
                news_count = max_quotes - regular_count
        
        # Adjust if we don't have enough of either type
        if len(cleaned_news) < news_count:
            # If no news quotes at all, supplement with news-like fallbacks
            if len(cleaned_news) == 0 and news_ratio > 0.0:
                cleaned_news = self._get_safe_news_fallbacks(topic)
            
            # If still not enough, adjust counts
            if len(cleaned_news) < news_count:
                regular_count += (news_count - len(cleaned_news))
                news_count = len(cleaned_news)
        
        if len(cleaned_regular) < regular_count:
            # If no regular quotes at all, use regular fallbacks
            if len(cleaned_regular) == 0 and news_ratio < 1.0:
                from app.routes import get_fallback_quotes
                fallbacks = [q for q in get_fallback_quotes(topic) if q.get('source') != 'Recent News']
                cleaned_regular = fallbacks
            
            # If still not enough, adjust counts
            if len(cleaned_regular) < regular_count:
                news_count += (regular_count - len(cleaned_regular))
                regular_count = len(cleaned_regular)
        
        # Build final result
        result_quotes = []
        
        # Add regular quotes
        if regular_count > 0 and cleaned_regular:
            if len(cleaned_regular) > regular_count:
                result_quotes.extend(random.sample(cleaned_regular, regular_count))
            else:
                result_quotes.extend(cleaned_regular)
        
        # Add news quotes
        if news_count > 0 and cleaned_news:
            if len(cleaned_news) > news_count:
                result_quotes.extend(random.sample(cleaned_news, news_count))
            else:
                result_quotes.extend(cleaned_news)
        
        # Randomize final order
        random.shuffle(result_quotes)
        return result_quotes[:max_quotes]
    
    def get_random_quote(self, topic: str) -> Dict:
        quotes = self.search_quotes(topic)
        return random.choice(quotes) if quotes else None 

    def _get_safe_fallback_quotes(self) -> List[Dict]:
        """Return family-friendly fallback quotes"""
        return [
            {
                "text": "Be the change you wish to see in the world.",
                "author": "Mahatma Gandhi",
                "source": "Fallback"
            },
            {
                "text": "The only way to do great work is to love what you do.",
                "author": "Steve Jobs",
                "source": "Fallback"
            },
            # Add more fallback quotes...
        ] 

    def _get_safe_news_fallbacks(self, topic):
        """Generate news-like quotes when no real news quotes can be found"""
        news_fallbacks = [
            {
                "text": f"Recent studies suggest that {topic} may play a significant role in overall well-being.",
                "author": "Health Journal",
                "source": "Recent News"
            },
            {
                "text": f"Experts are debating the future implications of {topic} on public policy.",
                "author": "Policy Digest",
                "source": "Recent News" 
            },
            {
                "text": f"New research shows unexpected connections between {topic} and mental health outcomes.",
                "author": "Psychology Today",
                "source": "Recent News"
            },
            {
                "text": f"A comprehensive analysis reveals changing trends in how {topic} is perceived across different demographics.",
                "author": "Sociological Review",
                "source": "Web Search"
            },
            {
                "text": f"Industry leaders are increasingly focused on integrating {topic} into sustainable business practices.",
                "author": "Business Weekly",
                "source": "Web Search"
            },
            {
                "text": f"The latest data on {topic} challenges previously held assumptions in the field.",
                "author": "Science Daily",
                "source": "Recent News"
            },
            {
                "text": f"Community organizers emphasize the importance of addressing {topic} at the local level.",
                "author": "Community Times",
                "source": "Web Search"
            },
            {
                "text": f"International cooperation will be essential to effectively manage {topic} in the coming decades.",
                "author": "Global Affairs",
                "source": "Recent News"
            },
            {
                "text": f"Emerging technologies offer promising solutions to challenges related to {topic}.",
                "author": "Tech Review",
                "source": "Web Search"
            },
            {
                "text": f"Educational approaches to {topic} are evolving based on new understanding of cognitive development.",
                "author": "Education Weekly",
                "source": "Recent News"
            }
        ]
        return news_fallbacks

    def _clean_and_deduplicate_quotes(self, quotes):
        """Clean and deduplicate quotes with improved author handling"""
        cleaned_quotes = []
        seen_quotes = set()
        
        for quote in quotes:
            # Clean up quote text
            text = quote['text'].strip()
            
            # Skip very short quotes
            if len(text) < 10:
                continue
            
            # Extract author from quote text if missing
            author = quote.get('author', '').strip()
            if not author or author.lower() == 'unknown':
                # Try to extract author from the quote if it contains attribution
                text_lower = text.lower()
                for pattern in [' - ', '– ', '— ', ' by ', ' according to ']:
                    if pattern in text_lower:
                        parts = text.split(pattern, 1)
                        if len(parts) == 2 and len(parts[1]) > 0 and len(parts[1]) < 50:
                            # Use the part after the separator as author
                            author = parts[1].strip('" .')
                            # Remove the author from the quote text
                            text = parts[0].strip()
                            break
            
            # Remove existing quotation marks to prevent doubles
            text = text.strip('"').strip('"').strip('"')
            
            # Then add back a single set of quotation marks
            text = f'"{text}"'
            
            # Create a key for deduplication
            key = (text.lower()[:50], author.lower())
            
            if key not in seen_quotes:
                seen_quotes.add(key)
                
                # Use a default author for truly unknown sources
                if not author or author.lower() == 'unknown':
                    author = "Unknown Source"
                
                cleaned_quotes.append({
                    'text': text,
                    'author': author,
                    'source': quote.get('source', 'General')
                })
        
        return cleaned_quotes

    def _scrape_from_source(self, source, topic, headers):
        """Scrape quotes from a specific source with improved author extraction"""
        quotes = []
        url = f"{source}{topic.replace(' ', '+').lower()}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"Error scraping {source}: {response.status_code} status code for url: {url}")
            return quotes
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if 'brainyquote.com' in source:
            quote_elements = soup.find_all('div', class_='grid-item')
            for element in quote_elements:
                quote_text_elem = element.find('a', class_='b-qt')
                author_elem = element.find('a', class_='bq-aut')
                
                if quote_text_elem and author_elem:
                    quote_text = quote_text_elem.text.strip()
                    author = author_elem.text.strip()
                    
                    quotes.append({
                        'text': quote_text,
                        'author': author,
                        'source': 'BrainyQuote'
                    })
        
        elif 'goodreads.com' in source:
            quote_elements = soup.find_all('div', class_='quoteDetails')
            for element in quote_elements:
                quote_text_elem = element.find('div', class_='quoteText')
                
                if quote_text_elem:
                    # Extract the full text including the author
                    full_text = quote_text_elem.get_text(strip=True)
                    
                    # Separate quote from author
                    parts = full_text.split('―', 1)
                    if len(parts) == 2:
                        quote_text = parts[0].strip()
                        # Extract just the author name, not additional info
                        author_full = parts[1].strip()
                        author = author_full.split(',')[0].strip()
                        
                        quotes.append({
                            'text': quote_text,
                            'author': author,
                            'source': 'Goodreads'
                        })
                    else:
                        # If we can't split by em dash, try to find other patterns
                        for pattern in [' - ', '– ', ' by ', ' according to ']:
                            if pattern in full_text:
                                parts = full_text.split(pattern, 1)
                                if len(parts) == 2:
                                    quote_text = parts[0].strip()
                                    author = parts[1].strip()
                                    
                                    quotes.append({
                                        'text': quote_text,
                                        'author': author,
                                        'source': 'Goodreads'
                                    })
                                    break
        
        elif 'quoteslyfe.com' in source:
            quote_elements = soup.find_all('div', class_='card')
            for element in quote_elements:
                quote_text_elem = element.find('p', class_='card-text')
                author_elem = element.find('footer', class_='blockquote-footer')
                
                if quote_text_elem and author_elem:
                    quotes.append({
                        'text': quote_text_elem.get_text(strip=True),
                        'author': author_elem.get_text(strip=True),
                        'source': 'QuotesLyfe'
                    })
        
        elif 'azquotes.com' in source:
            quote_elements = soup.find_all('div', class_='wrap-block')
            for element in quote_elements:
                quote_elem = element.find('a', class_='title')
                author_elem = element.find('div', class_='author')
                
                if quote_elem and author_elem:
                    quotes.append({
                        'text': quote_elem.get_text(strip=True),
                        'author': author_elem.get_text(strip=True),
                        'source': 'AZQuotes'
                    })
        
        elif 'wisdomquotes.com' in source:
            # Wisdom Quotes uses a different URL pattern for tags
            quote_elements = soup.find_all('blockquote')
            for element in quote_elements:
                quote_text = element.get_text(strip=True)
                
                # Find author in the citation element
                author_elem = element.find_next('cite')
                
                if author_elem:
                    author = author_elem.get_text(strip=True)
                    
                    quotes.append({
                        'text': quote_text,
                        'author': author,
                        'source': 'WisdomQuotes'
                    })
                else:
                    # If no citation element, check if author is in the quote
                    for pattern in [' - ', '– ', '— ', ' by ', ' according to ']:
                        if pattern in quote_text:
                            parts = quote_text.split(pattern, 1)
                            if len(parts) == 2:
                                cleaned_quote = parts[0].strip()
                                author = parts[1].strip()
                                
                                quotes.append({
                                    'text': cleaned_quote,
                                    'author': author,
                                    'source': 'WisdomQuotes'
                                })
                                break
        
        return quotes

    def _get_quotes_from_google(self, topic, headers):
        """Get quotes from Google search results"""
        quotes = []
        
        # Create a Google search query specifically for quotes
        search_query = f"inspirational quotes about {topic}"
        url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for elements that might contain quotes
            # This is more experimental since Google's HTML structure can change
            search_results = soup.find_all('div', class_='BNeawe s3v9rd AP7Wnd')
            
            for result in search_results:
                text = result.get_text(strip=True)
                
                # Check if the text looks like a quote (contains quotes or has author pattern)
                if ('"' in text or '"' in text) and '-' in text:
                    # Try to split the author from the quote
                    parts = text.split('-', 1)
                    if len(parts) == 2:
                        quote_text = parts[0].strip()
                        author = parts[1].strip()
                        
                        # Clean up quote text
                        if quote_text.startswith('"') and quote_text.endswith('"'):
                            quote_text = quote_text[1:-1]
                        
                        quotes.append({
                            'text': quote_text,
                            'author': author,
                            'source': 'Web Search'
                        })
                        
            # Also try to extract recent news quotes if we don't have enough
            if len(quotes) < 3:
                news_query = f"recent quote {topic} said"
                news_url = f"https://www.google.com/search?q={news_query.replace(' ', '+')}&tbm=nws"
                news_response = requests.get(news_url, headers=headers, timeout=10)
                news_soup = BeautifulSoup(news_response.text, 'html.parser')
                
                # Try to find news articles with quotes
                news_results = news_soup.find_all('div', class_='BNeawe vvjwJb AP7Wnd')
                
                for result in news_results:
                    text = result.get_text(strip=True)
                    
                    # Look for quoted text in news snippets
                    quote_match = re.search(r'"([^"]+)"', text)
                    if quote_match:
                        quote_text = quote_match.group(1)
                        # Try to find who said it
                        author_match = re.search(r'said ([^,\.]+)', text)
                        author = author_match.group(1) if author_match else "Recent Source"
                        
                        quotes.append({
                            'text': quote_text,
                            'author': author,
                            'source': 'Recent News'
                        })
        
        except Exception as e:
            print(f"Error with Google search: {str(e)}")
        
        return quotes

    def _get_quotes_from_news(self, topic, headers):
        """Get quotes specifically from news sources"""
        quotes = []
        
        # Create a news search query
        news_query = f"{topic} quote said recently"
        news_url = f"https://www.google.com/search?q={news_query.replace(' ', '+')}&tbm=nws"
        
        try:
            response = requests.get(news_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract news snippets
            news_results = soup.find_all(['div', 'span'], class_=['BNeawe', 'Y2IQFc'])
            
            for result in news_results:
                text = result.get_text(strip=True)
                
                # Look for quoted text in news snippets
                quote_matches = re.findall(r'"([^"]{15,200})"', text)  # At least 15 chars, max 200
                
                for quote_text in quote_matches:
                    # Try to find who said it
                    author = "Recent Source"
                    
                    # Look for attribution patterns after the quote
                    after_quote = text.split(f'"{quote_text}"', 1)
                    if len(after_quote) > 1:
                        # Look for patterns like "... said John Smith" or "... according to Jane Doe"
                        attribution = after_quote[1]
                        said_match = re.search(r'said ([^,\.]{3,30})', attribution)
                        according_match = re.search(r'according to ([^,\.]{3,30})', attribution)
                        
                        if said_match:
                            author = said_match.group(1).strip()
                        elif according_match:
                            author = according_match.group(1).strip()
                    
                    # Add the quote if it's not too short and has basic punctuation
                    if len(quote_text) > 20 and any(p in quote_text for p in ['.', ',', '!', '?']):
                        quotes.append({
                            'text': f'"{quote_text}"',
                            'author': author,
                            'source': 'Recent News'
                        })
        
        except Exception as e:
            print(f"Error with news search: {str(e)}")
        
        return quotes 