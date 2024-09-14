import os
import finnhub  # type: ignore
from django.core.cache import cache

    


# return stock data either from cache or external API




# real-time
def lookup_quote(symbol):
    """Look up detailed quote for symbol using Finnhub API and cache it for 1 minute."""
    cache_key = f"quote_{symbol.upper()}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        print("quote cached")
        return cached_data  # Return cached quote data if it exists

    try:
        api_key = os.environ.get("API_KEY")
        finnhub_client = finnhub.Client(api_key=api_key)
        quote = finnhub_client.quote(symbol)

        data = {
            "symbol": symbol.upper(),
            "current_price": round(float(quote["c"]), 2),
            "opening_price": round(float(quote["o"]), 2),
            "previous_close": round(float(quote["pc"]), 2),
            "high_price": round(float(quote["h"]), 2),
            "low_price": round(float(quote["l"]), 2),
        }
        cache.set(cache_key, data, timeout=60)  # Cache for 1 minute
        return data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None
    





# updated on quarterly basis
def lookup_basic_financial(symbol):
    """Look up financial metrics for a symbol using Finnhub API and cache it for 24 hours."""
    cache_key = f"basic_financial_{symbol.upper()}"
    cached_data = cache.get(cache_key)

    if cached_data:
        print("basic financials cached")
        return cached_data  # Return cached financial data if available

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

        cache.set(cache_key, data, timeout=60 * 60 * 24)  # Cache for 24 hours (60 sec * 60 min * 24 hours)
        return data
    except Exception as e:
        print(f"Error fetching financial data for {symbol}: {e}")
        return None

    





# change only occur when company info is officially updated (annual reports, corporate changes)
def lookup_profile(symbol):
    """Look up company profile for a symbol using Finnhub API and cache it for 24 hours."""
    cache_key = f"profile_{symbol.upper()}"
    cached_data = cache.get(cache_key)

    if cached_data:
        print("profile cached")
        return cached_data  # Return cached profile data if available

    try:
        api_key = os.environ.get("API_KEY")
        finnhub_client = finnhub.Client(api_key=api_key)
        profile = finnhub_client.company_profile2(symbol=symbol)

        data = {
            "symbol": symbol.upper(),
            "name": profile["name"],
            "exchange": profile.get("exchange"),
        }

        cache.set(cache_key, data, timeout=60 * 60 * 24)  # Cache for 24 hours (60 sec * 60 min * 24 hours)
        return data
    except Exception as e:
        print(f"Error fetching profile for {symbol}: {e}")
        return None
    




# formats a number into usd
def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"