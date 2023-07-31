from django.urls import path
from weightapp import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('',views.index,name="home"),
    path('login/', views.loginPage,name="login"),
    path('logout/', views.logoutUser,name="logout"),

    path('weight/table', views.weightTable,name="weightTable"),
    path('weight/edit/<int:weight_id>', views.editWeight,name="editWeight"),

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

    path('exportExcelStoneEstimateAndProduction/', views.exportExcelStoneEstimateAndProduction,name="exportExcelStoneEstimateAndProduction"),

    path('reset_password/', auth_views.PasswordResetView.as_view(template_name = "account/forgotPassword.html"),
          name="reset_password"),

    path('reset_password_send/', auth_views.PasswordResetDoneView.as_view(template_name = "account/resetPasswordSend.html"),
          name="password_reset_done"),
    path('reset/<uidb64>/<token>', auth_views.PasswordResetConfirmView.as_view(template_name = "account/passwordResetConfirm.html"), name="password_reset_confirm"),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name = "account/passwordResetComplete.html"), name="password_reset_complete"),
]