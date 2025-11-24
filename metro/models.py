from django.db import models
from django.conf import settings
from decimal import Decimal
import uuid

from accounts.models import PassengerProfile


class MetroLine(models.Model):
    name = models.CharField(max_length=100)      
    code = models.CharField(max_length=10, unique=True)  
    is_active = models.BooleanField(default=True)        
    allow_ticket_purchase = models.BooleanField(default=True)  

    def __str__(self):
        return f"{self.name} ({self.code})"


class Station(models.Model):
    code = models.CharField(max_length=10, unique=True)  
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Connection(models.Model):
    """
    Represents an edge between two stations on a specific metro line.
    """
    line = models.ForeignKey(MetroLine, on_delete=models.CASCADE, related_name='connections')
    from_station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='connections_from')
    to_station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='connections_to')

    def __str__(self):
        return f"{self.from_station.code} -> {self.to_station.code} ({self.line.code})"


class WalletTransaction(models.Model):
    """
    Tracks money added or deducted from a passenger's balance.
    """
    passenger = models.ForeignKey(PassengerProfile, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        sign = '+' if self.amount >= 0 else ''
        return f"{self.passenger.user.username} {sign}{self.amount} at {self.created_at}"


class Ticket(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('IN_USE', 'In use'),
        ('USED', 'Used'),
        ('EXPIRED', 'Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lines_used = models.CharField(max_length=200, blank=True, help_text="Comma-separated line names or codes")
    passenger = models.ForeignKey(PassengerProfile, on_delete=models.CASCADE, related_name='tickets')
    source = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='tickets_from')
    destination = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='tickets_to')
    price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)

    path_repr = models.TextField(blank=True, help_text="Stations path as codes, e.g. S1-S2-S3")

    def __str__(self):
        return f"Ticket[{self.id}] {self.source.code} -> {self.destination.code} ({self.status})"


class TicketScan(models.Model):
    DIRECTION_CHOICES = [
        ('ENTRY', 'Entry'),
        ('EXIT', 'Exit'),
    ]

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='scans')
    station = models.ForeignKey(Station, on_delete=models.SET_NULL, null=True, blank=True)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    scanned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    scanned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ticket.id} {self.direction} at {self.station} on {self.scanned_at}"
