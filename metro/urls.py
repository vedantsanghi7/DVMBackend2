from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='metro_dashboard'),

    path('wallet/add/', views.wallet_topup_view, name='metro_wallet_add'),

    path('tickets/', views.ticket_list_view, name='metro_ticket_list'),
    path('tickets/buy/', views.ticket_purchase_view, name='metro_ticket_buy'),
    path('tickets/<uuid:ticket_id>/', views.ticket_detail_view, name='metro_ticket_detail'),

    path('scanner/scan/', views.scanner_scan_view, name='metro_scanner_scan'),
    path('scanner/offline-ticket/', views.scanner_offline_ticket_view, name='metro_scanner_offline'),
    path('footfall/', views.footfall_report_view, name='metro_footfall'),
]
