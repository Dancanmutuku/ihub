from django import forms
from .models import Order

KENYA_COUNTIES = [
    ('', 'Select County'),
    ('Nairobi', 'Nairobi'), ('Mombasa', 'Mombasa'), ('Kisumu', 'Kisumu'),
    ('Nakuru', 'Nakuru'), ('Kiambu', 'Kiambu'), ('Machakos', 'Machakos'),
    ('Kajiado', 'Kajiado'), ('Uasin Gishu', 'Uasin Gishu'), ('Murang\'a', 'Murang\'a'),
    ('Nyeri', 'Nyeri'), ('Kilifi', 'Kilifi'), ('Kwale', 'Kwale'),
    ('Meru', 'Meru'), ('Embu', 'Embu'), ('Kirinyaga', 'Kirinyaga'),
    ('Nyandarua', 'Nyandarua'), ('Laikipia', 'Laikipia'), ('Samburu', 'Samburu'),
    ('Trans Nzoia', 'Trans Nzoia'), ('West Pokot', 'West Pokot'), ('Elgeyo Marakwet', 'Elgeyo Marakwet'),
    ('Nandi', 'Nandi'), ('Baringo', 'Baringo'), ('Bomet', 'Bomet'),
    ('Kericho', 'Kericho'), ('Narok', 'Narok'), ('Migori', 'Migori'),
    ('Kisii', 'Kisii'), ('Nyamira', 'Nyamira'), ('Homabay', 'Homabay'),
    ('Siaya', 'Siaya'), ('Vihiga', 'Vihiga'), ('Kakamega', 'Kakamega'),
    ('Bungoma', 'Bungoma'), ('Busia', 'Busia'), ('Tana River', 'Tana River'),
    ('Lamu', 'Lamu'), ('Taita Taveta', 'Taita Taveta'), ('Garissa', 'Garissa'),
    ('Wajir', 'Wajir'), ('Mandera', 'Mandera'), ('Marsabit', 'Marsabit'),
    ('Isiolo', 'Isiolo'), ('Tharaka Nithi', 'Tharaka Nithi'), ('Kitui', 'Kitui'),
    ('Makueni', 'Makueni'), ('Nandi', 'Nandi'),
]


class OrderCreateForm(forms.ModelForm):
    county = forms.ChoiceField(choices=KENYA_COUNTIES)

    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'phone',
                  'address', 'city', 'county', 'postal_code', 'notes']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional delivery instructions...'}),
            'phone': forms.TextInput(attrs={'placeholder': '07XXXXXXXX'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            self.fields['email'].initial = user.email
            name_parts = (user.get_full_name() or '').split(' ', 1)
            if name_parts:
                self.fields['first_name'].initial = name_parts[0]
                if len(name_parts) > 1:
                    self.fields['last_name'].initial = name_parts[1]
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
