from django import forms
from .models import CareGroup


class LoginForm(forms.Form):
    group_name = forms.ChoiceField(choices=[])
    pin = forms.CharField(widget=forms.PasswordInput, max_length=20)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [('', '— Select your group —')] + [
            (g.name, g.name) for g in CareGroup.objects.order_by('name')
        ]
        self.fields['group_name'].choices = choices


class VisitorForm(forms.Form):
    name = forms.CharField(max_length=100, label='Visitor name')
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
        label='Note (optional)',
    )
