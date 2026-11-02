from django.contrib import admin
from .models import Facility, FacilitySlot, Booking


class FacilitySlotInline(admin.TabularInline):
    model = FacilitySlot
    extra = 1


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ('name', 'kind', 'department', 'location', 'custodian', 'requires_approval', 'is_active')
    list_filter = ('kind', 'department', 'requires_approval', 'is_active')
    search_fields = ('name', 'department', 'location')
    inlines = [FacilitySlotInline]


@admin.register(FacilitySlot)
class FacilitySlotAdmin(admin.ModelAdmin):
    list_display = ('facility', 'weekday', 'opens', 'closes')
    list_filter = ('weekday', 'facility')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'facility', 'user', 'start', 'end', 'status', 'created_at')
    list_filter = ('status', 'facility')
    search_fields = ('purpose', 'user__username', 'facility__name')
