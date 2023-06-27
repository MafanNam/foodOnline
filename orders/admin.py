from django.contrib import admin

from .models import Payment, Order, OrderedFood


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_id', 'payment_method', 'amount', 'status')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'payment', 'order_number', 'total', 'payment_method', 'status')


@admin.register(OrderedFood)
class OrderedFoodAdmin(admin.ModelAdmin):
    list_display = ('order', 'payment', 'user', 'food_item', 'quantity', 'price')
