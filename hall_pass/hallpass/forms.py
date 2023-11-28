from django import forms
from .models import TenantUser

class TenantUserForm(forms.ModelForm):
    class Meta:
        model = TenantUser
        fields = ['first_name', 'last_name', 'username', 'email', 'password']  # Add other fields as needed

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # You can customize the form widget attributes or add additional fields here if needed
        self.fields['password'].widget = forms.PasswordInput()

    def clean_email(self):
        # You can add custom email validation logic here if needed
        email = self.cleaned_data.get('email')
        if email and TenantUser.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email
