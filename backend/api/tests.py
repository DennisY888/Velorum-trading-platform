from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from decimal import Decimal
from .models import UserProfile, Portfolio, History, Watchlist
from .views import lookup
from unittest.mock import patch
from rest_framework_simplejwt.tokens import RefreshToken




class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.user_profile = UserProfile.objects.get(user=self.user)


    # check UserProfile automatically created when User created
    def test_user_profile_creation(self):
        self.assertEqual(self.user_profile.user, self.user)
        self.assertEqual(self.user_profile.cash, Decimal('100000.00'))

    # check Portfolio can be created and associated with UserProfile
    def test_portfolio_creation(self):
        portfolio = Portfolio.objects.create(user=self.user_profile, symbol='AAPL', shares=10)
        self.assertEqual(portfolio.user, self.user_profile)
        self.assertEqual(portfolio.symbol, 'AAPL')
        self.assertEqual(portfolio.shares, 10)

    # check History can be created correctly and associated with UserProfile
    def test_history_creation(self):
        history = History.objects.create(
            user=self.user_profile,
            symbol='AAPL',
            shares=10,
            method='buy',
            price=Decimal('150.00')
        )
        self.assertEqual(history.user, self.user_profile)
        self.assertEqual(history.symbol, 'AAPL')
        self.assertEqual(history.shares, 10)
        self.assertEqual(history.method, 'buy')
        self.assertEqual(history.price, Decimal('150.00'))

    
    # test WatchList can be created and associated with UserProfile
    def test_watchlist_creation(self):
        watchlist_item = Watchlist.objects.create(user=self.user_profile, symbol='AAPL')
        self.assertEqual(watchlist_item.user, self.user_profile)
        self.assertEqual(watchlist_item.symbol, 'AAPL')
        self.assertEqual(str(watchlist_item), f"{self.user_profile.user.username} - Watching AAPL")

    # test Watchlist model uniqueness on user-symbol pair
    def test_watchlist_unique_constraint(self):
        Watchlist.objects.create(user=self.user_profile, symbol='AAPL')
        with self.assertRaises(Exception):
            # Trying to add the same stock again should raise an IntegrityError
            Watchlist.objects.create(user=self.user_profile, symbol='AAPL')

    def test_multiple_stocks_in_watchlist(self):
        Watchlist.objects.create(user=self.user_profile, symbol='AAPL')
        Watchlist.objects.create(user=self.user_profile, symbol='GOOGL')
        self.assertEqual(Watchlist.objects.filter(user=self.user_profile).count(), 2)

    def test_watchlist_item_deletion(self):
        watchlist_item = Watchlist.objects.create(user=self.user_profile, symbol='AAPL')
        watchlist_item.delete()
        self.assertEqual(Watchlist.objects.filter(user=self.user_profile).count(), 0)



    







class ViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.user_profile = UserProfile.objects.get(user=self.user)

    def get_tokens_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


    # register a new user
    def test_create_user(self):
        url = reverse('register')
        data = {'username': 'newuser', 'password': 'newpassword'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())


    #  ensures two tokens are generated when user logs in (api/token/)
    def test_token_obtain(self):
        url = reverse('get_token')
        data = {'username': 'testuser', 'password': '12345'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    # authenciated user should be able to check stock price
    def test_get_stock_quote_authenticated(self):
        tokens = self.get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        url = reverse('get_stock_quote', kwargs={'symbol': 'AAPL'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('current_price', response.data)

    
    def test_get_stock_quote_unauthenticated(self):
        url = reverse('get_stock_quote', kwargs={'symbol': 'AAPL'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_buy_stock_authenticated(self):
        tokens = self.get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        url = reverse('portfolio-buy')
        data = {'symbol': 'AAPL', 'shares': 10}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertTrue(Portfolio.objects.filter(user=self.user_profile, symbol='AAPL').exists())

    def test_buy_stock_unauthenticated(self):
        url = reverse('portfolio-buy')
        data = {'symbol': 'AAPL', 'shares': 10}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)



    def test_get_index_authenticated(self):
        tokens = self.get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        url = reverse('index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('portfolio', response.data)
        self.assertIn('cash', response.data)
        self.assertIn('grand_total', response.data)

    def test_get_index_unauthenticated(self):
        url = reverse('index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)






class FunctionalityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.user_profile = UserProfile.objects.get(user=self.user)
        self.client.force_authenticate(user=self.user)


    def test_buy_and_sell_workflow(self):
        # Buy stocks
        buy_url = reverse('portfolio-buy')
        buy_data = {'symbol': 'AAPL', 'shares': 10}
        buy_response = self.client.post(buy_url, buy_data, format='json')
        self.assertEqual(buy_response.status_code, status.HTTP_200_OK)

        # Check portfolio
        portfolio = Portfolio.objects.get(user=self.user_profile, symbol='AAPL')
        self.assertEqual(portfolio.shares, 10)

        # Sell stocks
        sell_url = reverse('portfolio-sell')
        sell_data = {'symbol': 'AAPL', 'shares': 5}
        sell_response = self.client.post(sell_url, sell_data, format='json')
        self.assertEqual(sell_response.status_code, status.HTTP_200_OK)

        # Check updated portfolio
        portfolio.refresh_from_db()
        self.assertEqual(portfolio.shares, 5)

        # Check history
        history = History.objects.filter(user=self.user_profile, symbol='AAPL')
        self.assertEqual(history.count(), 2)
        self.assertEqual(history.filter(method='buy').count(), 1)
        self.assertEqual(history.filter(method='sell').count(), 1)



    def test_insufficient_funds(self):
        # Set user's cash to a low amount
        self.user_profile.cash = Decimal('10.00')
        self.user_profile.save()

        # Attempt to buy expensive stock
        buy_url = reverse('portfolio-buy')
        buy_data = {'symbol': 'AAPL', 'shares': 1000}
        response = self.client.post(buy_url, buy_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


    def test_sell_without_owning(self):
        sell_url = reverse('portfolio-sell')
        sell_data = {'symbol': 'GOOGL', 'shares': 5}
        response = self.client.post(sell_url, sell_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_leaderboard_ranking(self):
        # Create multiple users with different portfolio values
        for i in range(5):
            user = User.objects.create_user(username=f'user{i}', password='12345')
            profile = UserProfile.objects.get(user=user)
            profile.cash = Decimal(f'{100000 + i * 10000}.00')
            profile.save()
            Portfolio.objects.create(user=profile, symbol='AAPL', shares=10 * (i + 1))

        url = reverse("leaderboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check leaderboard correctly ordered
        leaderboard = response.data
        self.assertTrue(all(leaderboard[i]['total_value'] >= leaderboard[i+1]['total_value'] 
                            for i in range(len(leaderboard)-1)))





class HelperFunctionTests(TestCase):
    def test_lookup_function(self):
        result = lookup('AAPL')
        self.assertIsNotNone(result)
        self.assertIn('current_price', result)

    def test_lookup_invalid_symbol(self):
        result = lookup('INVALID_SYMBOL')
        self.assertIsNone(result)






class AutocompleteSearchTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.force_authenticate(user=self.user)
        self.user_profile = UserProfile.objects.get(user=self.user)
        Portfolio.objects.create(user=self.user_profile, symbol='AAPL', shares=10)
        Portfolio.objects.create(user=self.user_profile, symbol='GOOGL', shares=5)
        Portfolio.objects.create(user=self.user_profile, symbol='BABA', shares=5)
        Portfolio.objects.create(user=self.user_profile, symbol='COIN', shares=5)

 

    def test_owned_stock_search_autocomplete(self):
        url = reverse('search_owned_stocks')  
        response = self.client.get(url, {'q': 'AAP'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('AAPL', [stock['symbol'] for stock in response.data])
        self.assertEqual(len(response.data), 1)

        response = self.client.get(url, {'q': 'AAPL'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('AAPL', [stock['symbol'] for stock in response.data])
        self.assertEqual(len(response.data), 1)
        print(response.data)

        response = self.client.get(url, {'q': 'L'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('AAPL', [stock['symbol'] for stock in response.data])
        self.assertIn('GOOGL', [stock['symbol'] for stock in response.data])
        self.assertEqual(len(response.data), 2)

        response = self.client.get(url, {'q': 'o'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('COIN', [stock['symbol'] for stock in response.data])
        self.assertIn('GOOGL', [stock['symbol'] for stock in response.data])
        self.assertEqual(len(response.data), 2)

        response = self.client.get(url, {'q': 'googl'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('GOOGL', [stock['symbol'] for stock in response.data])
        self.assertEqual(len(response.data), 1)

        response = self.client.get(url, {'q': 'aap'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('AAPL', [stock['symbol'] for stock in response.data])
        self.assertEqual(len(response.data), 1)





    

class TransactionHistoryTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.force_authenticate(user=self.user)
        self.user_profile = UserProfile.objects.get(user=self.user)
        History.objects.create(
            user=self.user_profile,
            symbol='AAPL',
            shares=10,
            method='buy',
            price=Decimal('150.00')
        )

    def test_transaction_details(self):
        url = reverse('history-list')  # or 'history-my_history', depending on what you want to test
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        transaction = response.data[0]
        self.assertEqual(transaction['symbol'], 'AAPL')
        self.assertEqual(transaction['method'], 'buy')
        self.assertEqual(transaction['shares'], 10)
        self.assertTrue('transacted' in transaction)






class WatchlistFunctionalityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.force_authenticate(user=self.user)
        self.user_profile = UserProfile.objects.get(user=self.user)

    def test_add_stock_to_watchlist(self):
        url = reverse('watchlist-add-to-watchlist')  
        data = {'symbol': 'AAPL'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Watchlist.objects.filter(user=self.user_profile, symbol='AAPL').exists())

    def test_remove_stock_from_watchlist(self):
        Watchlist.objects.create(user=self.user_profile, symbol='AAPL')
        url = reverse('watchlist-remove-from-watchlist')  
        data = {'symbol': 'AAPL'}
        response = self.client.delete(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Watchlist.objects.filter(user=self.user_profile, symbol='AAPL').exists())

    def test_add_duplicate_stock_to_watchlist(self):
        Watchlist.objects.create(user=self.user_profile, symbol='AAPL')
        url = reverse('watchlist-add-to-watchlist') 
        data = {'symbol': 'AAPL'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)







class LeaderboardViewTests(APITestCase):
    def setUp(self):
        # Set up some users and their portfolios
        self.user1 = User.objects.create_user(username='user1', password='password')
        self.user2 = User.objects.create_user(username='user2', password='password')
        self.user3 = User.objects.create_user(username='user3', password='password')

        self.user_profile1 = UserProfile.objects.get(user=self.user1)
        self.user_profile2 = UserProfile.objects.get(user=self.user2)
        self.user_profile3 = UserProfile.objects.get(user=self.user3)


        self.user_profile1.cash = 10000.00
        self.user_profile2.cash = 20000.00
        self.user_profile3.cash = 15000.00
        self.user_profile1.save()
        self.user_profile2.save()
        self.user_profile3.save()
        
        
        # Mocking the lookup function to return predefined stock prices
        self.mock_lookup = patch('api.views.lookup', side_effect=self.mocked_lookup).start()

        Portfolio.objects.create(user=self.user_profile1, symbol='AAPL', shares=10) # $11500
        Portfolio.objects.create(user=self.user_profile2, symbol='GOOGL', shares=5) # $25000
        Portfolio.objects.create(user=self.user_profile3, symbol='MSFT', shares=15) # $18000

        self.client = APIClient()
        self.tokens = self.get_tokens_for_user(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')


    def get_tokens_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


    def tearDown(self):
        self.mock_lookup.stop()



    def mocked_lookup(self, symbol):
        stock_data = {
            'AAPL': {'current_price': 150.00},
            'GOOGL': {'current_price': 1000.00},
            'MSFT': {'current_price': 200.00}
        }
        return stock_data.get(symbol, None)




    def test_leaderboard_top_10(self):
        """
        Ensure that the leaderboard correctly returns the top 10 users by total portfolio value.
        """
        url = reverse('leaderboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # Only 3 users in the setup
        
        # Validate the order
        self.assertEqual(response.data[0]['user'], 'user2')
        self.assertEqual(response.data[1]['user'], 'user3')
        self.assertEqual(response.data[2]['user'], 'user1')


    def test_search_user_found(self):
        """
        Ensure that searching for a specific username returns the correct user(s) and their rank.
        """
        url = reverse('leaderboard')
        response = self.client.get(url, {'q': 'user2'})

        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Should return exactly one user
        
        # Validate the returned data
        self.assertEqual(response.data[0]['user'], 'user2')
        self.assertEqual(response.data[0]['ranking'], 1)
        self.assertEqual(response.data[0]['total_value'], '$25,000.00')



        response = self.client.get(url, {'q': 'us'})

        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # Should return exactly one user
        
        # Validate the returned data
        self.assertEqual(response.data[0]['user'], 'user2')
        self.assertEqual(response.data[0]['ranking'], 1)
        self.assertEqual(response.data[0]['total_value'], '$25,000.00')

        self.assertEqual(response.data[1]['user'], 'user3')
        self.assertEqual(response.data[1]['ranking'], 2)
        self.assertEqual(response.data[2]['user'], 'user1')
        self.assertEqual(response.data[2]['ranking'], 3)



    def test_search_user_not_found(self):
        """
        Ensure that searching for a non-existent username returns an empty list.
        """
        url = reverse('leaderboard')
        response = self.client.get(url, {'q': 'nonexistentuser'})
        

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # No users should be returned



    def test_search_user_partial_match(self):
        """
        Ensure that a partial match in the username returns the correct user(s).
        """
        url = reverse('leaderboard')
        response = self.client.get(url, {'q': 'user'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # Should return all users with 'user' in the username

        # Validate that users are correctly ranked and ordered
        self.assertEqual(response.data[0]['user'], 'user2')
        self.assertEqual(response.data[0]['ranking'], 1)
        self.assertEqual(response.data[1]['user'], 'user3')
        self.assertEqual(response.data[1]['ranking'], 2)
        self.assertEqual(response.data[2]['user'], 'user1')
        self.assertEqual(response.data[2]['ranking'], 3)



    def test_leaderboard_ranking_calculation(self):
        """
        Ensure that the ranking calculation correctly accounts for portfolio values.
        """
        url = reverse('leaderboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)


        # Validate the ranking based on total portfolio value
        self.assertEqual(response.data[0]['user'], 'user2')
        self.assertEqual(response.data[1]['user'], 'user3')
        self.assertEqual(response.data[2]['user'], 'user1')


    def test_search_user_missing_query(self):
        """
        Ensure that the search endpoint returns the top 10 users when the query parameter is missing.
        """
        url = reverse('leaderboard')
        response = self.client.get(url)  # No query parameter provided
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # Should return the top 3 users (or however many exist)


