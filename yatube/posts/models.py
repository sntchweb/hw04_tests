from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings


User = get_user_model()

FIRST_FIFTEEN_CHARS_OF_TEXT = 15


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    slug = models.SlugField(unique=True, verbose_name='Категория')
    description = models.TextField(verbose_name='Описание')

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Текст записи'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        verbose_name='Группа',
        help_text='Выберите подходящую для записи группу '
                  'или оставьте поле пустым'
    )

    def __str__(self):
        return self.text[FIRST_FIFTEEN_CHARS_OF_TEXT]

    class Meta:
        ordering = ['-pub_date']
