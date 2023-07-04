from django.urls import path
from weightapp import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('',views.index,name="home"),
    path('login/', views.loginPage,name="login"),
    path('logout/', views.logoutUser,name="logout"),
    path('weightTable/', views.weightTable,name="weightTable"),

    path('production/view', views.viewProduction,name="viewProduction"),
    path('production/create', views.createProduction,name="createProduction"),
    path('production/edit/<int:pd_id>',views.editProduction,name="editProduction"),
    path('production/remove/<int:pd_id>',views.removeProduction,name="removeProduction"),

    path('exportExcelProductionByStone/', views.exportExcelProductionByStone,name="exportExcelProductionByStone"),
    path('exportExcelProductionAndLoss/', views.exportExcelProductionAndLoss,name="exportExcelProductionAndLoss"),
    
    path('reset_password/', auth_views.PasswordResetView.as_view(template_name = "account/forgotPassword.html"),
          name="reset_password"),

    path('reset_password_send/', auth_views.PasswordResetDoneView.as_view(template_name = "account/resetPasswordSend.html"),
          name="password_reset_done"),
    path('reset/<uidb64>/<token>', auth_views.PasswordResetConfirmView.as_view(template_name = "account/passwordResetConfirm.html"), name="password_reset_confirm"),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name = "account/passwordResetComplete.html"), name="password_reset_complete"),
]