from weightapp.models import UserProfile, BaseVisible, BaseCompany

def _get_user_profile(request):
    #แคชไว้ที่ request กัน query ซ้ำ เพราะ context processor สองตัวนี้ query user เดียวกัน
    if not hasattr(request, '_cached_user_profile'):
        try:
            request._cached_user_profile = UserProfile.objects.get(user_id = request.user.id)
        except UserProfile.DoesNotExist:
            request._cached_user_profile = None
    return request._cached_user_profile

def userVisibleTab(request):
    user_profile = _get_user_profile(request)
    if user_profile is not None:
        visible_tab = BaseVisible.objects.filter(userprofile = user_profile).order_by('step')
    else:
        visible_tab = None

    return dict(visible_tab = visible_tab)


def companyVisibleTab(request):
    user_profile = _get_user_profile(request)
    if user_profile is not None:
        #มี ALL ด้วย company_tab = BaseCompany.objects.filter(userprofile = user_profile).order_by('code')
        company_tab = BaseCompany.objects.filter(userprofile = user_profile).order_by('step')
    else:
        company_tab = None

    return dict(company_tab = company_tab)
