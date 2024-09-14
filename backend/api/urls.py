from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'portfolio', PortfolioViewSet)
router.register(r'history', HistoryViewSet)
router.register(r'watchlist', WatchlistViewSet)  

urlpatterns = [
    path('', include(router.urls)),
    path('index/', IndexView.as_view(), name='index'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    path('quote/<str:symbol>/', get_stock_quote, name='get_stock_quote'),
    path('search-owned-stocks/', OwnedStockSearchView.as_view(), name='search_owned_stocks'),  # for SELL autocomplete
    path('portfolio-history/', PortfolioHistoryView.as_view(), name='portfolio_history'),
    path('portfolio-breakdown/', PortfolioBreakdownView.as_view(), name='portfolio_breakdown'),
]



"""
IndexView will be accessible at api/index/
LeaderboardView will be accessible at api/leaderboard/
get_stock_quote function will be accessible at api/quote/<symbol>/
PortfolioViewSet views will be accessible at:

api/portfolio/ (list)
api/portfolio/<id>/ (detail)
api/portfolio/buy/ (buy action)
api/portfolio/sell/ (sell action)

HistoryViewSet views will be accessible at:

api/history/ (list)
api/history/<id>/ (detail)
api/history/my_history/ (my_history action)

WatchlistViewSet views will be accessible at:

api/watchlist/ (list)
api/watchlist/<id>/ (detail)
api/watchlist/add_to_watchlist/ (add_to_watchlist action)
api/watchlist/remove_from_watchlist/ (remove_from_watchlist action)

OwnedStockSearchView will be accessible at api/search-owned-stocks/
"""
