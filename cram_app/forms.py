from django import forms
from .models import TestQuestion

class TestQuestionForm(forms.ModelForm):
    class Meta:
        model = TestQuestion
        fields = ['question_text', 'correct_answer']
        widgets = {
            'question_text': forms.Textarea(attrs={'rows': 2}),
        }

class EditTestQuestionForm(forms.ModelForm):
    wrong1 = forms.CharField(label="", max_length=255, required=False)
    wrong2 = forms.CharField(label="", max_length=255, required=False)
    wrong3 = forms.CharField(label="", max_length=255, required=False)

    class Meta:
        model = TestQuestion
        fields = ['question_text', 'correct_answer']
        widgets = {
            'question_text': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        common_classes = 'form-input-style'

        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': common_classes})

        if self.instance and self.instance.wrong_answers:
            wrongs = self.instance.wrong_answers
            self.fields['wrong1'].initial = wrongs[0] if len(wrongs) > 0 else ''
            self.fields['wrong2'].initial = wrongs[1] if len(wrongs) > 1 else ''
            self.fields['wrong3'].initial = wrongs[2] if len(wrongs) > 2 else ''

    def clean(self):
        cleaned_data = super().clean()
        wrongs = [
            cleaned_data.get('wrong1'),
            cleaned_data.get('wrong2'),
            cleaned_data.get('wrong3'),
        ]
        if not any(wrongs):
            raise forms.ValidationError("Please provide at least one wrong answer.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.wrong_answers = list(filter(None, [
            self.cleaned_data.get('wrong1'),
            self.cleaned_data.get('wrong2'),
            self.cleaned_data.get('wrong3')
        ]))
        if commit:
            instance.save()
        return instance
