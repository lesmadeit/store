from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from .models import Product, Category
from cart.views import _cart_id
from cart.models import CartItem
from .models import ReviewRating
from .forms import ReviewForm
from django.contrib import messages
from orders.models import OrderProduct
from .models import ProductGallery
from accounts.views import logout
from . import forms
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from .forms import ContactForm





def home(request):
    if request.user.is_authenticated and request.user.is_staff:
        logout(request)
        return redirect('accounts:login')
    
    products = Product.objects.all().filter(is_available=True)
    featured_products = Product.objects.filter(featured=True, is_available=True)
    new_products = Product.objects.filter(new=True, is_available=True)  # Added for new arrivals
    
    # Paginate featured products (4 per page)
    featured_paginator = Paginator(featured_products, 4)
    featured_page = request.GET.get('featured_page')
    paged_featured_products = featured_paginator.get_page(featured_page)
    featured_products_count = featured_products.count()
    
    # Paginate new arrival products (4 per page)
    new_paginator = Paginator(new_products, 4)
    new_page = request.GET.get('new_page')  # Separate query param for new arrivals
    paged_new_products = new_paginator.get_page(new_page)
    new_products_count = new_products.count()
    
    context = {
        'products': products,
        'featured_products': paged_featured_products,
        'featured_products_count': featured_products_count,
        'new_products': paged_new_products,  # Added for new arrivals
        'new_products_count': new_products_count,  # Added for new arrivals
    }
    return render(request, 'shop/index.html', context)


def shop(request, category_slug=None):
    if request.user.is_authenticated and request.user.is_staff:
        # Log the user out
        logout(request)
        # Redirect to the login page or any other page
        return redirect('accounts:login')
    
    categories = None
    products = None
    featured_products = Product.objects.filter(featured=True, is_available=True).order_by('-id')[:3]  # Added for featured products

    if category_slug:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=categories, is_available=True)
    else:
        products = Product.objects.filter(is_available=True)
    
    paginator = Paginator(products, 6)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)
    products_count = products.count()
    
    # Note: The loop below seems incomplete or unnecessary as it doesn't store the reviews.
    # Consider revising if reviews are needed in the template.
    for product in products:
        reviews = ReviewRating.objects.order_by('-updated_at').filter(product_id=product.id, status=True)

    context = {
        'category_slug': category_slug,
        'products': paged_products,
        'products_count': products_count,
        'featured_products': featured_products,  # Added to context
    }
    return render(request, 'shop/shop/shop.html', context)

def about(request):
    return render(request, 'shop/shop/about.html',)

def contact_us(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']

            full_message = f"Message from {name} ({email}):\n\n{message}"
            
            # Send email
            send_mail(
                f'Message from {name}', #subject
                full_message,           #message
                'lesliemwendwa10@gmail.com', #To avoid SMTP issues
                ['lesliemwendwa10@gmail.com'],  # To (your email)
            )
            messages.success(request, 'Your message has been sent successfully. We will be in touch')
            return redirect('shop:contact_us')  
    else:
        form = ContactForm()
    
    return render(request, 'shop/shop/contact_us.html', {'form': form})




def product_details(request, category_slug, product_details_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_details_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except Exception as e:
        return e

    if request.user.is_authenticated:
        try:
            orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        except OrderProduct.DoesNotExist:
            orderproduct = None
    else:
        orderproduct = None

    reviews = ReviewRating.objects.order_by('-updated_at').filter(product_id=single_product.id, status=True)
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)
    related_products = Product.objects.filter(category=single_product.category, is_available=True).exclude(id=single_product.id)[:5]
    categories = Category.objects.all()
    # Compute category counts
    category_counts = {category.id: category.product_set.filter(is_available=True).count() for category in categories}
    
    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
        'product_gallery': product_gallery,
        'related_products': related_products,
        'categories': categories,
        'category_counts': category_counts,  # Added for category counts
        'featured_products': Product.objects.filter(featured=True, is_available=True)[:4],
    }
    return render(request, 'shop/shop/product_details.html', context)

def featured_products(request):
    products = Product.objects.filter(featured=True, is_available=True)
    paginator = Paginator(products, 4)  # 4 products per page to match homepage
    page = request.GET.get('featured_page')  # Match homepage's query param
    paged_products = paginator.get_page(page)
    products_count = products.count()
    return render(request, 'shop/shop/featured_products.html', {
        'products': paged_products,
        'products_count': products_count,
    })


def search(request):
    products_count = 0
    products = None
    paged_products = None
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword :
            products = Product.objects.filter(Q(description__icontains=keyword) | Q(name__icontains=keyword))
            
            products_count = products.count()
            
    
    context = {
        'products': products,
        'products_count': products_count,
    }
    return render(request, 'shop/shop/search.html', context)



def review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id,product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you, your review has been updated!')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank you, your review Posted!')
                return redirect(url)
