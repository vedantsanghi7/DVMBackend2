from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.contrib.admin.views.decorators import staff_member_required

from accounts.models import PassengerProfile
from .models import Ticket, WalletTransaction, MetroLine, Station, TicketScan, Connection
from .forms import WalletTopupForm, TicketPurchaseForm
from .services import shortest_path_between_stations, calculate_price_from_path
from django import forms

from django.contrib.auth.models import User

from .forms import WalletTopupForm, TicketPurchaseForm, OfflineTicketForm


def scanner_check(user):
    """
    For now, treat staff users as scanners.
    Later you can refine this with groups/permissions.
    """
    return user.is_active and user.is_staff


class TicketScanForm(forms.Form):
    ticket_id = forms.CharField(label="Ticket ID")
    station = forms.ModelChoiceField(queryset=Station.objects.all())
    direction = forms.ChoiceField(choices=TicketScan.DIRECTION_CHOICES)


@login_required
def dashboard_view(request):
    profile = request.user.profile
    recent_tickets = profile.tickets.order_by('-created_at')[:5]

    context = {
        'balance': profile.balance,
        'recent_tickets': recent_tickets,
    }
    return render(request, 'metro/dashboard.html', context)


@login_required
def wallet_topup_view(request):
    profile = request.user.profile

    if request.method == 'POST':
        form = WalletTopupForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            profile.balance += amount
            profile.save()

            WalletTransaction.objects.create(
                passenger=profile,
                amount=amount,
                description='Wallet top-up'
            )
            return redirect('metro_dashboard')
    else:
        form = WalletTopupForm()

    return render(request, 'metro/wallet_add.html', {'form': form})


@login_required
def ticket_list_view(request):
    profile = request.user.profile
    tickets = profile.tickets.order_by('-created_at')
    return render(request, 'metro/ticket_list.html', {'tickets': tickets})


@login_required
def ticket_detail_view(request, ticket_id):
    profile = request.user.profile
    ticket = get_object_or_404(Ticket, id=ticket_id, passenger=profile)
    return render(request, 'metro/ticket_detail.html', {'ticket': ticket})

@login_required
def ticket_purchase_view(request):
    profile = request.user.profile

    has_active_line = MetroLine.objects.filter(
        is_active=True,
        allow_ticket_purchase=True
    ).exists()

    if not has_active_line:
        return render(request, 'metro/ticket_buy.html', {
            'form': None,
            'error': "No active metro line is available for ticket purchase at the moment."
        })

    if request.method == 'POST':
        form = TicketPurchaseForm(request.POST)
        if form.is_valid():
            source = form.cleaned_data['source']
            destination = form.cleaned_data['destination']

            path_ids = shortest_path_between_stations(source, destination)
            if not path_ids:
                return render(request, 'metro/ticket_buy.html', {
                    'form': form,
                    'error': "No path found between selected stations."
                })

            price = calculate_price_from_path(path_ids)
            if profile.balance < price:
                return render(request, 'metro/ticket_buy.html', {
                    'form': form,
                    'error': (
                        f"Insufficient balance. Ticket costs ₹{price}, "
                        f"your balance is ₹{profile.balance}."
                    )
                })

            path_repr = "-".join(
                Station.objects.get(id=sid).code
                for sid in path_ids
            )

            lines_in_order = []
            if len(path_ids) > 1:
                for i in range(len(path_ids) - 1):
                    from_station = Station.objects.get(id=path_ids[i])
                    to_station = Station.objects.get(id=path_ids[i + 1])

                    conn = Connection.objects.filter(
                        from_station=from_station,
                        to_station=to_station
                    ).select_related('line').first()

                    if not conn:
                        conn = Connection.objects.filter(
                            from_station=to_station,
                            to_station=from_station
                        ).select_related('line').first()

                    if conn and conn.line:
                        line_name = conn.line.name
                        if line_name not in lines_in_order:
                            lines_in_order.append(line_name)

            lines_used_str = ", ".join(lines_in_order)

            profile.balance -= price
            profile.save()

            WalletTransaction.objects.create(
                passenger=profile,
                amount=-price,
                description=f'Ticket purchase {source.code}->{destination.code}'
            )

            ticket = Ticket.objects.create(
                passenger=profile,
                source=source,
                destination=destination,
                price=price,
                path_repr=path_repr,
                lines_used=lines_used_str,
            )

            return redirect('metro_ticket_detail', ticket_id=ticket.id)
    else:
        form = TicketPurchaseForm()

    return render(request, 'metro/ticket_buy.html', {'form': form})


