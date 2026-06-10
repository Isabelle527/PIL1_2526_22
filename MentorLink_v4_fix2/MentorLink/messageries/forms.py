from django import forms
from .models import Message, ContactMessage


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Écris ton message...'
            }),
        }
        labels = {
            'body': 'Message',
        }


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ton nom complet'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ton.email@ifri.com'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sujet de la demande'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Décris ton besoin...'}),
        }
        labels = {
            'name': 'Nom complet',
            'email': 'Email',
            'subject': 'Sujet',
            'message': 'Message',
        }


class SlotSuggestionForm(forms.Form):
    # libre: user can suggest one or multiple slots as text; parsed later
    slots = forms.CharField(widget=forms.Textarea(attrs={'rows':3, 'class':'form-control', 'placeholder':'Ex: Lundi 14h-16h; Mercredi 18h-20h'}), required=True, label='Propositions de créneaux')


class GoalProposalForm(forms.Form):
    goal = forms.CharField(widget=forms.Textarea(attrs={'rows':3, 'class':'form-control', 'placeholder':'Propose un premier objectif (court)'}), required=True, label="Proposer un premier objectif")


class InitiationMiniForm(forms.Form):
    expectations = forms.CharField(widget=forms.Textarea(attrs={'rows':3, 'class':'form-control', 'placeholder':'Ce que j\'attends de cette relation...'}), required=False, label="Ce que j'attends")
