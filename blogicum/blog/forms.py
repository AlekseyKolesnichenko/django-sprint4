from django import forms
from django.contrib.auth import get_user_model

from .models import Post, Comment

User = get_user_model()


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = '__all__'
        widgets = {'pub_date': forms.DateInput(attrs={'type': 'date'})}
        exclude = ('author',)


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
