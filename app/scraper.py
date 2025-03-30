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

    def search_quotes(self, topic: str) -> List[Dict]:
        # Check if topic should be filtered
        if self._should_filter_term(topic):
            # Return appropriate fallback quotes instead of explicit filtering
            return self._get_safe_fallback_quotes()
        
        quotes = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Check the cache first, but don't always return cached results
        cache_key = topic.lower()
        if cache_key in self.quote_cache and random.random() > 0.3:  # 70% chance to use cache
            cached_quotes = self.quote_cache[cache_key]
            # Randomize the order of quotes to provide variety
            random.shuffle(cached_quotes)
            # Return only a subset of cached quotes for variety
            return cached_quotes[:min(10, len(cached_quotes))]
        
        # Try to scrape from standard quote websites
        for source in self.sources:
            try:
                source_quotes = self._scrape_from_source(source, topic, headers)
                quotes.extend(source_quotes)
            except Exception as e:
                print(f"Error processing {source}: {str(e)}")
                continue
        
        # If Google search is enabled and we don't have enough quotes, try Google
        if self.google_search_enabled and len(quotes) < 5:
            try:
                google_quotes = self._get_quotes_from_google(topic, headers)
                quotes.extend(google_quotes)
            except Exception as e:
                print(f"Error with Google quotes search: {str(e)}")
        
        # Clean and deduplicate quotes
        cleaned_quotes = self._clean_and_deduplicate_quotes(quotes)
        
        # If no quotes found from scraping, return fallback quotes
        if not cleaned_quotes:
            from app.routes import get_fallback_quotes
            return get_fallback_quotes(topic)
        
        # Update the cache with the new quotes
        self.quote_cache[cache_key] = cleaned_quotes
        
        # Randomize the order
        random.shuffle(cleaned_quotes)
        
        # Return a subset (up to 10) of the found quotes
        result = cleaned_quotes[:min(10, len(cleaned_quotes))]
        return result
    
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

    def _scrape_from_source(self, source, topic, headers):
        """Scrape quotes from a specific source"""
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
                    quotes.append({
                        'text': quote_text,
                        'author': author_elem.text.strip(),
                        'source': 'BrainyQuote'
                    })
        
        elif 'goodreads.com' in source:
            quote_elements = soup.find_all('div', class_='quoteDetails')
            for element in quote_elements:
                quote_text_elem = element.find('div', class_='quoteText')
                
                if quote_text_elem:
                    # Extract quote and author from quoteText
                    full_text = quote_text_elem.get_text(strip=True)
                    parts = full_text.split('―', 1)
                    
                    if len(parts) == 2:
                        quote_text = parts[0].strip()
                        author = parts[1].strip().split(',')[0]
                        
                        quotes.append({
                            'text': quote_text,
                            'author': author,
                            'source': 'Goodreads'
                        })
        
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
                author = author_elem.get_text(strip=True) if author_elem else "Unknown"
                
                quotes.append({
                    'text': quote_text,
                    'author': author,
                    'source': 'WisdomQuotes'
                })
        
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

    def _clean_and_deduplicate_quotes(self, quotes):
        """Clean and deduplicate quotes"""
        cleaned_quotes = []
        seen_quotes = set()
        
        for quote in quotes:
            # Clean up quote text
            text = quote['text'].strip()
            
            # Skip very short quotes
            if len(text) < 10:
                continue
            
            # Create a key for deduplication
            key = (text.lower()[:50], quote['author'].lower())  # Use first 50 chars for comparison
            
            if key not in seen_quotes:
                seen_quotes.add(key)
                
                # Clean up the quote format
                if text.startswith('"') and text.endswith('"'):
                    text = text[1:-1].strip()
                
                # Make sure we have quotes around the text
                if not (text.startswith('"') and text.endswith('"')):
                    text = f'"{text}"'
                
                quote['text'] = text
                cleaned_quotes.append(quote)
        
        return cleaned_quotes 