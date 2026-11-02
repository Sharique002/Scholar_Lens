from django import forms
from .models import Booking


class BookingForm(forms.ModelForm):
    start_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    end_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))

    class Meta:
        model = Booking
        fields = ['purpose']
