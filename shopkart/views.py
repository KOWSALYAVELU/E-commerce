from django.http import  JsonResponse
from django.shortcuts import redirect, render
from shopkart.form import CustomUserForm, FeedbackForm
from . models import *
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def settings(request):
    if not request.user.is_authenticated:
        messages.error(request, "Please login to access settings")
        return redirect('login')
    return render(request, "shop/settings.html")
 
 
def get_dashboard_context(user):
    try:
        user_profile = UserProfile.objects.get(user=user)
        orders = Order.objects.filter(user=user).order_by('-created_at')[:10]  # Last 10 orders
        cart_items = Cart.objects.filter(user=user)
        favorites = Favourite.objects.filter(user=user)
        
        # Calculate total spent and average order value
        all_orders = Order.objects.filter(user=user, payment_status='paid')
        total_spent = sum(order.total_amount for order in all_orders)
        average_order_value = total_spent / len(all_orders) if all_orders else 0
        
        context = {
            'profile': user_profile,
            'orders': orders,
            'cart_items': cart_items,
            'favorites': favorites,
            'order_count': orders.count(),
            'cart_count': cart_items.count(),
            'favorite_count': favorites.count(),
            'total_spent': total_spent,
            'average_order_value': round(average_order_value, 2),
        }
        return context
    except UserProfile.DoesNotExist:
        return None

def home(request):
    products = Product.objects.filter(trending=1)
    return render(request, "shop/index.html", {"products": products})
 
def favviewpage(request):
  if request.user.is_authenticated:
    fav=Favourite.objects.filter(user=request.user)
    return render(request,"shop/fav.html",{"fav":fav})
  else:
    return redirect("/")
 
def remove_fav(request,fid):
  item=Favourite.objects.get(id=fid)
  item.delete()
  return redirect("/favviewpage")
 
 
def cart_page(request):
  if request.user.is_authenticated:
    cart=Cart.objects.filter(user=request.user)
    return render(request,"shop/cart.html",{"cart":cart})
  else:
    return redirect("/")
 
def remove_cart(request,cid):
  cartitem=Cart.objects.get(id=cid)
  cartitem.delete()
  return redirect("/cart")
 
 
 
def fav_page(request):
   logger.info("fav_page called")
   if request.headers.get('x-requested-with')=='XMLHttpRequest':
    logger.info("AJAX request detected")
    if request.user.is_authenticated:
      logger.info(f"User {request.user.id} is authenticated")
      try:
        data=json.loads(request.body)
        logger.info(f"Request body: {request.body}")
        product_id=data['pid']
        logger.info(f"Product ID: {product_id}")
        product_status=Product.objects.get(id=product_id)
        if product_status:
          if Favourite.objects.filter(user=request.user,product_id=product_id).exists():
            logger.info(f"Product {product_id} already in favorites for user {request.user.id}")
            return JsonResponse({'status':'Product Already in Favourite'}, status=200)
          else:
            Favourite.objects.create(user=request.user, product=product_status)
            logger.info(f"Product {product_id} added to favorites for user {request.user.id}")
            return JsonResponse({'status':'Product Added to Favourite'}, status=200)
      except KeyError:
        logger.error("Missing product ID in request body")
        return JsonResponse({'status':'Missing product ID'}, status=400)
      except Product.DoesNotExist:
        logger.error(f"Product with ID {product_id} not found")
        return JsonResponse({'status':'Product not found'}, status=404)
      except Exception as e:
        logger.error(f"Error in fav_page: {str(e)}")  # Use logger instead of print
        return JsonResponse({'status':f'Error: {str(e)}'}, status=500)
    else:
      logger.warning("User not authenticated")
      return JsonResponse({'status':'Login to Add Favourite'}, status=401)
   else:
    logger.warning("Invalid access to fav_page - not AJAX request")
    return JsonResponse({'status':'Invalid Access'}, status=400)
 

