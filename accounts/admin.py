from django.contrib import admin
from .models import GuestProfile, Booking, Room

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'capacity', 'price_per_day', 'is_active']
    list_filter = ['type', 'is_active']
    search_fields = ['name', 'description']

admin.site.register(GuestProfile)
admin.site.register(Booking)
