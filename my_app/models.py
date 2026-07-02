from django.db import models
from django.contrib.auth.models import User
import os

# Create your models here.
# User Profile Extension (optional, for extra user data)
class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='Profile_pic/', blank=True, null=True)
    name = models.CharField(max_length=100, default='Unknown')
    gender = models.CharField(max_length=10, default='Unknown')
    breed = models.CharField(max_length=100, default='Unknown')
    birthday = models.DateField(default='2000-01-01')
    location = models.CharField(max_length=200, default='Unknown')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

# Gallery
class GalleryImage(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='gallery_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.profile.user.username} uploaded at {self.uploaded_at}"
    def delete(self, *args, **kwargs):
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)


# Messages
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"
    