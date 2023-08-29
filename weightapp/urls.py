from django.urls import path
from weightapp import views
from django.contrib.auth import views as auth_views

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
]