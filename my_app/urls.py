from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


# from .views import login_view

urlpatterns = [
    path('', views.login_user, name='login'),
    path('home/', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('profile/<int:user_id>', views.viewprofile, name='viewprofile'),
    path('edit/', views.editprofile, name='editprofile'),
    path('messages/', views.chat, name='chat'),
    path('forgot_password/', views.forgotpass, name='forgotpass'),
    path('password_reset_confirm/', views.reset_password, name='reset_password'),
    path('create/', views.createprofile, name='createprofile'),
    path('logout/', views.logout_user, name='logout'),
    path('delete_image/<int:image_id>/', views.delete_gallery_image, name='delete_gallery_image'),
    path('chat/', views.chat, name='chat_view'),
    path('chat/<int:user_id>/', views.load_chat, name='load_chat'),
    path('send_message/', views.send_message, name='send_message'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)