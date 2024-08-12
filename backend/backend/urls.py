
from django.contrib import admin
from django.urls import path, include
from api.views import CreateUserView
# pre-build views (instead of our own in views.py) that allow us to obtain access and refresh tokens and to refresh the token
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView 


urlpatterns = [
    path('admin/', admin.site.urls),

    # we keep all routes related to authentication here just for clarity
    path("api/user/register/", CreateUserView.as_view(), name="register"), # CreaterUserView class already includes html form and css for the web page
    path("api/token/", TokenObtainPairView.as_view(), name="get_token"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("api-auth/", include("rest_framework.urls")),  # pre-built views from REST framework for authentication

    # all the paths in stock_simulator.urls will begin with "stock_simulator/", then follow with their route in urls.py
    path("api/", include("api.urls")),
]
