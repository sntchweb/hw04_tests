from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post, User
from posts.models import FIRST_FIFTEEN_CHARS_OF_TEXT


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
        test_str = {
            self.group.title: self.group,
            self.post.text[FIRST_FIFTEEN_CHARS_OF_TEXT]: self.post,
        }
        for correct_str, expected_value in test_str.items():
            with self.subTest(correct_str=correct_str):
                self.assertEqual(correct_str, str(expected_value))

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
