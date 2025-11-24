from django.contrib import admin
from .models import MetroLine, Station, Connection, WalletTransaction, Ticket, TicketScan


class MetroLineAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'allow_ticket_purchase')
    list_filter = ('is_active', 'allow_ticket_purchase')


class StationAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')


class ConnectionAdmin(admin.ModelAdmin):
    list_display = ('line', 'from_station', 'to_station')
    list_filter = ('line',)


class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('passenger', 'amount', 'description', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('passenger__user__username',)


class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'passenger', 'source', 'destination', 'price', 'status', 'lines_used', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'passenger__user__username')


class TicketScanAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'station', 'direction', 'scanned_by', 'scanned_at')
    list_filter = ('direction', 'station', 'scanned_at')


admin.site.register(MetroLine, MetroLineAdmin)
admin.site.register(Station, StationAdmin)
admin.site.register(Connection, ConnectionAdmin)
admin.site.register(WalletTransaction, WalletTransactionAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(TicketScan, TicketScanAdmin)