def add_to_cart(request):
   if request.headers.get('x-requested-with')=='XMLHttpRequest':
    if request.user.is_authenticated:
      try:
        data=json.loads(request.body)
        product_qty=data['product_qty']
        product_id=data['pid']
        product_status=Product.objects.get(id=product_id)
        if product_status:
          if Cart.objects.filter(user=request.user,product_id=product_id).exists():
            return JsonResponse({'status':'Product Already in Cart'}, status=200)
          else:
            if product_status.quantity >= product_qty:
              Cart.objects.create(user=request.user, product_id=product_id, product_qty=product_qty)
              return JsonResponse({'status':'Product Added to Cart'}, status=200)
            else:
              return JsonResponse({'status':'Product Stock Not Available'}, status=400)
      except KeyError as e:
        return JsonResponse({'status': f'Missing required field: {str(e)}'}, status=400)
      except json.JSONDecodeError:
        return JsonResponse({'status':'Invalid JSON data'}, status=400)
      except Product.DoesNotExist:
        return JsonResponse({'status':'Product not found'}, status=404)
      except Exception as e:
        return JsonResponse({'status': f'Error: {str(e)}'}, status=500)
    else:
      return JsonResponse({'status':'Login to Add Cart'}, status=401)
   else:
    return JsonResponse({'status':'Invalid Access'}, status=400)
 
def logout_page(request):
  if request.user.is_authenticated:
    logout(request)
    messages.success(request,"Logged out Successfully")
  return redirect("/")
 
 
def login_page(request):
  if request.user.is_authenticated:
    return redirect("/")
  else:
    if request.method=='POST':
      name=request.POST.get('username')
      pwd=request.POST.get('password')
      user=authenticate(request,username=name,password=pwd)
      if user is not None:
        login(request,user)
        messages.success(request,"Logged in Successfully")
        return redirect("/")
      else:
        messages.error(request,"Invalid User Name or Password")
        return redirect("/login")
    return render(request,"shop/login.html")
 
def register(request):
    form = CustomUserForm()
    if request.method == 'POST':
        form = CustomUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user, phone_number=request.POST.get('phone_number'), address=request.POST.get('address'))
            messages.success(request, "Registration Success! You can Login Now..!")
            return redirect('/login')
    return render(request, "shop/register.html", {'form': form})
 
def collections(request):
  category=Category.objects.filter(status=0)
  return render(request,"shop/collections.html",{"category":category})
 
def collectionsview(request,name):
  print(f"collectionsview called with name: {name}")
  if(Category.objects.filter(name=name,status=0)):
      products=Product.objects.filter(category__name=name)
      return render(request,"shop/products/index.html",{"products":products,"category_name":name})
  else:
    messages.warning(request,"No Such Category Found")
    return redirect('collections')
 
 
def product_details(request,cname,pname):
    if(Category.objects.filter(name=cname,status=0)):
      if(Product.objects.filter(name=pname,status=0)):
        products=Product.objects.filter(name=pname,status=0).first()
        return render(request,"shop/products/product_details.html",{"products":products})
      else:
        messages.error(request,"No Such Produtct Found")
        return redirect('collections')
    else:
      messages.error(request,"No Such Catagory Found")
      return redirect('collections')

def shop_now(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.user.is_authenticated:
            try:
                data = json.loads(request.body)
                product_id = data['pid']
                quantity = data.get('product_qty', 1)
                
                product = Product.objects.get(id=product_id)
                
                # Check if product is in stock
                if product.quantity < quantity:
                    return JsonResponse({'status': 'Product Stock Not Available'}, status=400)
                
                # Create order
                user_profile = UserProfile.objects.get(user=request.user)
                order_number = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{request.user.id}"
                
                order = Order.objects.create(
                    user=request.user,
                    order_number=order_number,
                    total_amount=product.selling_price * quantity,
                    shipping_address=user_profile.address,
                    phone_number=user_profile.phone_number
                )
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.selling_price
                )
                
                # Reduce product quantity
                product.quantity -= quantity
                product.save()
                
                return JsonResponse({
                    'status': 'Order Created Successfully', 
                    'order_id': order.id,
                    'order_number': order.order_number,
                    'redirect_url': f'/checkout/{order.id}/'
                }, status=200)
                
            except Product.DoesNotExist:
                return JsonResponse({'status': 'Product not found'}, status=404)
            except UserProfile.DoesNotExist:
                return JsonResponse({'status': 'Please complete your profile with address and phone number'}, status=400)
            except Exception as e:
                return JsonResponse({'status': f'Error: {str(e)}'}, status=500)
        else:
            return JsonResponse({'status': 'Login to Purchase'}, status=401)
    else:
        return JsonResponse({'status': 'Invalid Access'}, status=400)

