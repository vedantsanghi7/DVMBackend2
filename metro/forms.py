from django import forms
from .models import Station, MetroLine


class WalletTopupForm(forms.Form):
    amount = forms.DecimalField(max_digits=8, decimal_places=2, min_value=0.01)


class TicketPurchaseForm(forms.Form):
    source = forms.ModelChoiceField(queryset=Station.objects.all())
    destination = forms.ModelChoiceField(queryset=Station.objects.all())

    def clean(self):
        cleaned_data = super().clean()
        src = cleaned_data.get('source')
        dest = cleaned_data.get('destination')

        if src and dest and src == dest:
            raise forms.ValidationError("Source and destination cannot be the same.")

        return cleaned_data


# metro/forms.py
from django import forms
from .models import Station

class OfflineTicketForm(forms.Form):
    source = forms.ModelChoiceField(queryset=Station.objects.all())
    destination = forms.ModelChoiceField(queryset=Station.objects.all())

    def clean(self):
        cleaned_data = super().clean()
        src = cleaned_data.get('source')
        dest = cleaned_data.get('destination')

        if src and dest and src == dest:
            raise forms.ValidationError("Source and destination cannot be the same.")
        return cleaned_data

