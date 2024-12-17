from django.urls import path
from weightapp import views
from django.contrib.auth import views as auth_views
from weightapp.views import BaseScoopView, BaseScoopViewById, CreateBaseScoop, BaseStoneTypeList, LoginApiView, SignUpApiView
from rest_framework_simplejwt.views import(
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
) 

urlpatterns = [
    path('',views.index,name="home"),
    path('login/', views.loginPage,name="login"),
    path('logout/', views.logoutUser,name="logout"),
    path('login/api/', views.LoginApiView.as_view(), name="login_api"),
    path('signup/api/', views.SignUpApiView.as_view(), name="signup_api"),

    path('jwt/create/', TokenObtainPairView.as_view(), name="jwt_create"),
    path('jwt/refresh/', TokenRefreshView.as_view(), name="token_refresh"),
    path('jwt/verify/', TokenVerifyView.as_view(), name="token_verify"),

    path('weight/table', views.weightTable,name="weightTable"),
    path('weight/edit/<int:mode>/<int:weight_id>', views.editWeight,name="editWeight"),
    path('autocompalteCustomer/',views.autocompalteCustomer,name="autocompalteCustomer"),
    path('autocompalteSite/',views.autocompalteSite,name="autocompalteSite"),
    path('weight/approve', views.approveWeight,name="approveWeight"),

    path('production/view', views.viewProduction,name="viewProduction"),
    path('production/create', views.createProduction,name="createProduction"),
    path('production/edit/<int:pd_id>',views.editProduction,name="editProduction"),
    path('production/remove/<int:pd_id>',views.removeProduction,name="removeProduction"),
    path('production/summary', views.summaryProduction,name="summaryProduction"),
    path('production/monthly', views.monthlyProduction,name="monthlyProduction"),

    path('stoneEstimate/view', views.viewStoneEstimate,name="viewStoneEstimate"),
    path('stoneEstimate/create', views.createStoneEstimate,name="createStoneEstimate"),
    path('stoneEstimate/edit/<int:se_id>', views.editStoneEstimate,name="editStoneEstimate"),
    path('stoneEstimate/remove/<int:se_id>', views.removeStoneEstimate,name="removeStoneEstimate"),

    path('stock/view', views.viewStock, name="viewStock"),
    path('stock/create', views.createStock, name="createStock"),
    path('stock/step2/edit/<int:stock_id>', views.editStep2Stock, name="editStep2Stock"),
    path('stock/remove/<int:stock_id>', views.removeStock, name="removeStock"),
    path('stockStone/remove/<int:ssn_id>', views.removeStockStone, name="removeStockStone"),
    path('stockStoneItem/edit/<int:stock_id>/<int:ssn_id>', views.editStockStoneItem, name="editStockStoneItem"),
    path('searchStockInDay', views.searchStockInDay, name="searchStockInDay"),
    path('searchDataWeightToStock', views.searchDataWeightToStock, name="searchDataWeightToStock"),

    path('exportExcelProductionByStone/', views.exportExcelProductionByStone,name="exportExcelProductionByStone"),
    path('exportExcelProductionByStone/dashboard', views.exportExcelProductionByStoneInDashboard,name="exportExcelProductionByStoneInDashboard"),

    path('exportExcelProductionByStoneAndMonth/', views.exportExcelProductionByStoneAndMonth,name="exportExcelProductionByStoneAndMonth"),
    path('exportExcelProductionByStoneAndMonthInDashboard/', views.exportExcelProductionByStoneAndMonthInDashboard,name="exportExcelProductionByStoneAndMonthInDashboard"),

    path('exportExcelProductionAndLoss/', views.exportExcelProductionAndLoss,name="exportExcelProductionAndLoss"),
    path('exportExcelProductionAndLoss/dashboard', views.exportExcelProductionAndLossDashboard,name="exportExcelProductionAndLossDashboard"),
    
    path('searchProductionGoal', views.searchProductionGoal, name="searchProductionGoal"),
    path('searchStoneEstimate', views.searchStoneEstimate, name="searchStoneEstimate"),
    path('searchNumCalQ', views.searchNumCalQ, name="searchNumCalQ"),
    path('searchDataCustomer/',views.searchDataCustomer,name="searchDataCustomer"),
    path('setDataCustomer/',views.setDataCustomer,name="setDataCustomer"),
    path('setDataSite/',views.setDataSite,name="setDataSite"),
    path('setDataCarryType/',views.setDataCarryType,name="setDataCarryType"),
    path('searchTeamFromCar/',views.searchTeamFromCar,name="searchTeamFromCar"),
    path('searchDataBaesCustomer/',views.searchDataBaesCustomer,name="searchDataBaesCustomer"),
    path('searchDetailMcType', views.searchDetailMcType, name="searchDetailMcType"),

    path('baseMill/setting',views.settingBaseMill,name="settingBaseMill"),
    path('baseMill/create',views.createBaseMill,name="createBaseMill"),
    path('baseMill/edit/<str:id>',views.editBaseMill,name="editBaseMill"),

    path('baseJobType/setting',views.settingBaseJobType,name="settingBaseJobType"),
    path('baseJobType/create',views.createBaseJobType,name="createBaseJobType"),
    path('baseJobType/edit/<str:id>',views.editBaseJobType,name="editBaseJobType"),

    path('baseStoneType/setting',views.settingBaseStoneType,name="settingBaseStoneType"),
    path('baseStoneType/create',views.createBaseStoneType,name="createBaseStoneType"),
    path('baseStoneType/edit/<str:id>',views.editBaseStoneType,name="editBaseStoneType"),

    path('baseScoop/setting',views.settingBaseScoop,name="settingBaseScoop"),
    path('baseScoop/create',views.createBaseScoop,name="createBaseScoop"),
    path('baseScoop/edit/<str:id>',views.editBaseScoop,name="editBaseScoop"),

    path('baseCarTeam/setting',views.settingBaseCarTeam,name="settingBaseCarTeam"),
    path('baseCarTeam/create',views.createBaseCarTeam,name="createBaseCarTeam"),
    path('baseCarTeam/edit/<str:id>',views.editBaseCarTeam,name="editBaseCarTeam"),

    path('baseCar/setting',views.settingBaseCar,name="settingBaseCar"),
    path('baseCar/create',views.createBaseCar,name="createBaseCar"),
    path('baseCar/edit/<str:id>',views.editBaseCar,name="editBaseCar"),
    path('createCarId/',views.createCarId,name="createCarId"),

    path('baseSite/setting',views.settingBaseSite,name="settingBaseSite"),
    path('baseSite/create',views.createBaseSite,name="createBaseSite"),
    path('baseSite/edit/<str:id>',views.editBaseSite,name="editBaseSite"),

    path('baseCustomer/setting',views.settingBaseCustomer,name="settingBaseCustomer"),
    path('baseCustomer/create',views.createBaseCustomer,name="createBaseCustomer"),
    path('baseCustomer/edit/<str:id>',views.editBaseCustomer,name="editBaseCustomer"),
    path('createCustomerId/',views.createCustomerId,name="createCustomerId"),

    path('baseCustomerSite/setting',views.settingBaseCustomerSite,name="settingBaseCustomerSite"),
    path('baseCustomerSite/create',views.createBaseCustomerSite,name="createBaseCustomerSite"),
    path('baseCustomerSite/edit/<str:id>',views.editBaseCustomerSite,name="editBaseCustomerSite"),

    path('baseDriver/setting',views.settingBaseDriver,name="settingBaseDriver"),
    path('baseDriver/create',views.createBaseDriver,name="createBaseDriver"),
    path('baseDriver/edit/<str:id>',views.editBaseDriver,name="editBaseDriver"),

    path('baseCarRegistration/setting',views.settingBaseCarRegistration,name="settingBaseCarRegistration"),
    path('baseCarRegistration/create',views.createBaseCarRegistration,name="createBaseCarRegistration"),
    path('baseCarRegistration/edit/<str:id>',views.editBaseCarRegistration,name="editBaseCarRegistration"),

    path('exportExcelStoneEstimateAndProduction/', views.exportExcelStoneEstimateAndProduction,name="exportExcelStoneEstimateAndProduction"),
    path('exportExcelStoneEstimateAndProduction/dashboard', views.exportExcelStoneEstimateAndProductionDashboard,name="exportExcelStoneEstimateAndProductionDashboard"),
    path('exportWeightToExpress/', views.exportWeightToExpress,name="exportWeightToExpress"),

    path('reset_password/', auth_views.PasswordResetView.as_view(template_name = "account/forgotPassword.html"),
          name="reset_password"),

    path('reset_password_send/', auth_views.PasswordResetDoneView.as_view(template_name = "account/resetPasswordSend.html"),
          name="password_reset_done"),
    path('reset/<uidb64>/<token>', auth_views.PasswordResetConfirmView.as_view(template_name = "account/passwordResetConfirm.html"), name="password_reset_confirm"),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name = "account/passwordResetComplete.html"), name="password_reset_complete"),

    path('baseScoop/api/list/',BaseScoopView.as_view()),
    path('baseScoop/api/<str:pk>/',BaseScoopViewById.as_view()),
    path('baseScoop/api/create/', CreateBaseScoop.as_view(), name="createBaesScoop"),
    path('baseScoop/api/detail/<str:pk>/',views.baseScoopDetail,name="baseScoopDetail"),
    path('baseScoop/api/vStamp/<str:dt>/',views.baseScoopVStamp,name="baseScoopVStamp"),

     path('baseMill/api/',views.apiBaseMillOverview,name="apiBaseMillOverview"),
     path('baseMill/api/list/',views.baseMillList,name="baseMillList"),
     path('baseMill/api/detail/<str:pk>/',views.baseMillDetail,name="baseMillDetail"),
     path('baseMill/api/create/',views.baseMillCreate,name="baseMillCreate"),
     path('baseMill/api/update/<str:pk>/',views.baseMillUpdate,name="baseMillUpdate"),
     path('baseMill/api/delete/<str:pk>/',views.baseMillDelete,name="baseMillDelete"),
     path('baseMill/api/vStamp/<str:dt>/',views.baseMillVStamp,name="baseMillVStamp"),

     path('weight/api/',views.apiWeightOverview,name="apiWeightOverview"),
     path('weight/api/list/',views.weightList,name="weightList"),
     path('weight/api/detail/<str:pk>/',views.weightDetail,name="weightDetail"),
     path('weight/api/create/',views.weightCreate,name="weightCreate"),
     path('weight/api/update/<str:pk>/',views.weightUpdate,name="weightUpdate"),
     path('weight/api/detail/date/<str:str_date>/<str:str_lc>/',views.weightDetailByDate,name="weightDetailByDate"),
     path('weight/api/vStamp/<str:dt>/<str:str_lc>/',views.weightVStamp,name="weightVStamp"),
     path('weight/api/all/vStamp/<str:dt>/',views.weightVStampAll,name="weightVStampAll"),
     path('weight/api/between/<str:start_date>/<str:end_date>/<int:weight_type>/',views.weightDetailBetween,name="weightDetailBetween"),
     path('weight/api/between/bws/<str:start_date>/<str:end_date>/<str:bws>/',views.weightDetailBetweenByBWS,name="weightDetailBetweenByBWS"),

     path('baseCustomer/api/',views.apiBaseCustomerOverview,name="apiBaseCustomerOverview"),
     path('baseCustomer/api/list/',views.baseCustomerList,name="baseCustomerList"),
     path('baseCustomer/api/detail/<str:pk>/',views.baseCustomerDetail,name="baseCustomerDetail"),
     path('baseCustomer/api/create/',views.baseCustomerCreate,name="baseCustomerCreate"),
     path('baseCustomer/api/update/<str:pk>/',views.baseCustomerUpdate,name="baseCustomerUpdate"),
     path('baseCustomer/api/vStamp/<str:dt>/',views.baseCustomerVStamp,name="baseCustomerVStamp"),

     path('baseStoneType/api/',views.apiBaseStoneTypeOverview,name="apiBaseStoneTypeOverview"),
     path('baseStoneType/api/list/',views.baseStoneTypeList,name="baseStoneTypeList"),
     path('baseStoneType/api/detail/<str:pk>/',views.baseStoneTypeDetail,name="baseStoneTypeDetail"),
     path('baseStoneType/api/create/',views.baseStoneTypeCreate,name="baseStoneTypeCreate"),
     path('baseStoneType/api/update/<str:pk>/',views.baseStoneTypeUpdate,name="baseStoneTypeUpdate"),
     path('baseStoneType/api/test/', BaseStoneTypeList.as_view(), name="baseStoneTypeList"),
     path('baseStoneType/api/vStamp/<str:dt>/',views.baseStoneTypeVStamp,name="baseStoneTypeVStamp"),

     path('baseCarTeam/api/',views.apiBaseCarTeamOverview,name="apiBaseCarTeamOverview"),
     path('baseCarTeam/api/list/',views.baseCarTeamList,name="baseCarTeamList"),
     path('baseCarTeam/api/detail/<str:pk>/',views.baseCarTeamDetail,name="baseCarTeamDetail"),
     path('baseCarTeam/api/create/',views.baseCarTeamCreate,name="baseCarTeamCreate"),
     path('baseCarTeam/api/update/<str:pk>/',views.baseCarTeamUpdate,name="baseCarTeamUpdate"),
     path('baseCarTeam/api/vStamp/<str:dt>/',views.baseCarTeamVStamp,name="baseCarTeamVStamp"),

     path('baseDriver/api/',views.apiBaseDriverOverview,name="apiBaseDriverOverview"),
     path('baseDriver/api/list/',views.baseDriverList,name="baseDriverList"),
     path('baseDriver/api/detail/<str:pk>/',views.baseDriverDetail,name="baseDriverDetail"),
     path('baseDriver/api/create/',views.baseDriverCreate,name="baseDriverCreate"),
     path('baseDriver/api/update/<str:pk>/',views.baseDriverUpdate,name="baseDriverUpdate"),
     path('baseDriver/api/vStamp/<str:dt>/',views.baseDriverVStamp,name="baseDriverVStamp"),

     path('baseCarRegistration/api/',views.apiBaseCarRegistrationOverview,name="apiBaseCarRegistrationOverview"),
     path('baseCarRegistration/api/list/',views.baseCarRegistrationList,name="baseCarRegistrationList"),
     path('baseCarRegistration/api/detail/<str:pk>/',views.baseCarRegistrationDetail,name="baseCarRegistrationDetail"),
     path('baseCarRegistration/api/create/',views.baseCarRegistrationCreate,name="baseCarRegistrationCreate"),
     path('baseCarRegistration/api/update/<str:pk>/',views.baseCarRegistrationUpdate,name="baseCarRegistrationUpdate"),
     path('baseCarRegistration/api/vStamp/<str:dt>/',views.baseCarRegistrationVStamp,name="baseCarRegistrationVStamp"),

     path('baseSite/api/',views.apiBaseSiteOverview,name="apiBaseSiteOverview"),
     path('baseSite/api/list/',views.baseSiteList,name="baseSiteList"),
     path('baseSite/api/detail/<str:pk>/',views.baseSiteDetail,name="baseSiteDetail"),
     path('baseSite/api/create/',views.baseSiteCreate,name="baseSiteCreate"),
     path('baseSite/api/update/<str:pk>/',views.baseSiteUpdate,name="baseSiteUpdate"),
     path('baseSite/api/vStamp/<str:dt>/',views.baseSiteVStamp,name="baseSiteVStamp"),

     path('baseCar/api/',views.apiBaseCarOverview,name="apiBaseCarOverview"),
     path('baseCar/api/list/',views.baseCarList,name="baseCarList"),
     path('baseCar/api/detail/<str:pk>/',views.baseCarDetail,name="baseCarDetail"),
     path('baseCar/api/create/',views.baseCarCreate,name="baseCarCreate"),
     path('baseCar/api/update/<str:pk>/',views.baseCarUpdate,name="baseCarUpdate"),
     path('baseCar/api/vStamp/<str:dt>/',views.baseCarVStamp,name="baseCarVStamp"),

     path('baseJobType/api/',views.apiBaseJobTypeOverview,name="apiBaseJobTypeOverview"),
     path('baseJobType/api/list/',views.baseJobTypeList,name="baseJobTypeList"),
     path('baseJobType/api/detail/<str:pk>/',views.baseJobTypeDetail,name="baseJobTypeDetail"),
     path('baseJobType/api/create/',views.baseJobTypeCreate,name="baseJobTypeCreate"),
     path('baseJobType/api/update/<str:pk>/',views.baseJobTypeUpdate,name="baseJobTypeUpdate"),
     path('baseJobType/api/vStamp/<str:dt>/',views.baseJobTypeVStamp,name="baseJobTypeVStamp"),

     path('baseCustomerSite/api/',views.apiBaseCustomerSiteOverview,name="apiBaseCustomerSiteOverview"),
     path('baseCustomerSite/api/list/',views.baseCustomerSiteList,name="baseCustomerSiteList"),
     path('baseCustomerSite/api/detail/<str:pk>/',views.baseCustomerSiteDetail,name="baseCustomerSiteDetail"),
     path('baseCustomerSite/api/create/',views.baseCustomerSiteCreate,name="baseCustomerSiteCreate"),
     path('baseCustomerSite/api/update/<str:pk>/',views.baseCustomerSiteUpdate,name="baseCustomerSiteUpdate"),
     path('baseCustomerSite/api/vStamp/<str:dt>/',views.baseCustomerSiteVStamp,name="baseCustomerSiteVStamp"),

     path('setSessionCompany', views.setSessionCompany, name="setSessionCompany"),
     path('setDateInDashbord', views.setDateInDashbord, name="setDateInDashbord"),

     #path('callback', views.callback, name='callback'), #line api messaging callback
]