def create_order_from_cart(request):
    if request.user.is_authenticated:
        try:
            cart_items = Cart.objects.filter(user=request.user)
            if not cart_items.exists():
                messages.error(request, "Your cart is empty")
                return redirect('cart')
            
            # Calculate total amount
            total_amount = sum(item.total_cost for item in cart_items)
            
            # Get user profile for address and phone number
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                shipping_address = user_profile.address
                phone_number = user_profile.phone_number
            except UserProfile.DoesNotExist:
                messages.error(request, "Please complete your profile with address and phone number")
                return redirect('cart')
            
            # Create order
            order_number = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{request.user.id}"
            order = Order.objects.create(
                user=request.user,
                order_number=order_number,
                total_amount=total_amount,
                shipping_address=shipping_address,
                phone_number=phone_number
            )
          
            
            # Clear the cart
            cart_items.delete()
            
            # Redirect to checkout page
            return redirect('checkout', order_id=order.id)
            
        except Exception as e:
            messages.error(request, f"Error creating order: {str(e)}")
            return redirect('cart')
    else:
        return redirect('login')

def checkout(request, order_id):
    if request.user.is_authenticated:
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            return render(request, "shop/checkout.html", {"order": order})
        except Order.DoesNotExist:
            messages.error(request, "Order not found")
            return redirect('home')
    else:
        return redirect('login')

def process_payment(request, order_id):
    if request.user.is_authenticated:
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            
            if request.method == 'POST':
                # Update order with form data
                order.shipping_address = request.POST.get('shipping_address')
                phone_number = request.POST.get('phone_number')
                payment_method = request.POST.get('payment_method')
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                email = request.POST.get('email')
                city = request.POST.get('city')
                state = request.POST.get('state')
                coupon_code = request.POST.get('coupon_code')
                
                # Validate phone number
                if not phone_number or len(phone_number) != 10 or not phone_number.isdigit():
                    messages.error(request, "Phone number must be exactly 10 digits")
                    return redirect('checkout', order_id=order.id)
                
                order.phone_number = phone_number
                
                # Store additional information in the order (you might want to add these fields to your Order model)
                # For now, we'll store them in a JSON field or as separate fields if they exist
                # If these fields don't exist in your Order model, you may need to add them
                order.first_name = first_name
                order.last_name = last_name
                order.email = email
                order.city = city
                order.state = state
                order.coupon_code = coupon_code
                
                # Process payment based on selected method
                if payment_method in ['credit_card', 'debit_card']:
                    # Simulate card payment processing
                    order.payment_status = 'paid'
                    order.payment_method = 'Card Payment'
                    order.transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    messages.success(request, "Card payment successful! Your order has been placed.")
                    
                elif payment_method == 'gpay':
                    # Simulate Google Pay payment
                    order.payment_status = 'paid'
                    order.payment_method = 'Google Pay'
                    order.transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    messages.success(request, "Google Pay payment successful! Your order has been placed.")
                    
                elif payment_method == 'phonepay':
                    # Simulate PhonePe payment
                    order.payment_status = 'paid'
                    order.payment_method = 'PhonePe'
                    order.transaction_id = f"PP{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    messages.success(request, "PhonePe payment successful! Your order has been placed.")
                    
                elif payment_method == 'paypal':
                    # Simulate PayPal payment
                    order.payment_status = 'paid'
                    order.payment_method = 'PayPal'
                    order.transaction_id = f"PL{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    messages.success(request, "PayPal payment successful! Your order has been placed.")
                    
                elif payment_method == 'cash_on_delivery':
                    # Cash on delivery
                    order.payment_status = 'pending'
                    order.payment_method = 'Cash on Delivery'
                    messages.success(request, "Order placed successfully! Please have cash ready for delivery.")
                    
                elif payment_method == 'upi':
                    # Simulate UPI payment
                    order.payment_status = 'paid'
                    order.payment_method = 'UPI Payment'
                    order.transaction_id = f"UPI{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    messages.success(request, "UPI payment successful! Your order has been placed.")
                    
                elif payment_method == 'netbanking':
                    # Simulate Net Banking payment
                    order.payment_status = 'paid'
                    order.payment_method = 'Net Banking'
                    order.transaction_id = f"NB{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    messages.success(request, "Net Banking payment successful! Your order has been placed.")
                    
                elif payment_method == 'digital_wallet':
                    # Simulate Digital Wallet payment
                    order.payment_status = 'paid'
                    order.payment_method = 'Digital Wallet'
                    order.transaction_id = f"DW{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    messages.success(request, "Digital Wallet payment successful! Your order has been placed.")
                    
                else:
                    messages.error(request, "Please select a valid payment method.")
                    return redirect('checkout', order_id=order.id)
                
                order.save()
                return redirect('order_confirmation', order_id=order.id)
            
            else:
                # GET request - redirect back to checkout
                return redirect('checkout', order_id=order.id)
                
        except Order.DoesNotExist:
            messages.error(request, "Order not found")
            return redirect('home')
    else:
        return redirect('login')

