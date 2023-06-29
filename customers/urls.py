from django.urls import path
from accounts import views as AccountViews
from . import views

urlpatterns = [
    path('', AccountViews.custDashboard, name='customer'),
    path('profile/', views.c_profile, name='c_profile'),
    path('my_orders/', views.my_orders, name='customer_my_orders'),
    path('order_detail/<int:order_number>/', views.order_detail, name='order_detail'),
    path('profile/change_password/', views.change_password, name='change_password'),
]
