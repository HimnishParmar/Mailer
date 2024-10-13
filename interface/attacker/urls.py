from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('campaign/<str:campaign_id>/', views.campaign_page, name='campaign_page'),
    path('create-campaign/', views.create_campaign, name='create_campaign'),
    path('track_link/<str:tracking_id>/<str:link_id>/', views.track_link, name='track_link'),
    path('track_pixel/<str:tracking_id>/', views.track_pixel, name='track_pixel'),
    path('send-email/', views.send_email, name='send_email'),
    path('new-template/', views.new_template, name='create_custom_template'),
    path('update-email-tracking-log/', views.update_email_tracking_log, name='update_email_tracking_log'),
    path('edit-template/<uuid:template_id>/', views.edit_template, name='edit_template'),
    path('save-custom-template/', views.save_custom_template, name='save_custom_template'),
    
    path('1/', views.initialize_template, name='initialize_template'),
    
    path('test/', views.test, name='test'),
    path('edit-default-template/<int:template_id>/', views.edit_default_template, name='edit_default_template'),
    path('download-attachment/<int:campaign_id>/<uuid:tracking_id>/', views.download_attachment, name='download_attachment'),
    path('scrape/', views.scrape_url, name='scrape_url'),
    path('landing/', views.landing_page, name='landing_page'),
]
