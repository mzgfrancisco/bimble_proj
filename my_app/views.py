import os
import json
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Profile, GalleryImage
from django.contrib.auth.hashers import make_password
from datetime import date, datetime
from django.urls import reverse
from .models import Profile, GalleryImage, Message
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
# from templatetags import custom_tags
# Create your views here.

@login_required(login_url='login')
def home(request):
    search_query = request.GET.get('search', '')
    profiles = Profile.objects.all()
    profile = profiles.first()  
    gallery_images = GalleryImage.objects.all()
    
    gallery_images = GalleryImage.objects.all()
    images = [image.image.url for image in gallery_images]

    if search_query:
        profiles = profiles.filter(location__icontains=search_query) | profiles.filter(breed__icontains=search_query)
    
    locations = profiles.values_list('location', flat=True).distinct()
    breeds = profiles.values_list('breed', flat=True).distinct()
    
    if profile:
        birth_date = profile.birthday
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    else:
        birth_date = None
        age = None

    context = {
        'profiles': profiles,
        'birthday': birth_date,
        'age': age,
        'locations': list(locations),
        'breeds': list(breeds),
        'images': images,
        'dummy' : False,
    }
    return render(request, 'home.html', context)

def forgotpass(request):
    if request.user.is_authenticated:
        return redirect('home') 
    return render(request, "forgot_password.html")

@login_required(login_url='login')
def createprofile(request):
    if request.method == "POST":
        user = request.user 
        profile_picture = request.FILES["pet_picture"]
        name = request.POST["petname"]
        original_name, original_ext = os.path.splitext(profile_picture.name)
        new_name = f"{name}{original_ext}"
        profile_picture.name = new_name
        breed = request.POST["petbreed"]
        gender = request.POST["petgender"]
        birthday = request.POST["petbirthday"]
        location = request.POST["location"]
        petprofile = Profile(user=user, profile_picture=profile_picture, name=name, gender=gender, breed=breed, birthday=birthday, location=location) 
        petprofile.save()
        return redirect('home')
    else:
        return render(request, "createform.html")

