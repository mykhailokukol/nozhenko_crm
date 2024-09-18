from django import forms
from django.utils.safestring import mark_safe
from django.contrib.auth.hashers import make_password

from base.models import User, ItemStock, ItemBooking, ItemBookingItemM2M


class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("username", "password")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.password = make_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class ItemStockAdminForm(forms.ModelForm):
    class Meta:
        model = ItemStock
        fields = "__all__"
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field in self.fields:
            if field != "is_approved":
                self.fields[field].widget.attrs["readonly"] = True


class BookingAdminForm(forms.ModelForm):
    class Meta:
        model = ItemBooking
        fields = "__all__"

    class Media:
        js = (
            "//ajax.googleapis.com/ajax/libs/jquery/3.4.1/jquery.min.js",
            "admin/js/item_booking.js",
        )