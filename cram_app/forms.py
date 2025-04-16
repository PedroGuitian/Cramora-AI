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
    wrong1 = forms.CharField(label="Wrong Answer 1", max_length=255, required=True)
    wrong2 = forms.CharField(label="Wrong Answer 2", max_length=255, required=True)
    wrong3 = forms.CharField(label="Wrong Answer 3", max_length=255, required=True)

    class Meta:
        model = TestQuestion
        fields = ['question_text', 'correct_answer']
        widgets = {
            'question_text': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        # Load wrong answers into separate fields if instance exists
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.wrong_answers:
            wrongs = self.instance.wrong_answers
            self.fields['wrong1'].initial = wrongs[0] if len(wrongs) > 0 else ''
            self.fields['wrong2'].initial = wrongs[1] if len(wrongs) > 1 else ''
            self.fields['wrong3'].initial = wrongs[2] if len(wrongs) > 2 else ''

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.wrong_answers = [
            self.cleaned_data['wrong1'],
            self.cleaned_data['wrong2'],
            self.cleaned_data['wrong3'],
        ]
        if commit:
            instance.save()
        return instance