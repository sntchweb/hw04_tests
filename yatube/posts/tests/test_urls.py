from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Post, Group


User = get_user_model()

INDEX_URL = 'posts:index'
GROUP_URL = 'posts:group_list'
PROFILE_URL = 'posts:profile'
POST_ID_URL = 'posts:post_detail'
POST_CREATE_URL = 'posts:post_create'
POST_EDIT_URL = 'posts:post_edit'
UNEXISTING_PAGE_URL = '/bad/address/'

INDEX_TEMPLATE = 'posts/index.html'
GROUP_TEMPLATE = 'posts/group_list.html'
PROFILE_TEMPLATE = 'posts/profile.html'
POST_ID_TEMPLATE = 'posts/post_detail.html'


class PostURLSTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_urls0')
        cls.post = Post.objects.create(
            text='Test post text',
            author=cls.author,
        )
        cls.group = Group.objects.create(
            title = 'Test group title',
            slug='test_group',
            description='Test group description'
        )


    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_urls1')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_post_author = Client()
        self.authorized_client_post_author.force_login(self.author)


    def test_urls_for_unauthorized_user(self):
        """Страницы index, group/<slug>/, profile/<username>/ и
        posts/<post_id>/ доступны любому пользователю.
        """
        pages = {
            reverse(INDEX_URL): HTTPStatus.OK,
            reverse(GROUP_URL, args=[self.group.slug]): HTTPStatus.OK,
            reverse(PROFILE_URL, args=[self.user]): HTTPStatus.OK,
            reverse(POST_ID_URL, args=[self.post.pk]): HTTPStatus.OK,
            UNEXISTING_PAGE_URL: HTTPStatus.NOT_FOUND,
        }
        for field, expected_value in pages.items():
            response = self.guest_client.get(field)
            with self.subTest(field=field):
                self.assertEqual(response.status_code, expected_value)


    def test_post_edit_available_to_author(self):
        """Страница posts/<post_id>/edit/ доступна автору поста."""
        response = self.authorized_client_post_author.get(
            reverse(POST_EDIT_URL, kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)


    def test_create_post_authorized_user(self):
        """Страница create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get(reverse(POST_CREATE_URL))
        self.assertEqual(response.status_code, HTTPStatus.OK)


    def test_create_url_redirect_anonymous_on_login(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get(
            reverse(POST_CREATE_URL), follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')


    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_templates_names = {
            INDEX_URL: (INDEX_TEMPLATE, {}),
            GROUP_URL: (GROUP_TEMPLATE, {'slug': self.group.slug}),
            PROFILE_URL: (PROFILE_TEMPLATE, {'username': self.user}),
            POST_ID_URL: (POST_ID_TEMPLATE, {'post_id': self.post.pk})
        }
        for address, params in url_templates_names.items():
            template, arguments = params
            response = self.authorized_client.get(
                reverse(address, kwargs=arguments)
            )
            with self.subTest(address=address):
                self.assertTemplateUsed(response, template)
