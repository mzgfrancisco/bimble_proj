from django.contrib import admin
from .models import Profile, Message, GalleryImage
# Register your models here.

admin.site.register(Profile)
admin.site.register(GalleryImage)
admin.site.register(Message)