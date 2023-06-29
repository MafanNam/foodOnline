import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

from accounts.forms import UserProfileForm, UserInfoForm
from accounts.models import UserProfile, User
from orders.models import Order, OrderedFood


@login_required(login_url='login')
def c_profile(request):
    profile = get_object_or_404(UserProfile, user=request.user)

    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        user_form = UserInfoForm(request.POST, instance=request.user)
        if profile_form.is_valid() and user_form.is_valid():
            profile_form.save()
            user_form.save()
            messages.success(request, 'Profile updated')
            return redirect('c_profile')
        else:
            messages.error(request, 'Error')

    else:
        profile_form = UserProfileForm(instance=profile)
        user_form = UserInfoForm(instance=request.user)

    context = {
        'profile_form': profile_form,
        'user_form': user_form,
        'profile': profile,
    }
    return render(request, 'customers/c_profile.html', context)


@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        password = request.POST['password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        user = User.objects.get(id=request.user.pk)

        if user.check_password(password):
            if new_password == confirm_password and len(new_password) >= 8 and len(confirm_password) >= 8:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password changed')
                return redirect('login')
            else:
                messages.error(request, 'New Password do not match!')
                return redirect('change_password')
        else:
            messages.error(request, 'Old Password do not match!')
            return redirect('change_password')

    return render(request, 'customers/change_password.html')


@login_required(login_url='login')
def my_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')

    context = {
        'orders': orders,
    }
    return render(request, 'customers/my_orders.html', context)


@login_required(login_url='login')
def order_detail(request, order_number=None):
    try:
        order = Order.objects.get(user=request.user, is_ordered=True, order_number=order_number)
        ordered_food = OrderedFood.objects.filter(order=order)

        subtotal = 0
        for item in ordered_food:
            subtotal += (item.price * item.quantity)

        tax_data = json.loads(order.tax_data)

        context = {
            'order': order,
            'ordered_food': ordered_food,
            'subtotal': subtotal,
            'tax_data': tax_data
        }
        return render(request, 'customers/order_detail.html', context)

    except:
        return redirect('custDashboard')
