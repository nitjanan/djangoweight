from weightapp.models import UserProfile, BaseVisible, BaseCompany

def userVisibleTab(request):
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)
        visible_tab = BaseVisible.objects.filter(userprofile = user_profile)
    except:
        visible_tab = None

    return dict(visible_tab = visible_tab)


def companyVisibleTab(request):
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)
        company_tab = BaseCompany.objects.filter(userprofile = user_profile).order_by('code')
        
    except:
        company_tab = None

    return dict(company_tab = company_tab)