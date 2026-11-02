from datetime import datetime
from django import forms
from django.conf import settings
from django.utils import timezone
from psycopg2.extras import DateTimeTZRange

from .models import Booking, FacilitySlot


class BookingForm(forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text="Select reservation date"
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        help_text="Start time (e.g. 09:00)"
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        help_text="End time (e.g. 11:00)"
    )
    purpose = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Describe your research experiment or activity'}),
        help_text="Provide a clear description of the project or experiment"
    )

    def __init__(self, *args, facility=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.facility = facility

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if not (date and start_time and end_time):
            return cleaned_data

        if end_time <= start_time:
            raise forms.ValidationError("End time must be after start time.")

        start_dt_naive = datetime.combine(date, start_time)
        end_dt_naive = datetime.combine(date, end_time)

        duration_hours = (end_dt_naive - start_dt_naive).total_seconds() / 3600.0
        if duration_hours > 8.0:
            raise forms.ValidationError("A single booking can be at most 8 hours.")

        start_dt = timezone.make_aware(start_dt_naive)
        end_dt = timezone.make_aware(end_dt_naive)

        if start_dt < timezone.now():
            raise forms.ValidationError("You can't book a time in the past.")

        if self.facility:
            weekday = date.weekday()
            slots = list(self.facility.slots.filter(weekday=weekday).order_by('opens'))
            fits_in_slot = any(slot.opens <= start_time and slot.closes >= end_time for slot in slots)
            if not fits_in_slot:
                if slots:
                    hours_str = ", ".join(f"{s.opens.strftime('%H:%M')}–{s.closes.strftime('%H:%M')}" for s in slots)
                else:
                    hours_str = "Closed all day"
                raise forms.ValidationError(f"The facility is closed at that time. Open hours: {hours_str}")

        cleaned_data['during'] = DateTimeTZRange(start_dt, end_dt, bounds='[)')
        return cleaned_data
