from django import forms
from .models import Order
from django.core.exceptions import ValidationError
import re

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'phone', 'email', 'county', 'order_note']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'custom-input-field'}),
            'last_name': forms.TextInput(attrs={'class': 'custom-input-field'}),
            'phone': forms.TextInput(attrs={'class': 'custom-input-field'}),
            'email': forms.EmailInput(attrs={'class': 'custom-input-field'}),
            'county': forms.TextInput(attrs={'class': 'custom-input-field'}),
            'order_note': forms.Textarea(attrs={'class': 'custom-input-field', 'rows': 2}),
        }

    def clean_phone(self):
        phone =self.cleaned_data.get('phone')
        # Check if the phone number matches the format '254XXXXXXXXX'
        if not re.fullmatch(r'254\d{9}', phone):
            raise ValidationError("Phone number must be in the format 254XXXXXXXXX.")
        return phone
        
        

