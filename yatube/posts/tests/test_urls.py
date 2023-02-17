from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from posts.models import Group, Post, User
from yatube.urls import handler404, handler403


INDEX_URL = 'posts:index'
GROUP_URL = 'posts:group_list'
PROFILE_URL = 'posts:profile'
POST_ID_URL = 'posts:post_detail'
POST_CREATE_URL = 'posts:post_create'
POST_EDIT_URL = 'posts:post_edit'
UNEXISTING_PAGE_URL = '/bad/address/'
CUSTOM_404_PAGE_URL = handler404
CUSTOM_403_PAGE_URL = handler403

INDEX_TEMPLATE = 'posts/index.html'
GROUP_TEMPLATE = 'posts/group_list.html'
PROFILE_TEMPLATE = 'posts/profile.html'
POST_ID_TEMPLATE = 'posts/post_detail.html'
CUSTOM_404_PAGE_TEMPLATE = 'core/404.html'
CUSTOM_403_PAGE_TEMPLATE = 'core/403csrf.html'


class PostURLSTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_urls1')
        cls.author = User.objects.create_user(username='test_urls0')
        cls.post = Post.objects.create(
            text='Test post text',
            author=cls.author,
        )
        cls.group = Group.objects.create(
            title='Test group title',
            slug='test_group',
            description='Test group description'
        )
        cls.url_templates_names = {
            INDEX_URL: (INDEX_TEMPLATE, {}),
            GROUP_URL: (GROUP_TEMPLATE, {'slug': cls.group.slug}),
            PROFILE_URL: (PROFILE_TEMPLATE, {'username': cls.user}),
            POST_ID_URL: (POST_ID_TEMPLATE, {'post_id': cls.post.pk})
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_post_author = Client()
        self.authorized_client_post_author.force_login(self.author)
        cache.clear()

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
        """Страницы по адресу create/ и /<post_id>/edit/ перенаправит анонимного
        пользователя на страницу логина.
        """
        redirect_urls = {
            reverse(POST_CREATE_URL): '/auth/login/?next=/create/',
            reverse(
                POST_EDIT_URL,
                kwargs={'post_id': self.post.pk}
            ): f'/auth/login/?next=/posts/{self.post.pk}/edit/',
        }
        for url, expected_redirect in redirect_urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, expected_redirect)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, params in self.url_templates_names.items():
            template, arguments = params
            response = self.authorized_client.get(
                reverse(address, kwargs=arguments)
            )
            with self.subTest(address=address):
                self.assertTemplateUsed(response, template)

    def test_404_page_uses_custom_template(self):
        """Страница 404 использует кастомный шаблон."""
        response = self.guest_client.get(
            CUSTOM_404_PAGE_URL
        )
        self.assertTemplateUsed(response, CUSTOM_404_PAGE_TEMPLATE)
