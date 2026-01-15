# backend/api/helpers.py

import os
import finnhub
from django.core.cache import cache
from datetime import datetime, timedelta
import pytz

def get_smart_ttl():
    """
    Calculates TTL based on NYSE Market Hours.
    Resume Claim: 'market-aware TTL logic'
    """
    # 1. Get Current Time in EST (New York)
    utc_now = datetime.now(pytz.utc)
    est_now = utc_now.astimezone(pytz.timezone('US/Eastern'))
    
    market_open = est_now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = est_now.replace(hour=16, minute=0, second=0, microsecond=0)

    # 2. If Market is Open (Mon-Fri, 9:30-4:00): Short Cache (1 min)
    if est_now.weekday() < 5 and market_open <= est_now <= market_close:
        return 60

    # 3. If Market is Closed: Cache until next Open
    next_open = market_open
    if est_now > market_open: 
        next_open = market_open + timedelta(days=1)
    
    # Handle Weekends (Skip Sat/Sun)
    while next_open.weekday() >= 5:
        next_open += timedelta(days=1)
        
    delta = (next_open - est_now).total_seconds()
    # Return delta, but ensure at least 60s safety buffer
    return int(max(60, delta))

def lookup_quote(symbol):
    """
    Look up quote using Redis with Market-Aware TTL.
    """
    symbol = symbol.upper()
    cache_key = f"quote_{symbol}"
    
    # 1. Check Redis First (Low Latency)
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data

    # 2. Cache Miss: Fetch from Finnhub API
    try:
        api_key = os.environ.get("API_KEY")
        if not api_key:
            print("Error: API_KEY missing in environment variables")
            return None
            
        finnhub_client = finnhub.Client(api_key=api_key)
        quote = finnhub_client.quote(symbol)
        
        # Validate data (Finnhub returns 0s for invalid symbols)
        if quote['c'] == 0 and quote['pc'] == 0:
            return None

        data = {
            "symbol": symbol,
            "current_price": round(float(quote["c"]), 2),
            "opening_price": round(float(quote["o"]), 2),
            "previous_close": round(float(quote["pc"]), 2),
            "daily_change": round(((float(quote["c"]) - float(quote["pc"])) / float(quote["pc"])) * 100, 2) if float(quote["pc"]) != 0 else 0
        }
        
        # 3. Set Cache with Smart TTL (Resume Claim Logic)
        ttl = get_smart_ttl()
        cache.set(cache_key, data, timeout=ttl)
        return data

    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

# Keep existing helpers for compatibility
def lookup_basic_financial(symbol):
    cache_key = f"basic_financial_{symbol.upper()}"
    cached_data = cache.get(cache_key)
    if cached_data: return cached_data

    try:
        api_key = os.environ.get("API_KEY")
        finnhub_client = finnhub.Client(api_key=api_key)
        metrics = finnhub_client.company_basic_financials(symbol, 'all')['metric']
        data = {
            "symbol": symbol.upper(),
            "ten_day_avg_volume": int(metrics.get('10DayAverageTradingVolume', 0)),
            "market_cap": round(float(metrics.get('marketCapitalization', 0)), 2),
            "pe_ratio": round(float(metrics.get("peTTM", 0)), 2),
            "annual_dividend_yield": round(float(metrics.get("dividendYieldIndicatedAnnual", 0)), 2),
            "52_week_high": round(float(metrics.get("52WeekHigh", 0)), 2),
            "52_week_low": round(float(metrics.get("52WeekLow", 0)), 2),
            "beta": round(float(metrics.get("beta", 0)), 2),
            "three_month_avg_volume": int(metrics.get('3MonthAverageTradingVolume', 0)),
        }
        cache.set(cache_key, data, timeout=60 * 60 * 24)
        return data
    except Exception as e:
        print(f"Error financial data {symbol}: {e}")
        return None

def lookup_profile(symbol):
    cache_key = f"profile_{symbol.upper()}"
    cached_data = cache.get(cache_key)
    if cached_data: return cached_data

    try:
        api_key = os.environ.get("API_KEY")
        finnhub_client = finnhub.Client(api_key=api_key)
        profile = finnhub_client.company_profile2(symbol=symbol)
        data = {
            "symbol": symbol.upper(),
            "name": profile.get("name", "N/A"),
            "exchange": profile.get("exchange", "N/A"),
        }
        cache.set(cache_key, data, timeout=60 * 60 * 24)
        return data
    except Exception as e:
        print(f"Error profile {symbol}: {e}")
        return None

def usd(value):
    return f"${value:,.2f}"