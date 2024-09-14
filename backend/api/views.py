from django.shortcuts import render
from django.contrib.auth.models import User
from .serializers import *
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import *
from rest_framework import generics
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .helpers import lookup_quote, lookup_basic_financial, lookup_profile, usd
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.pagination import LimitOffsetPagination
import random





# Creates a new User entry, and consequently UserProfile entry
class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]




# Retrieves stock metrics data given a symbol
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_stock_quote(request, symbol):
    # Use lookup_quote for real-time stock data
    quote_data = lookup_quote(symbol)
    # Use lookup_basic_financial for financial metrics
    financial_data = lookup_basic_financial(symbol)
    # Use lookup_profile for company profile info
    profile_data = lookup_profile(symbol)

    if quote_data and financial_data and profile_data:
        current_price = Decimal(quote_data['current_price'])
        prev_close = Decimal(quote_data['previous_close'])
        percent_change = Decimal((current_price - prev_close) / prev_close) * 100

        # Combine all data into the response
        data = {
            'symbol': quote_data['symbol'],
            'current_price': quote_data['current_price'],
            'opening_price': quote_data['opening_price'],
            'previous_close': quote_data['previous_close'],
            'high_price': quote_data['high_price'],
            'low_price': quote_data['low_price'],
            'daily_change': percent_change,
            'ten_day_avg_volume': financial_data['ten_day_avg_volume'],
            'market_cap': financial_data['market_cap'],
            'pe_ratio': financial_data['pe_ratio'],
            'annual_dividend_yield': financial_data['annual_dividend_yield'],
            '52_week_high': financial_data['52_week_high'],
            '52_week_low': financial_data['52_week_low'],
            'beta': financial_data['beta'],
            'three_month_avg_volume': financial_data['three_month_avg_volume'],
            'name': profile_data['name'],
            'exchange': profile_data['exchange']
        }
        return Response(data, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Could not retrieve stock data'}, status=status.HTTP_400_BAD_REQUEST)




# View for portfolio value over time (line chart)
class PortfolioHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_profile = request.user.userprofile
        history = PortfolioHistory.objects.filter(user=user_profile).order_by('date')  # Sorted by date
        serializer = PortfolioHistorySerializer(history, many=True)
        return Response(serializer.data, status=200)



# View for stock performance breakdown (pie chart)
class PortfolioBreakdownView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_profile = request.user.userprofile
        portfolio = Portfolio.objects.filter(user=user_profile)

        # Calculate the total portfolio value (stocks + cash)
        total_stock_value = Decimal(0)
        portfolio_data = []
        colors = []  # List to keep track of generated colors
        
        for item in portfolio:
            stock_data = lookup_quote(item.symbol)
            if stock_data:
                current_price = Decimal(stock_data['current_price'])
                stock_value = current_price * item.shares
                total_stock_value += stock_value
                
                # Generate a random color for each stock
                color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
                while color in colors:
                    color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
                colors.append(color)
                
                portfolio_data.append({
                    'symbol': item.symbol,
                    'shares': item.shares,
                    'current_value': stock_value,
                    'color': color,
                })
        
        # Calculate the total portfolio value including cash
        total_value_with_cash = total_stock_value + user_profile.cash

        # Add "percent" field for each stock and update the portfolio data
        for stock in portfolio_data:
            stock['percent'] = round((stock['current_value'] / total_value_with_cash) * 100, 2)

        # Generate a random color for cash
        cash_color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        while cash_color in colors:
            cash_color = "#{:06x}".format(random.randint(0, 0xFFFFFF))

        # Calculate the percent of cash relative to the total portfolio value
        cash_percent = round((user_profile.cash / total_value_with_cash) * 100, 2)

        # Prepare the response
        response_data = {
            'portfolio': portfolio_data,
            'cash': {
                'value': user_profile.cash,
                'percent': cash_percent,
                'color': cash_color  # Add a random color for cash
            },
        }

        return Response(response_data, status=200)






class PortfolioViewSet(viewsets.ModelViewSet):
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user_profile = UserProfile.objects.select_related('user').get(user=self.request.user)
        serializer.save(user=user_profile)

    # Buy page
    @action(detail=False, methods=['post'])
    def buy(self, request):
        symbol = request.data.get('symbol')
        shares = int(request.data.get('shares'))

        if not symbol or shares <= 0:
            return Response({'error': 'Invalid symbol or shares'}, status=status.HTTP_400_BAD_REQUEST)

        # Use lookup_quote for stock price and lookup_profile for company name
        stock_data = lookup_quote(symbol)
        profile_data = lookup_profile(symbol)

        if not stock_data or not profile_data:
            return Response({'error': 'Stock symbol not found'}, status=status.HTTP_400_BAD_REQUEST)

        user_profile = UserProfile.objects.select_related('user').get(user=request.user)
        total_cost = Decimal(stock_data['current_price']) * Decimal(shares)

        if user_profile.cash < total_cost:
            return Response({'error': 'Insufficient funds'}, status=status.HTTP_400_BAD_REQUEST)

        portfolio_item, created = Portfolio.objects.get_or_create(
            user=user_profile,
            symbol=symbol
        )
        portfolio_item.shares += shares
        portfolio_item.save()

        user_profile.cash -= total_cost
        user_profile.save()

        History.objects.create(
            user=user_profile,
            symbol=symbol,
            shares=shares,
            method='buy',
            price=stock_data['current_price'],
            name=profile_data['name'],
            new_cash=user_profile.cash,
            total_value=shares * stock_data['current_price']
        )

        return Response({'message': 'Stock purchased successfully'}, status=status.HTTP_200_OK)

    # Sell page
    @action(detail=False, methods=['post'])
    def sell(self, request):
        symbol = request.data.get('symbol')
        shares = int(request.data.get('shares'))

        if not symbol or shares <= 0:
            return Response({'error': 'Invalid symbol or shares'}, status=status.HTTP_400_BAD_REQUEST)

        user_profile = UserProfile.objects.select_related('user').get(user=request.user)
        portfolio_item = get_object_or_404(Portfolio, user=user_profile, symbol=symbol)

        if portfolio_item.shares < shares:
            return Response({'error': 'Not enough shares to sell'}, status=status.HTTP_400_BAD_REQUEST)

        # Use lookup_quote for stock price and lookup_profile for company name
        stock_data = lookup_quote(symbol)
        profile_data = lookup_profile(symbol)

        if not stock_data or not profile_data:
            return Response({'error': 'Stock symbol not found'}, status=status.HTTP_400_BAD_REQUEST)

        portfolio_item.shares -= shares
        portfolio_item.save()

        if portfolio_item.shares == 0:
            portfolio_item.delete()

        total_earnings = Decimal(stock_data['current_price']) * Decimal(shares)
        user_profile.cash += total_earnings
        user_profile.save()

        History.objects.create(
            user=user_profile,
            symbol=symbol,
            shares=shares,
            method='sell',
            price=stock_data['current_price'],
            name=profile_data['name'],
            new_cash=user_profile.cash,
            total_value=shares * stock_data['current_price']
        )

        return Response({'message': 'Stock sold successfully'}, status=status.HTTP_200_OK)




# Partial query only works for symbol, not company names
class OwnedStockSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').upper()
        user_profile = UserProfile.objects.select_related('user').get(user=request.user)
        if query:
            # Filtering owned stocks based on query
            owned_stocks = Portfolio.objects.filter(
                user=user_profile,
                symbol__icontains=query
            )
            data = [lookup_profile(stock.symbol) for stock in owned_stocks]
            return Response(data, status=status.HTTP_200_OK)
        return Response({"error": "Query parameter 'q' is missing"}, status=status.HTTP_400_BAD_REQUEST)





# Transaction History page
class HistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = History.objects.all()
    serializer_class = HistorySerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def my_history(self, request):
        user_profile = UserProfile.objects.select_related('user').get(user=request.user)
        history = self.queryset.filter(user=user_profile).order_by('-transacted')

        # Apply pagination, retrieves from database only the current pagination data
        paginator = LimitOffsetPagination()
        paginated_history = paginator.paginate_queryset(history, request)

        # Build response with new fields included
        response_data = [
            {
                'id': transaction.id,
                'symbol': transaction.symbol,
                'name': transaction.name,
                'shares': transaction.shares,
                'method': transaction.method,
                'price': usd(transaction.price),
                'total_value': usd(transaction.total_value),
                'transacted': transaction.transacted,
                'new_cash': usd(transaction.new_cash)
            }
            for transaction in paginated_history
        ]

        return paginator.get_paginated_response(response_data)




# Leaderboard page
class LeaderboardView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = UserProfile.objects.prefetch_related('portfolios').all()
        user_data = []

        for user_profile in queryset:
            total_stock_value = Decimal(0)
            for portfolio in user_profile.portfolios.all():
                stock_data = lookup_quote(portfolio.symbol)
                if stock_data:
                    total_stock_value += portfolio.shares * Decimal(stock_data['current_price'])
            total_value = user_profile.cash + total_stock_value
            user_data.append({
                'user_profile': user_profile,
                'total_value': total_value
            })

        # Sort by total_value descending
        sorted_data = sorted(user_data, key=lambda x: x['total_value'], reverse=True)

        # Add ranking
        for index, data in enumerate(sorted_data):
            data['ranking'] = index + 1

        return sorted_data

    def list(self, request, *args, **kwargs):
        query = request.query_params.get('q', '')

        # Check if there's a search query
        if query:
            sorted_data = self.get_queryset()
            # Filter the full list based on the search query
            filtered_data = [data for data in sorted_data if query.lower() in data['user_profile'].user.username.lower()]

            # Only return the filtered data based on the search query
            response_data = [
                {
                    'user': data['user_profile'].user.username,
                    'total_value': usd(data['total_value']),
                    'ranking': data['ranking']
                }
                for data in filtered_data
            ]
        else:
            # Return the top 10 users by total portfolio value if no search query
            sorted_data = self.get_queryset()[:10]
            response_data = [
                {
                    'user': data['user_profile'].user.username,
                    'cash': usd(data['user_profile'].cash),
                    'total_value': usd(data['total_value']),
                    'ranking': data['ranking']
                }
                for data in sorted_data
            ]

        return Response(response_data)




# Home page
class IndexView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_profile = UserProfile.objects.select_related('user').get(user=request.user)
        portfolio = Portfolio.objects.filter(user=user_profile)

        portfolio_data = []

        total_value = Decimal(0)
        for item in portfolio:
            stock_data = lookup_quote(item.symbol)
            if stock_data:
                current_price = Decimal(stock_data['current_price'])
                prev_close = Decimal(stock_data['previous_close'])
                percent_change = Decimal((current_price - prev_close) / prev_close) * 100
                item_value = current_price * item.shares
                total_value += item_value
                portfolio_data.append({
                    'symbol': item.symbol,
                    'shares': item.shares,
                    'current_price': current_price,
                    'total_value': item_value,
                    'daily_change': percent_change,
                })

        current_cash = user_profile.cash
        grand_total = current_cash + total_value

        return Response({
            'username': request.user.username,
            'portfolio': portfolio_data,
            'cash': current_cash,
            'grand_total': grand_total,
        })




# Watchlist viewset
class WatchlistViewSet(viewsets.ModelViewSet):
    queryset = Watchlist.objects.all()
    serializer_class = WatchlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_profile = UserProfile.objects.select_related('user').get(user=self.request.user)
        return Watchlist.objects.filter(user=user_profile)

    @action(detail=False, methods=['get'])
    def my_watchlist(self, request):
        user_profile = UserProfile.objects.select_related('user').get(user=request.user)
        watchlist = self.get_queryset().order_by('-id')

        # Apply pagination, retrieves from database only the current pagination data
        paginator = LimitOffsetPagination()
        paginated_watchlist = paginator.paginate_queryset(watchlist, request)

        paginated_watchlist_data = []

        for item in paginated_watchlist:
            stock_data = lookup_quote(item.symbol)
            profile_data = lookup_profile(item.symbol)  # Fetch profile data
            
            if stock_data and profile_data:
                current_price = Decimal(stock_data.get('current_price', 0))  # Default to 0 if missing
                prev_close = Decimal(stock_data.get('previous_close', 0))   # Default to 0 if missing
                percent_change = Decimal((current_price - prev_close) / prev_close) * 100 if prev_close else 0
                paginated_watchlist_data.append({
                    'symbol': item.symbol,
                    'name': profile_data.get('name', 'N/A'),  # Handle missing name
                    'current_price': current_price,
                    'daily_change': percent_change,
                })

        return paginator.get_paginated_response(paginated_watchlist_data)


    @action(detail=False, methods=['post'])
    def add_to_watchlist(self, request):
        symbol = request.data.get('symbol')
        user_profile = UserProfile.objects.select_related('user').get(user=request.user)

        if Watchlist.objects.filter(user=user_profile, symbol=symbol).exists():
            return Response({'error': 'Stock is already in watchlist'}, status=status.HTTP_400_BAD_REQUEST)

        watchlist_item = Watchlist.objects.create(user=user_profile, symbol=symbol)
        return Response({'message': 'Stock added to watchlist', 'watchlist_item': WatchlistSerializer(watchlist_item).data}, status=status.HTTP_201_CREATED)


    @action(detail=False, methods=['delete'])
    def remove_from_watchlist(self, request):
        symbol = request.data.get('symbol')
        user_profile = UserProfile.objects.select_related('user').get(user=request.user)
        watchlist_item = Watchlist.objects.filter(user=user_profile, symbol=symbol).first()

        if not watchlist_item:
            return Response({'error': 'Stock not found in watchlist'}, status=status.HTTP_404_NOT_FOUND)

        watchlist_item.delete()
        return Response({'message': 'Stock removed from watchlist'}, status=status.HTTP_200_OK)
