"""API ingestion module with retry logic and rate limiting.

This module provides robust API data fetching with:
- Exponential backoff retry logic
- Rate limiting and circuit breaker pattern
- Support for multiple API sources
- Error handling and logging
"""
import time
import logging
from typing import List, Dict, Optional, Callable, Any
from functools import wraps
from datetime import datetime, timedelta
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple token bucket rate limiter."""
    
    def __init__(self, max_calls: int, time_window: int):
        """
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def wait_if_needed(self):
        """Wait if rate limit is exceeded."""
        now = datetime.now()
        # Remove old calls outside time window
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < timedelta(seconds=self.time_window)]
        
        if len(self.calls) >= self.max_calls:
            sleep_time = (self.calls[0] + timedelta(seconds=self.time_window) - now).total_seconds()
            if sleep_time > 0:
                logger.info(f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                self.calls = []
        
        self.calls.append(now)


class CircuitBreaker:
    """Circuit breaker pattern to prevent cascading failures."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        """
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting reset
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == 'open':
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = 'half-open'
                logger.info("Circuit breaker: attempting reset (half-open)")
            else:
                raise Exception(f"Circuit breaker is OPEN. Try again after {self.timeout}s")
        
        try:
            result = func(*args, **kwargs)
            if self.state == 'half-open':
                self.state = 'closed'
                self.failure_count = 0
                logger.info("Circuit breaker: reset to CLOSED")
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'open'
                logger.error(f"Circuit breaker: OPENED after {self.failure_count} failures")
            
            raise e


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """Decorator for exponential backoff retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retries = 0
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}")
                        raise e
                    
                    # Exponential backoff with jitter
                    delay = min(base_delay * (2 ** (retries - 1)), max_delay)
                    jitter = delay * 0.1  # 10% jitter
                    sleep_time = delay + (jitter * (0.5 - abs(hash(str(time.time())) % 100) / 100))
                    
                    logger.warning(f"Retry {retries}/{max_retries} for {func.__name__} after {sleep_time:.2f}s. Error: {e}")
                    time.sleep(sleep_time)
            
            return None
        return wrapper
    return decorator


class APIIngestor:
    """Unified API ingestion with rate limiting and retry logic."""
    
    def __init__(self, rate_limit_calls: int = 10, rate_limit_window: int = 60):
        """
        Args:
            rate_limit_calls: Max API calls per window
            rate_limit_window: Time window in seconds
        """
        self.rate_limiter = RateLimiter(rate_limit_calls, rate_limit_window)
        self.circuit_breaker = CircuitBreaker()
        
    @retry_with_backoff(max_retries=3, base_delay=2.0)
    def fetch_json_api(self, url: str, headers: Optional[Dict] = None, 
                      params: Optional[Dict] = None) -> Dict:
        """Fetch data from a JSON REST API.
        
        Args:
            url: API endpoint URL
            headers: Optional HTTP headers
            params: Optional query parameters
        
        Returns:
            Parsed JSON response as dict
        """
        try:
            import requests
        except ImportError:
            logger.error("requests library not installed. Run: pip install requests")
            return {}
        
        self.rate_limiter.wait_if_needed()
        
        def _make_request():
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        
        return self.circuit_breaker.call(_make_request)
    
    @retry_with_backoff(max_retries=3, base_delay=2.0)
    def fetch_paginated_api(self, base_url: str, headers: Optional[Dict] = None,
                           page_param: str = 'page', max_pages: int = 100) -> List[Dict]:
        """Fetch data from paginated API.
        
        Args:
            base_url: Base API URL
            headers: Optional HTTP headers
            page_param: Name of pagination parameter
            max_pages: Maximum pages to fetch
        
        Returns:
            List of all records from all pages
        """
        all_data = []
        page = 1
        
        while page <= max_pages:
            try:
                params = {page_param: page}
                data = self.fetch_json_api(base_url, headers=headers, params=params)
                
                if not data or (isinstance(data, list) and len(data) == 0):
                    break
                
                # Handle different response structures
                if isinstance(data, dict):
                    records = data.get('data', data.get('results', data.get('items', [])))
                else:
                    records = data
                
                if not records:
                    break
                
                all_data.extend(records if isinstance(records, list) else [records])
                logger.info(f"Fetched page {page}, total records: {len(all_data)}")
                page += 1
                
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                break
        
        return all_data
    
    def fetch_shopify_orders(self, shop_url: str, access_token: str, 
                            limit: int = 250) -> List[Dict]:
        """Fetch orders from Shopify API.
        
        Args:
            shop_url: Shopify store URL (e.g., 'mystore.myshopify.com')
            access_token: Shopify API access token
            limit: Orders per page (max 250)
        
        Returns:
            List of order records
        """
        url = f"https://{shop_url}/admin/api/2024-01/orders.json"
        headers = {'X-Shopify-Access-Token': access_token}
        params = {'limit': limit, 'status': 'any'}
        
        try:
            response = self.fetch_json_api(url, headers=headers, params=params)
            return response.get('orders', [])
        except Exception as e:
            logger.error(f"Shopify API error: {e}")
            return []
    
    def fetch_woocommerce_orders(self, base_url: str, consumer_key: str, 
                                consumer_secret: str) -> List[Dict]:
        """Fetch orders from WooCommerce API.
        
        Args:
            base_url: WooCommerce site URL
            consumer_key: WooCommerce consumer key
            consumer_secret: WooCommerce consumer secret
        
        Returns:
            List of order records
        """
        url = f"{base_url}/wp-json/wc/v3/orders"
        
        try:
            import requests
            auth = (consumer_key, consumer_secret)
            
            self.rate_limiter.wait_if_needed()
            response = requests.get(url, auth=auth, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"WooCommerce API error: {e}")
            return []
    
    def fetch_stripe_charges(self, api_key: str, limit: int = 100) -> List[Dict]:
        """Fetch charges from Stripe API.
        
        Args:
            api_key: Stripe secret API key
            limit: Number of charges per request (max 100)
        
        Returns:
            List of charge records
        """
        url = "https://api.stripe.com/v1/charges"
        headers = {'Authorization': f'Bearer {api_key}'}
        params = {'limit': limit}
        
        try:
            response = self.fetch_json_api(url, headers=headers, params=params)
            return response.get('data', [])
        except Exception as e:
            logger.error(f"Stripe API error: {e}")
            return []


def fetch_from_api(api_type: str, config: Dict) -> List[Dict]:
    """Convenience function to fetch from various API sources.
    
    Args:
        api_type: Type of API ('shopify', 'woocommerce', 'stripe', 'generic')
        config: Configuration dict with API credentials and parameters
    
    Returns:
        List of records fetched from API
    """
    ingestor = APIIngestor(
        rate_limit_calls=config.get('rate_limit_calls', 10),
        rate_limit_window=config.get('rate_limit_window', 60)
    )
    
    if api_type == 'shopify':
        return ingestor.fetch_shopify_orders(
            config['shop_url'],
            config['access_token'],
            config.get('limit', 250)
        )
    elif api_type == 'woocommerce':
        return ingestor.fetch_woocommerce_orders(
            config['base_url'],
            config['consumer_key'],
            config['consumer_secret']
        )
    elif api_type == 'stripe':
        return ingestor.fetch_stripe_charges(
            config['api_key'],
            config.get('limit', 100)
        )
    elif api_type == 'generic':
        return ingestor.fetch_json_api(
            config['url'],
            config.get('headers'),
            config.get('params')
        )
    elif api_type == 'paginated':
        return ingestor.fetch_paginated_api(
            config['url'],
            config.get('headers'),
            config.get('page_param', 'page'),
            config.get('max_pages', 100)
        )
    else:
        raise ValueError(f"Unsupported API type: {api_type}")


if __name__ == '__main__':
    # Example usage
    print("API Ingestion module with retry logic and rate limiting")
    print("Use fetch_from_api() to ingest from various sources")
