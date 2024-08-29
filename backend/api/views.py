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
from .helpers import lookup, usd
from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.response import Response



# creates a new User entry, and consequently UserProfile entry
class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]



# retrieves stock metrics data given a symbol
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_stock_quote(request, symbol):
    data = lookup(symbol)
    if data:
        current_price = Decimal(data['current_price'])  # Convert to Decimal
        prev_close = Decimal(data['previous_close'])
        percent_change = Decimal((current_price - prev_close) / prev_close) * 100
        data["daily_change"] = percent_change
        return Response(data, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Could not retrieve stock data'}, status=status.HTTP_400_BAD_REQUEST)



#
class PortfolioViewSet(viewsets.ModelViewSet):
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user_profile = UserProfile.objects.get(user=self.request.user)
        serializer.save(user=user_profile)



    # buy page
    @action(detail=False, methods=['post'])
    def buy(self, request):
        symbol = request.data.get('symbol')
        shares = int(request.data.get('shares'))

        if not symbol or shares <= 0:
            return Response({'error': 'Invalid symbol or shares'}, status=status.HTTP_400_BAD_REQUEST)

        stock_data = lookup(symbol)
        if not stock_data:
            return Response({'error': 'Stock symbol not found'}, status=status.HTTP_400_BAD_REQUEST)

        user_profile = UserProfile.objects.get(user=request.user)
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
            name=stock_data['name'],
            new_cash=user_profile.cash,
            total_value=shares*stock_data['current_price']
        )

        return Response({'message': 'Stock purchased successfully'}, status=status.HTTP_200_OK)




    # sell page
    @action(detail=False, methods=['post'])
    def sell(self, request):
        symbol = request.data.get('symbol')
        shares = int(request.data.get('shares'))

        if not symbol or shares <= 0:
            return Response({'error': 'Invalid symbol or shares'}, status=status.HTTP_400_BAD_REQUEST)

        user_profile = UserProfile.objects.get(user=request.user)
        portfolio_item = get_object_or_404(Portfolio, user=user_profile, symbol=symbol)

        if portfolio_item.shares < shares:
            return Response({'error': 'Not enough shares to sell'}, status=status.HTTP_400_BAD_REQUEST)

        stock_data = lookup(symbol)
        if not stock_data:
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
            name=stock_data['name'],
            new_cash=user_profile.cash,
            total_value=shares*stock_data['current_price']
        )

        return Response({'message': 'Stock sold successfully'}, status=status.HTTP_200_OK)






# partial query only works for symbol, not company names
class OwnedStockSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').upper()
        user_profile = UserProfile.objects.get(user=request.user)
        if query:
            # Filtering owned stocks based on query
            owned_stocks = Portfolio.objects.filter(
                user=user_profile,
                symbol__icontains=query
            )
            data = [lookup(stock.symbol) for stock in owned_stocks]
            return Response(data, status=status.HTTP_200_OK)
        return Response({"error": "Query parameter 'q' is missing"}, status=status.HTTP_400_BAD_REQUEST)







# Transaction History page
from rest_framework.pagination import LimitOffsetPagination

class HistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = History.objects.all()
    serializer_class = HistorySerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def my_history(self, request):
        user_profile = UserProfile.objects.get(user=request.user)
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




    


# leaderboard page
class LeaderboardView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = UserProfile.objects.all()
        user_data = []

        for user_profile in queryset:
            total_stock_value = Decimal(0)
            for portfolio in user_profile.portfolios.all():
                stock_data = lookup(portfolio.symbol)
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
        user_profile = UserProfile.objects.get(user=request.user)
        portfolio = Portfolio.objects.filter(user=user_profile)
        portfolio_data = []

        total_value = Decimal(0)  # Initialize as Decimal
        for item in portfolio:
            stock_data = lookup(item.symbol)
            if stock_data:
                current_price = Decimal(stock_data['current_price'])  # Convert to Decimal
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

        current_cash = user_profile.cash  # Assuming this is already a Decimal
        grand_total = current_cash + total_value  # Both are Decimals now

        return Response({
            'portfolio': portfolio_data,
            'cash': current_cash,
            'grand_total': grand_total,
        })






class WatchlistViewSet(viewsets.ModelViewSet):
    queryset = Watchlist.objects.all()
    serializer_class = WatchlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_profile = UserProfile.objects.get(user=self.request.user)
        return Watchlist.objects.filter(user=user_profile)

    @action(detail=False, methods=['get'])
    def my_watchlist(self, request):
        user_profile = UserProfile.objects.get(user=request.user)
        watchlist = self.get_queryset().filter(user=user_profile).order_by('-id')

        # Apply pagination, retrieves from database only the current pagination data
        paginator = LimitOffsetPagination()
        paginated_watchlist = paginator.paginate_queryset(watchlist, request)

        paginated_watchlist_data = []

        for item in paginated_watchlist:
            stock_data = lookup(item.symbol)
            if stock_data:
                current_price = Decimal(stock_data['current_price'])  # Convert to Decimal
                prev_close = Decimal(stock_data['previous_close'])
                percent_change = Decimal((current_price - prev_close) / prev_close) * 100
                paginated_watchlist_data.append({
                    'symbol': item.symbol,
                    'name': stock_data['name'],
                    'current_price': current_price,
                    'daily_change': percent_change,
                })

        return paginator.get_paginated_response(paginated_watchlist_data)


    @action(detail=False, methods=['post'])
    def add_to_watchlist(self, request):
        symbol = request.data.get('symbol')
        user_profile = UserProfile.objects.get(user=request.user)

        # Check if the symbol is already in the watchlist
        if Watchlist.objects.filter(user=user_profile, symbol=symbol).exists():
            return Response({'error': 'Stock is already in watchlist'}, status=status.HTTP_400_BAD_REQUEST)

        watchlist_item = Watchlist.objects.create(user=user_profile, symbol=symbol)
        return Response({'message': 'Stock added to watchlist', 'watchlist_item': WatchlistSerializer(watchlist_item).data}, status=status.HTTP_201_CREATED)


    @action(detail=False, methods=['delete'])
    def remove_from_watchlist(self, request):
        symbol = request.data.get('symbol')
        user_profile = UserProfile.objects.get(user=request.user)
        watchlist_item = Watchlist.objects.filter(user=user_profile, symbol=symbol).first()

        if not watchlist_item:
            return Response({'error': 'Stock not found in watchlist'}, status=status.HTTP_404_NOT_FOUND)

        watchlist_item.delete()
        return Response({'message': 'Stock removed from watchlist'}, status=status.HTTP_200_OK)