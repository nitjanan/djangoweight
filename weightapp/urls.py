from django.urls import path
from weightapp import views
from django.contrib.auth import views as auth_views
from weightapp.views import BaseScoopView, BaseScoopViewById, CreateBaseScoop, BaseStoneTypeList

urlpatterns = [
    path('',views.index,name="home"),
    path('login/', views.loginPage,name="login"),
    path('logout/', views.logoutUser,name="logout"),

    path('weight/table', views.weightTable,name="weightTable"),
    path('weight/edit/<int:mode>/<int:weight_id>', views.editWeight,name="editWeight"),
    path('autocompalteCustomer/',views.autocompalteCustomer,name="autocompalteCustomer"),

    path('production/view', views.viewProduction,name="viewProduction"),
    path('production/create', views.createProduction,name="createProduction"),
    path('production/edit/<int:pd_id>',views.editProduction,name="editProduction"),
    path('production/remove/<int:pd_id>',views.removeProduction,name="removeProduction"),

    path('stoneEstimate/view', views.viewStoneEstimate,name="viewStoneEstimate"),
    path('stoneEstimate/create', views.createStoneEstimate,name="createStoneEstimate"),
    path('stoneEstimate/edit/<int:se_id>', views.editStoneEstimate,name="editStoneEstimate"),
    path('stoneEstimate/remove/<int:se_id>', views.removeStoneEstimate,name="removeStoneEstimate"),

    path('exportExcelProductionByStone/', views.exportExcelProductionByStone,name="exportExcelProductionByStone"),
    path('exportExcelProductionByStone/dashboard', views.exportExcelProductionByStoneInDashboard,name="exportExcelProductionByStoneInDashboard"),

    path('exportExcelProductionAndLoss/', views.exportExcelProductionAndLoss,name="exportExcelProductionAndLoss"),
    path('exportExcelProductionAndLoss/dashboard', views.exportExcelProductionAndLossDashboard,name="exportExcelProductionAndLossDashboard"),
    
    path('searchProductionGoal', views.searchProductionGoal, name="searchProductionGoal"),
    path('searchStoneEstimate', views.searchStoneEstimate, name="searchStoneEstimate"),
    path('searchNumCalQ', views.searchNumCalQ, name="searchNumCalQ"),
    path('searchDataCustomer/',views.searchDataCustomer,name="searchDataCustomer"),
    path('setDataCustomer/',views.setDataCustomer,name="setDataCustomer"),
    path('setDataCarryType/',views.setDataCarryType,name="setDataCarryType"),
    path('searchTeamFromCar/',views.searchTeamFromCar,name="searchTeamFromCar"),
    path('searchDataBaesCustomer/',views.searchDataBaesCustomer,name="searchDataBaesCustomer"),

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

    path('baseSite/setting',views.settingBaseSite,name="settingBaseSite"),
    path('baseSite/create',views.createBaseSite,name="createBaseSite"),
    path('baseSite/edit/<str:id>',views.editBaseSite,name="editBaseSite"),

    path('baseCustomer/setting',views.settingBaseCustomer,name="settingBaseCustomer"),
    path('baseCustomer/create',views.createBaseCustomer,name="createBaseCustomer"),
    path('baseCustomer/edit/<str:id>',views.editBaseCustomer,name="editBaseCustomer"),

    path('baseDriver/setting',views.settingBaseDriver,name="settingBaseDriver"),
    path('baseDriver/create',views.createBaseDriver,name="createBaseDriver"),
    path('baseDriver/edit/<str:id>',views.editBaseDriver,name="editBaseDriver"),

    path('baseCarRegistration/setting',views.settingBaseCarRegistration,name="settingBaseCarRegistration"),
    path('baseCarRegistration/create',views.createBaseCarRegistration,name="createBaseCarRegistration"),
    path('baseCarRegistration/edit/<str:id>',views.editBaseCarRegistration,name="editBaseCarRegistration"),

    path('exportExcelStoneEstimateAndProduction/', views.exportExcelStoneEstimateAndProduction,name="exportExcelStoneEstimateAndProduction"),

    path('reset_password/', auth_views.PasswordResetView.as_view(template_name = "account/forgotPassword.html"),
          name="reset_password"),

    path('reset_password_send/', auth_views.PasswordResetDoneView.as_view(template_name = "account/resetPasswordSend.html"),
          name="password_reset_done"),
    path('reset/<uidb64>/<token>', auth_views.PasswordResetConfirmView.as_view(template_name = "account/passwordResetConfirm.html"), name="password_reset_confirm"),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name = "account/passwordResetComplete.html"), name="password_reset_complete"),

    path('baseScoop/api/list/',BaseScoopView.as_view()),
    path('baseScoop/api/<str:pk>/',BaseScoopViewById.as_view()),
    path('baseScoop/api/create/', CreateBaseScoop.as_view(), name="createBaesScoop"),

     path('baseMill/api/',views.apiBaseMillOverview,name="apiBaseMillOverview"),
     path('baseMill/api/list/',views.baseMillList,name="baseMillList"),
     path('baseMill/api/detail/<str:pk>/',views.baseMillDetail,name="baseMillDetail"),
     path('baseMill/api/create/',views.baseMillCreate,name="baseMillCreate"),
     path('baseMill/api/update/<str:pk>/',views.baseMillUpdate,name="baseMillUpdate"),
     path('baseMill/api/delete/<str:pk>/',views.baseMillDelete,name="baseMillDelete"),

     path('weight/api/',views.apiWeightOverview,name="apiWeightOverview"),
     path('weight/api/list/',views.weightList,name="weightList"),
     path('weight/api/detail/<str:pk>/',views.weightDetail,name="weightDetail"),
     path('weight/api/create/',views.weightCreate,name="weightCreate"),
     path('weight/api/update/<str:pk>/',views.weightUpdate,name="weightUpdate"),

     path('baseCustomer/api/',views.apiBaseCustomerOverview,name="apiBaseCustomerOverview"),
     path('baseCustomer/api/list/',views.baseCustomerList,name="baseCustomerList"),
     path('baseCustomer/api/detail/<str:pk>/',views.baseCustomerDetail,name="baseCustomerDetail"),
     path('baseCustomer/api/create/',views.baseCustomerCreate,name="baseCustomerCreate"),
     path('baseCustomer/api/update/<str:pk>/',views.baseCustomerUpdate,name="baseCustomerUpdate"),

     path('baseStoneType/api/',views.apiBaseStoneTypeOverview,name="apiBaseStoneTypeOverview"),
     path('baseStoneType/api/list/',views.baseStoneTypeList,name="baseStoneTypeList"),
     path('baseStoneType/api/detail/<str:pk>/',views.baseStoneTypeDetail,name="baseStoneTypeDetail"),
     path('baseStoneType/api/create/',views.baseStoneTypeCreate,name="baseStoneTypeCreate"),
     path('baseStoneType/api/update/<str:pk>/',views.baseStoneTypeUpdate,name="baseStoneTypeUpdate"),
     path('baseStoneType/api/test/', BaseStoneTypeList.as_view(), name="baseStoneTypeList"),

     path('baseCarTeam/api/',views.apiBaseCarTeamOverview,name="apiBaseCarTeamOverview"),
     path('baseCarTeam/api/list/',views.baseCarTeamList,name="baseCarTeamList"),
     path('baseCarTeam/api/detail/<str:pk>/',views.baseCarTeamDetail,name="baseCarTeamDetail"),
     path('baseCarTeam/api/create/',views.baseCarTeamCreate,name="baseCarTeamCreate"),
     path('baseCarTeam/api/update/<str:pk>/',views.baseCarTeamUpdate,name="baseCarTeamUpdate"),

     path('baseDriver/api/',views.apiBaseDriverOverview,name="apiBaseDriverOverview"),
     path('baseDriver/api/list/',views.baseDriverList,name="baseDriverList"),
     path('baseDriver/api/detail/<str:pk>/',views.baseDriverDetail,name="baseDriverDetail"),
     path('baseDriver/api/create/',views.baseDriverCreate,name="baseDriverCreate"),
     path('baseDriver/api/update/<str:pk>/',views.baseDriverUpdate,name="baseDriverUpdate"),

     path('baseCarRegistration/api/',views.apiBaseCarRegistrationOverview,name="apiBaseCarRegistrationOverview"),
     path('baseCarRegistration/api/list/',views.baseCarRegistrationList,name="baseCarRegistrationList"),
     path('baseCarRegistration/api/detail/<str:pk>/',views.baseCarRegistrationDetail,name="baseCarRegistrationDetail"),
     path('baseCarRegistration/api/create/',views.baseCarRegistrationCreate,name="baseCarRegistrationCreate"),
     path('baseCarRegistration/api/update/<str:pk>/',views.baseCarRegistrationUpdate,name="baseCarRegistrationUpdate"),

     path('baseSite/api/',views.apiBaseSiteOverview,name="apiBaseSiteOverview"),
     path('baseSite/api/list/',views.baseSiteList,name="baseSiteList"),
     path('baseSite/api/detail/<str:pk>/',views.baseSiteDetail,name="baseSiteDetail"),
     path('baseSite/api/create/',views.baseSiteCreate,name="baseSiteCreate"),
     path('baseSite/api/update/<str:pk>/',views.baseSiteUpdate,name="baseSiteUpdate"),

     path('baseCar/api/',views.apiBaseCarOverview,name="apiBaseCarOverview"),
     path('baseCar/api/list/',views.baseCarList,name="baseCarList"),
     path('baseCar/api/detail/<str:pk>/',views.baseCarDetail,name="baseCarDetail"),
     path('baseCar/api/create/',views.baseCarCreate,name="baseCarCreate"),
     path('baseCar/api/update/<str:pk>/',views.baseCarUpdate,name="baseCarUpdate"),

     path('baseJobType/api/',views.apiBaseJobTypeOverview,name="apiBaseJobTypeOverview"),
     path('baseJobType/api/list/',views.baseJobTypeList,name="baseJobTypeList"),
     path('baseJobType/api/detail/<str:pk>/',views.baseJobTypeDetail,name="baseJobTypeDetail"),
     path('baseJobType/api/create/',views.baseJobTypeCreate,name="baseJobTypeCreate"),
     path('baseJobType/api/update/<str:pk>/',views.baseJobTypeUpdate,name="baseJobTypeUpdate"),
]