@login_required(login_url='login')
def viewprofile(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    profile = get_object_or_404(Profile, user=user)
    gallery_images = profile.gallery_images.all()   
    # Calculate age
    today = date.today()
    birth_date = profile.birthday
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    # For Gallery Images
    if request.method == 'POST':
        images = request.FILES.getlist('images')
        if gallery_images.count() + len(images) > 8:
            messages.error(request, "You can only upload up to 8 images.")
            return redirect(reverse('viewprofile', args=[user_id]))
        
        for image in images:
            gallery_image = GalleryImage(profile=profile, image=image)
            gallery_image.save()
        return redirect(reverse('viewprofile', args=[user_id]))
    else:
        form = GalleryImageForm()
    
    return render(request, 'viewprofile.html', {'profile': profile, 'age': age, 'form': form, 'gallery_images': gallery_images})

# Delete Gallery Image
@login_required(login_url='login')
def delete_gallery_image(request, image_id):
    image = get_object_or_404(GalleryImage, id=image_id)
    profile = image.profile

    if request.user != profile.user:
        messages.error(request, "You do not have permission to delete this image.")
        return redirect('viewprofile', user_id=profile.user.id)

    image.delete()
    messages.success(request, "Image deleted successfully.")
    return redirect('viewprofile', user_id=profile.user.id)

@login_required(login_url='login')
def editprofile(request):
    profile = Profile.objects.get(user=request.user)
    
    if request.method == 'POST':
        profile.name = request.POST.get('petname')
        profile.breed = request.POST.get('petbreed')
        profile.gender = request.POST.get('petgender')
        profile.birthday = request.POST.get('petbirthday')
        profile.location = request.POST.get('location')
        
        if 'pet-picture' in request.FILES:
            profile.profile_picture = request.FILES['pet-picture']
        
        profile.save()
        return redirect('viewprofile', user_id=request.user.id)
    
    birthday = profile.birthday.strftime('%Y-%m-%d') if profile.birthday else ''
    
    context = {
        'profile': profile,
        'birthday': birthday
    }
    return render(request, 'editprofile.html', context)

# Chat Functions
@login_required(login_url='login')
def chat(request):
    sent_messages = Message.objects.filter(sender=request.user).values_list('receiver_id', flat=True)
    received_messages = Message.objects.filter(receiver=request.user).values_list('sender_id', flat=True)
    user_ids = set(sent_messages).union(set(received_messages))
    users = User.objects.filter(id__in=user_ids)
    
    # Get the latest message for each user
    latest_messages = {}
    for user in users:
        latest_message = Message.objects.filter(
            (Q(sender=request.user) & Q(receiver=user)) | (Q(sender=user) & Q(receiver=request.user))
        ).order_by('-timestamp').first()
        latest_messages[user.id] = latest_message

    # Get profiles for users
    # profiles = {profile.user.id: profile for profile in Profile.objects.filter(user__in=users)}
    profiles = Profile.objects.all()

    return render(request, 'chat.html', {'users': users, 'latest_messages': latest_messages, 'profiles': profiles})

@login_required(login_url='login')
def load_chat(request, user_id):
    if request.method == 'GET':
        user = User.objects.get(id=user_id)
        messages = Message.objects.filter(sender=request.user, receiver=user) | Message.objects.filter(sender=user, receiver=request.user)
        messages = messages.order_by('timestamp')
        chat_data = [{'sender': msg.sender.username, 'content': msg.content, 'timestamp': msg.timestamp} for msg in messages]
        return JsonResponse({'chat': chat_data})
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required(login_url='login')
@csrf_exempt
def send_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            sender = request.user
            receiver_id = data.get('receiver_id')
            content = data.get('content')

            if receiver_id and content:
                try:
                    receiver = User.objects.get(id=receiver_id)
                    message = Message(sender=sender, receiver=receiver, content=content)
                    message.save()
                    return JsonResponse({'status': 'success', 'message': 'Message sent successfully.'})
                except User.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Receiver not found.'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid data.'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

#Fun Login
def login_user(request):
    if request.user.is_authenticated:
        return redirect('home') 
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            # Return an 'invalid login' error message.
            messages.error(request, "Invalid login credentials")
            return redirect("login")
    
    return render(request, "login.html", {})

# Logout
def logout_user(request):
    logout(request)
    return redirect("login")

# User Registration
class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter password'}),
        label="Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}),
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")


def signup(request):
    if request.user.is_authenticated:
        return redirect('home') 
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Create and save the user
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()

            #messages.success(request, "User registered successfully!")
            user = authenticate(request, username=username, password=password)
            login(request, user)
            return redirect("createprofile")
    else:
        form = UserRegistrationForm()
        return render(request, 'signup.html', {'form': form})

# For forgot password
def forgotpass(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        email = request.POST.get("email")

        try:
            # Check if the user exists with the provided email
            user = User.objects.get(email=email)
            # Store user's ID in the session for the reset password step
            request.session['reset_user_id'] = user.id
            return redirect('reset_password')

        except User.DoesNotExist:
            messages.error(request, "No account found with this email.")
            
    return render(request, "forgot_password.html")


def reset_password(request):
    user_id = request.session.get('reset_user_id')

    if not user_id:
        messages.error(request, "Session expired or invalid access.")
        return redirect('forgotpass')

    if request.method == "POST":
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('reset_password')
        else:
            # Update the user's password
            user = User.objects.get(id=user_id)
            user.password = make_password(password)
            user.save()

            # Clear the session
            del request.session['reset_user_id']

            messages.success(request, "Password reset successful. Please log in.")
            return redirect('login')

    return render(request, "password_reset_confirm.html")

# For Uploading Images in Gallery
class GalleryImageForm(forms.ModelForm):
    class Meta:
        model = GalleryImage
        fields = ['image']

