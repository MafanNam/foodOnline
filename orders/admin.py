from django.contrib import admin

from .models import Payment, Order, OrderedFood


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_id', 'payment_method', 'amount', 'status')


class OrderedFoodInline(admin.TabularInline):
    model = OrderedFood
    readonly_fields = ('order', 'payment', 'user', 'food_item', 'quantity', 'price', 'amount')
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'payment', 'order_number', 'total', 'payment_method', 'status', 'order_placed_to', 'is_ordered')
    inlines = [OrderedFoodInline]


@admin.register(OrderedFood)
class OrderedFoodAdmin(admin.ModelAdmin):
    list_display = ('order', 'payment', 'user', 'food_item', 'quantity', 'price')
