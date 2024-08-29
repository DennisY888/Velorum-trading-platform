import os
import finnhub  # type: ignore

    




# returns stock metrics for a given stock symbol
# Free tier 60 API calls per minute
def lookup(symbol):
    """Look up detailed quote for symbol using Finnhub API."""
    try:
        api_key = os.environ.get("API_KEY")
        finnhub_client = finnhub.Client(api_key=api_key)
        
        # Get basic quote data
        quote = finnhub_client.quote(symbol)
        
        # Get additional metrics
        metrics = finnhub_client.company_basic_financials(symbol, 'all')['metric']

        profile = finnhub_client.company_profile2(symbol=symbol)
        
        return {
            "symbol": symbol.upper(),
            "name": profile["name"],
            "current_price": round(float(quote["c"]), 2),
            "opening_price": round(float(quote["o"]), 2),
            "previous_close": round(float(quote["pc"]), 2),
            "high_price": round(float(quote["h"]), 2),
            "low_price": round(float(quote["l"]), 2),
            "ten_day_avg_volume": int(metrics.get('10DayAverageTradingVolume', "N/A")),
            "market_cap": round(float(metrics.get('marketCapitalization', 0)), 2),
            "pe_ratio": round(float(metrics.get("peTTM", 0)), 2),
            "annual_dividend_yield": round(float(metrics.get("dividendYieldIndicatedAnnual", 0)), 2),
            "52_week_high": round(float(metrics.get("52WeekHigh", 0)), 2),
            "52_week_low": round(float(metrics.get("52WeekLow", 0)), 2),
            "beta": round(float(metrics.get("beta", 0)), 2),
            "exchange": profile.get("exchange"),
            "three_month_avg_volume": int(metrics.get('3MonthAverageTradingVolume', "N/A")),
        }
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None
    


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"