from django.urls import path
from . import views
  

urlpatterns = [
path('', views.home,name='home'),
path('register/',views.register,name='register'),
path('login/',views.login_page,name='login'),
path('logout/',views.logout_page,name='logout'),
path('cart/',views.cart_page,name='cart'),
path('fav/',views.fav_page,name='fav'),
path('favviewpage/',views.favviewpage,name='favviewpage'),
path('remove_fav/<str:fid>',views.remove_fav,name='remove_fav'),
path('remove_cart/<str:cid>',views.remove_cart,name='remove_cart'),
path('collections/',views.collections,name='collections'),
path('collections/<str:name>',views.collectionsview,name='collections'),
path('collections/<str:cname>/<str:pname>',views.product_details,name='product_details'),
path('addtocart/',views.add_to_cart,name='add_to_cart'),
path('shop_now/', views.shop_now, name='shop_now'),
path('create_order_from_cart/', views.create_order_from_cart, name='create_order_from_cart'),
path('checkout/<int:order_id>/', views.checkout, name='checkout'),
path('process_payment/<int:order_id>/', views.process_payment, name='process_payment'),
path('order_confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
path('feedback/', views.feedback, name='feedback'),
path('about/', views.about, name='about'),
path('dashboard/', views.dashboard, name='dashboard'),
path('update_profile/', views.update_profile, name='update_profile'),
path('settings/', views.settings, name='settings'),

]
