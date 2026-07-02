from .models import Profile

def user_profile(request):
    if request.user.is_authenticated:
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            profile = None
        return {'profile': profile}
    return {}

def global_context(request):
    profiles = Profile.objects.all()
    locations = profiles.values_list('location', flat=True).distinct()
    breeds = profiles.values_list('breed', flat=True).distinct()
    return {
        'locations': list(locations),
        'breeds': list(breeds)
    }