@user_passes_test(scanner_check)
def scanner_scan_view(request):
    message = None

    if request.method == 'POST':
        form = TicketScanForm(request.POST)
        if form.is_valid():
            ticket_id = form.cleaned_data['ticket_id']
            station = form.cleaned_data['station']
            direction = form.cleaned_data['direction']

            ticket = get_object_or_404(Ticket, id=ticket_id)

            if direction == 'ENTRY':
                if ticket.status != 'ACTIVE':
                    message = f"Cannot ENTRY scan. Ticket status is {ticket.status}."
                else:
                    ticket.status = 'IN_USE'
                    ticket.save()
                    TicketScan.objects.create(
                        ticket=ticket,
                        station=station,
                        direction='ENTRY',
                        scanned_by=request.user,
                    )
                    message = "Entry scan successful. Ticket is now IN_USE."
            else:  # EXIT
                if ticket.status != 'IN_USE':
                    message = f"Cannot EXIT scan. Ticket status is {ticket.status}."
                else:
                    ticket.status = 'USED'
                    ticket.save()
                    TicketScan.objects.create(
                        ticket=ticket,
                        station=station,
                        direction='EXIT',
                        scanned_by=request.user,
                    )
                    message = "Exit scan successful. Ticket is now USED."
    else:
        form = TicketScanForm()

    return render(request, 'metro/scanner_scan.html', {'form': form, 'message': message})

@user_passes_test(scanner_check)
def scanner_offline_ticket_view(request):
    """
    Scanner creates a ticket for an offline (cash) passenger.
    Ticket is immediately marked as USED.
    """
    message = None
    ticket_obj = None

    if request.method == 'POST':
        form = OfflineTicketForm(request.POST)
        if form.is_valid():
            source = form.cleaned_data['source']
            destination = form.cleaned_data['destination']

            path_ids = shortest_path_between_stations(source, destination)
            if not path_ids:
                message = "No path found between selected stations."
            else:
                price = calculate_price_from_path(path_ids)

                path_repr = "-".join(
                    Station.objects.get(id=sid).code
                    for sid in path_ids
                )

                lines_in_order = []
                if len(path_ids) > 1:
                    for i in range(len(path_ids) - 1):
                        from_station = Station.objects.get(id=path_ids[i])
                        to_station = Station.objects.get(id=path_ids[i + 1])

                        conn = Connection.objects.filter(
                            from_station=from_station,
                            to_station=to_station
                        ).select_related('line').first()

                        if not conn:
                            conn = Connection.objects.filter(
                                from_station=to_station,
                                to_station=from_station
                            ).select_related('line').first()

                        if conn and conn.line:
                            line_name = conn.line.name
                            if line_name not in lines_in_order:
                                lines_in_order.append(line_name)

                lines_used_str = ", ".join(lines_in_order)

                offline_user = User.objects.get(username='offline')
                offline_profile = offline_user.profile

                ticket_obj = Ticket.objects.create(
                    passenger=offline_profile,
                    source=source,
                    destination=destination,
                    price=price,
                    status='USED',
                    path_repr=path_repr,
                    lines_used=lines_used_str,
                )

                message = f"Offline ticket created and marked as USED. Ticket ID: {ticket_obj.id}"
    else:
        form = OfflineTicketForm()

    return render(request, 'metro/scanner_offline_ticket.html', {
        'form': form,
        'message': message,
        'ticket': ticket_obj,
    })


@staff_member_required
def footfall_report_view(request):
    """
    Show daily footfall per station, using TicketScan entries.
    Footfall = number of scans (ENTRY + EXIT) at each station per day.
    """

    scans = (
        TicketScan.objects
        .annotate(day=TruncDate('scanned_at'))
        .values('day', 'station__name')
        .annotate(count=Count('id'))
        .order_by('-day', 'station__name')
    )

    context = {
        'rows': scans,
    }
    return render(request, 'metro/admin_footfall.html', context)

