from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from ..models import Group, Post


PROFILE_URL = 'posts:profile'
POST_CREATE_URL = 'posts:post_create'
INDEX_URL = 'posts:index'
POST_ID_URL = 'posts:post_detail'
POST_EDIT_URL = 'posts:post_edit'

User = get_user_model()


class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_forms0')
        cls.post = Post.objects.create(
            text='Test post text',
            author=cls.author,
            group=Group.objects.create(
                title='Test group one',
                slug='test-group-one',
                description='Test group description'
            )
        )
        cls.new_group = Group.objects.create(
            title='Test group two',
            slug='test-group-two',
            description='Test two group description'
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_forms1')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_post_author = Client()
        self.authorized_post_author.force_login(self.post.author)

    def test_create_post_from(self):
        """Валидная форма создает запись."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Test form text',
            'group': self.post.group.id,
        }
        response = self.authorized_client.post(
            reverse(POST_CREATE_URL),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(PROFILE_URL, kwargs={'username': self.user})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
            ).exists()
        )

    def test_author_can_edit_post(self):
        """Автор поста может редактировать текст и менять группу."""
        form_data = {
            'text': 'Changed test form text',
            'group': self.new_group.id
        }
        response_edit = self.authorized_post_author.post(
            reverse(POST_EDIT_URL,
                    kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True,
        )
        post_change = Post.objects.get(id=self.post.pk)
        self.assertEqual(response_edit.status_code, HTTPStatus.OK)
        self.assertEqual(post_change.text, form_data['text'])
        self.assertEqual(post_change.group.id, form_data['group'])
