from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_username')
        cls.group = Group.objects.create(
            title='Test group title',
            slug='test_group',
            description='Test group description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test first fifteen chars of text',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        expected_group_name = self.group.title
        expected_text = self.post.text[:settings.FIRST_FIFTEEN_CHARS_OF_TEXT]
        self.assertEqual(expected_group_name, str(self.group))
        self.assertEqual(expected_text, str(self.post))

    def test_verbose_name(self):
        """Проверяем, что verbose_name модели Post совпадает с ожидаемым."""
        field_labels = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_labels.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_help_text(self):
        """help_text в полях text и group совпадает с ожидаемым."""
        field_help_texts = {
            'text': 'Текст записи',
            'group': ('Выберите подходящую для записи группу '
                      'или оставьте поле пустым'),
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text,
                    expected_value
                )