def order_confirmation(request, order_id):
    if request.user.is_authenticated:
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            return render(request, "shop/order_confirmation.html", {"order": order})
        except Order.DoesNotExist:
            messages.error(request, "Order not found")
            return redirect('home')
    else:
        return redirect('login')


def feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            # Here you can process the feedback data
            # For now, we'll just show a success message
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            
            # You can save this to a database, send email, etc.
            # For demonstration, we'll just show a success message
            messages.success(request, "successfully submit your feedback")
            return redirect('feedback')
    else:
        form = FeedbackForm()
    
    return render(request, "shop/feedback.html", {"form": form})

def about(request):
    """Render the About Us page"""
    return render(request, "shop/about.html")

def update_profile(request):
    """Update user profile information"""
    if request.method == 'POST':
        if request.user.is_authenticated:
            user_profile = UserProfile.objects.get(user=request.user)
            user_profile.phone_number = request.POST.get('phone_number')
            user_profile.address = request.POST.get('address')
            user_profile.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('dashboard')
        else:
            messages.error(request, "You need to be logged in to update your profile.")
            return redirect('login')
    return redirect('dashboard')

# The duplicate dashboard function has been removed.

def dashboard(request):
    """User dashboard showing profile information and order history"""
    if not request.user.is_authenticated:
        messages.error(request, "Please login to access your dashboard")
        return redirect('login')
    
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        orders = Order.objects.filter(user=request.user).order_by('-created_at')[:10]  # Last 10 orders
        cart_items = Cart.objects.filter(user=request.user)
        favorites = Favourite.objects.filter(user=request.user)
        
        # Calculate total spent and average order value
        all_orders = Order.objects.filter(user=request.user, payment_status='paid')
        total_spent = sum(order.total_amount for order in all_orders)
        average_order_value = total_spent / len(all_orders) if all_orders else 0
        
        context = {
            'profile': user_profile,
            'orders': orders,
            'cart_items': cart_items,
            'favorites': favorites,
            'order_count': orders.count(),
            'cart_count': cart_items.count(),
            'favorite_count': favorites.count(),
            'total_spent': total_spent,
            'average_order_value': round(average_order_value, 2),
        }
        return render(request, "shop/dashboard.html", context)
        
    except UserProfile.DoesNotExist:
        messages.error(request, "Please complete your profile")
        return redirect('home')
