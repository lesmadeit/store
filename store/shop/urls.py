from django.urls import path
from django.utils.regex_helper import normalize
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.home, name='home'),
    path('shop/', views.shop, name='shop'),
    path('shop/<slug:category_slug>/', views.shop, name='categories'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact_us, name='contact_us'),
    path('shop/<slug:category_slug>/<slug:product_details_slug>/', views.product_details, name='product_details'),
    path('featured/', views.featured_products, name='featured_products'),
    path('search/', views.search, name='search'),
    path('review/<int:product_id>/', views.review, name='review'),
    
]
