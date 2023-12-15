from weightapp.models import UserProfile, BaseVisible

def userVisibleTab(request):
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)
        visible_tab = BaseVisible.objects.filter(userprofile = user_profile)
    except:
        visible_tab = None

    return dict(visible_tab = visible_tab)