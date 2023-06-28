from django.contrib.auth.decorators import login_required
from django.contrib.gis.db.models.functions import Distance
from django.db.models import Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect

from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D

from accounts.models import UserProfile
from marketplace.context_processors import get_cart_counter, get_cart_amounts
from marketplace.models import Cart
from menu.models import Category, FoodItem
from orders.forms import OrderForm
from vendor.models import Vendor, OpeningHour

from datetime import date


def marketplace(request):
    vendors = Vendor.objects.filter(is_approved=True, user__is_active=True)
    vendor_count = vendors.count()

    context = {
        'vendors': vendors,
        'vendor_count': vendor_count,
    }

    return render(request, 'marketplace/listings.html', context)


def vendor_detail(request, vendor_slug):
    vendor = get_object_or_404(Vendor, vendor_slug=vendor_slug)

    categories = Category.objects.filter(vendor=vendor).prefetch_related(
        Prefetch(
            'food_items',
            queryset=FoodItem.objects.filter(is_available=True)
        )
    )

    opening_hours = OpeningHour.objects.filter(vendor=vendor).order_by('day', '-from_hour')

    # Check current day's opening hours.
    today_date = date.today()
    today = today_date.isoweekday()

    current_opening_hours = OpeningHour.objects.filter(vendor=vendor, day=today)

    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user)
    else:
        cart_items = None

    context = {
        'vendor': vendor,
        'categories': categories,
        'cart_items': cart_items,
        'opening_hours': opening_hours,
        'current_opening_hours': current_opening_hours,
    }
    return render(request, 'marketplace/vendor_detail.html', context)


def add_to_cart(request, food_id=None):
    if request.user.is_authenticated:

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Check if the food item exists
            try:
                food_item = FoodItem.objects.get(id=food_id)
                # Check if the user has already added that food to the cart
                try:
                    chkCart = Cart.objects.get(user=request.user, food_item=food_item)
                    # Increase the cart quantity
                    chkCart.quantity += 1
                    chkCart.save()
                    return JsonResponse({'status': 'Success', 'message': 'Increased the cart quantity',
                                         'cart_counter': get_cart_counter(request),
                                         'cart_amount': get_cart_amounts(request),
                                         'qty': chkCart.quantity})
                except:
                    chkCart = Cart.objects.create(user=request.user, food_item=food_item, quantity=1)
                    return JsonResponse({'status': 'Success', 'message': 'Added the food to the cart',
                                         'cart_counter': get_cart_counter(request),
                                         'cart_amount': get_cart_amounts(request),
                                         'qty': chkCart.quantity})
            except:
                return JsonResponse({'status': 'Failed', 'message': 'This food does not exist!'})
        else:
            return JsonResponse({'status': 'Failed', 'message': 'Invalid request!'})

    else:
        return JsonResponse({'status': 'login_required', 'message': 'Please login to continue'})


def decrease_cart(request, food_id):
    if request.user.is_authenticated:

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Check if the food item exists
            try:
                food_item = FoodItem.objects.get(id=food_id)
                # Check if the user has already added that food to the cart
                try:
                    chkCart = Cart.objects.get(user=request.user, food_item=food_item)
                    if chkCart.quantity > 1:
                        # Decrease the cart quantity
                        chkCart.quantity -= 1
                        chkCart.save()
                    else:
                        chkCart.delete()
                        chkCart.quantity = 0
                    return JsonResponse({'status': 'Success', 'cart_counter': get_cart_counter(request),
                                         'cart_amount': get_cart_amounts(request),
                                         'qty': chkCart.quantity})
                except:
                    return JsonResponse({'status': 'Failed', 'message': 'You do not have this item in your cart'})
            except:
                return JsonResponse({'status': 'Failed', 'message': 'This food does not exist!'})
        else:
            return JsonResponse({'status': 'Failed', 'message': 'Invalid request!'})

    else:
        return JsonResponse({'status': 'login_required', 'message': 'Please login to continue'})


@login_required(login_url='login')
def cart(request):
    cart_items = Cart.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'cart_items': cart_items,
    }
    return render(request, 'marketplace/cart.html', context)


def delete_cart(request, cart_id):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                # Check if the cart item exists
                cart_item = Cart.objects.get(user=request.user, id=cart_id)
                if cart_item:
                    cart_item.delete()

                return JsonResponse({'status': 'Success', 'message': 'Cart item has been deleted!',
                                     'cart_counter': get_cart_counter(request),
                                     'cart_amount': get_cart_amounts(request)})
            except:
                return JsonResponse({'status': 'Failed', 'message': 'Cart item does not exist!'})
        else:
            return JsonResponse({'status': 'Failed', 'message': 'Invalid request'})

    return


def search(request):
    if 'address' not in request.GET:
        return redirect('marketplace')

    address = request.GET['address']
    keyword = request.GET['keyword']
    latitude = request.GET['lat']
    longitude = request.GET['lng']
    radius = request.GET['radius']

    # get vendor id that has food item the user is looking for
    fetch_vendor_by_food_items = FoodItem.objects.filter(food_title__icontains=keyword, is_available=True).values_list(
        'vendor', flat=True)
    vendors = Vendor.objects.filter(
        Q(id__in=fetch_vendor_by_food_items) | Q(vendor_name__icontains=keyword, is_approved=True,
                                                 user__is_active=True))
    if latitude and longitude and radius:
        pnt = GEOSGeometry(f"POINT({longitude} {latitude})")

        vendors = Vendor.objects.filter(
            Q(id__in=fetch_vendor_by_food_items) | Q(vendor_name__icontains=keyword, is_approved=True,
                                                     user__is_active=True),
            user_profile__location__distance_lte=(pnt, D(km=radius))).annotate(
            distance=Distance("user_profile__location", pnt)).order_by('distance')

        for v in vendors:
            v.kms = round(v.distance.km, 1)

    vendor_count = vendors.count()

    context = {
        'vendors': vendors,
        'vendor_count': vendor_count,
        'source_location': address,
    }

    return render(request, 'marketplace/listings.html', context)


@login_required(login_url='login')
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user).order_by('created_at')
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('marketplace')

    user_profile = UserProfile.objects.get(user=request.user)
    default_values = {
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'email': request.user.email,
        'phone': request.user.phone_number,
        'address': user_profile.address,
        'country': user_profile.country,
        'state': user_profile.state,
        'city': user_profile.city,
        'pin_code': user_profile.pin_code,
    }
    form = OrderForm(initial=default_values)

    context = {
        'form': form,
        'cart_items': cart_items,
        'cart_count': cart_count,
    }
    return render(request, 'marketplace/checkout.html', context)
