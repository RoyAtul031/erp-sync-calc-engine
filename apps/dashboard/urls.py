from django.urls import path
from apps.dashboard.views import LandingLoginView, DashboardView, LogoutUserView

urlpatterns = [
    # Landing & Enterprise Authentication Gateway
    path('', LandingLoginView.as_view(), name='landing'),
    path('login/', LandingLoginView.as_view(), name='login'),
    path('logout/', LogoutUserView.as_view(), name='logout'),

    # Enterprise Executive Dashboard & Calculation Studio
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('console/', DashboardView.as_view(), name='console'),
]
