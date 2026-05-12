from django import forms
from .models import Comment
from .models import Post
from django.contrib.auth.models import User


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "text", "pub_date", "location", "category", "image"]
        widgets = {
            "pub_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "text": forms.Textarea(attrs={"rows": 5}),
        }
        labels = {
            "title": "Заголовок",
            "text": "Текст",
            "pub_date": "Дата публикации",
            "location": "Местоположение",
            "category": "Категория",
            "image": "Изображение",
        }


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email"]
        labels = {
            "first_name": "Имя",
            "last_name": "Фамилия",
            "username": "Логин",
            "email": "Электронная почта",
        }


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ("text",)
