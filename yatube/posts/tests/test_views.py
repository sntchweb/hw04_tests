from http import HTTPStatus

from django import forms
from django.core.paginator import Page
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, User
from posts.utils import NUMBER_OF_POSTS


INDEX_URL = 'posts:index'
GROUP_URL = 'posts:group_list'
PROFILE_URL = 'posts:profile'
POST_DETAIL_URL = 'posts:post_detail'
POST_CREATE_URL = 'posts:post_create'
POST_EDIT_URL = 'posts:post_edit'

INDEX_TEMPLATE = 'posts/index.html'
GROUP_TEMPLATE = 'posts/group_list.html'
PROFILE_TEMPLATE = 'posts/profile.html'
POST_DETAIL_TEMPLATE = 'posts/post_detail.html'
POST_CREATE_TEMPLATE = 'posts/create_post.html'
POST_EDIT_TEMPLATE = 'posts/create_post.html'


class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_views1')
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='test_post_author'),
            text='Test post text',
            group=Group.objects.create(
                title='Test group title',
                slug='test_group'))
        Post.objects.bulk_create([
            Post(
                text='Test post text',
                author=cls.post.author,
                group=cls.post.group
            ) for i in range(NUMBER_OF_POSTS + 2)
        ])

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_post_author = Client()
        self.authorized_post_author.force_login(self.post.author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий HTML шаблон."""
        templates_pages_names = {
            INDEX_TEMPLATE: reverse(INDEX_URL),
            GROUP_TEMPLATE: (
                reverse(GROUP_URL, kwargs={'slug': self.post.group.slug})
            ),
            PROFILE_TEMPLATE: (
                reverse(PROFILE_URL, kwargs={'username': self.user})
            ),
            POST_DETAIL_TEMPLATE: (
                reverse(POST_DETAIL_URL, kwargs={'post_id': self.post.pk})
            ),
            POST_CREATE_TEMPLATE: reverse(POST_CREATE_URL),
            POST_EDIT_TEMPLATE: (
                reverse(POST_EDIT_URL, kwargs={'post_id': self.post.pk})
            ),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_post_author.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_index_context(self):
        """Шаблон index/ сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(INDEX_URL))
        context_object = response.context['page_obj'][0]
        self.assertEqual(context_object.text, self.post.text)
        self.assertEqual(context_object.group.title, self.post.group.title)
        self.assertEqual(
            context_object.author.username,
            self.post.author.username
        )

    def test_group_list_context(self):
        """Шаблон group_list/ сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(GROUP_URL, kwargs={'slug': self.post.group.slug})
        )
        context_object = response.context['group']
        self.assertEqual(context_object.title, self.post.group.title)
        self.assertEqual(context_object.slug, self.post.group.slug)

    def test_profile_context(self):
        """Шаблон profile/ сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(PROFILE_URL, kwargs={'username': self.post.author})
        )
        context_object = response.context['page_obj'][0]
        context_object_author = response.context['author']
        self.assertEqual(context_object.text, self.post.text)
        self.assertEqual(context_object.group.title, self.post.group.title)
        self.assertEqual(
            context_object.author.username,
            self.post.author.username
        )
        self.assertEqual(
            context_object_author.username,
            self.post.author.username
        )

    def test_post_detail_context(self):
        """Шаблон post_detail/ сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(POST_DETAIL_URL, kwargs={'post_id': self.post.pk})
        )
        context_object = response.context['post']
        self.assertEqual(context_object.text, self.post.text)
        self.assertEqual(context_object.group.title, self.post.group.title)
        self.assertEqual(
            context_object.author.username,
            self.post.author.username
        )

    def test_post_create_context(self):
        """Шаблон post_create/ сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(POST_CREATE_URL))
        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_post_edit_context(self):
        """Шаблон post_edit/ сформирован с правильным контекстом."""
        response = self.authorized_post_author.get(
            reverse(POST_EDIT_URL, kwargs={'post_id': self.post.pk})
        )
        context_object = response.context['is_edit']
        self.assertIsInstance(response.context.get('form'), PostForm)
        self.assertTrue(context_object, True)

    def test_post_added_to_the_right_pages(self):
        """Добавленный пост отображается на страницах index/
        profile/ и group_list/ при указании группы.
        """
        urls_context = {
            reverse(INDEX_URL): ['page_obj'][0],
            reverse(
                GROUP_URL,
                kwargs={'slug': self.post.group.slug}
            ): 'group',
            reverse(
                PROFILE_URL,
                kwargs={'username': self.post.author}
            ): ['page_obj'][0]
        }
        for reverse_url, page_context in urls_context.items():
            with self.subTest(reverse_url=reverse_url):
                response = self.authorized_client.get(reverse_url)
                if page_context != 'group':
                    context_object = response.context[page_context][0]
                    self.assertEqual(context_object.text, self.post.text)
                    self.assertEqual(
                        context_object.group.title,
                        self.post.group.title
                    )
                    self.assertEqual(
                        context_object.author.username,
                        self.post.author.username
                    )
                else:
                    context_object = response.context[page_context]
                    self.assertEqual(
                        context_object.title,
                        self.post.group.title
                    )
                    self.assertEqual(
                        context_object.slug,
                        self.post.group.slug
                    )

    def test_first_page_contains_ten_records(self):
        """Количество постов на первой странице index/, group_list/
        и profile/ равно 10. Страница доступна, у страницы нужный тип
        и != None.
        """
        urls_expected_post_number = [
            reverse(INDEX_URL),
            reverse(GROUP_URL, args=[self.post.group.slug]),
            reverse(PROFILE_URL, args=[self.post.author])
        ]
        for url in urls_expected_post_number:
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            page_obj = response.context.get('page_obj')
            self.assertIsNotNone(page_obj)
            self.assertIsInstance(page_obj, Page)
            self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """Количество постов на второй странице index/, group_list/
        и profile/ равно 3. Страница доступна, у страницы нужный тип
        и != None.
        """
        urls_expected_post_number = [
            reverse(INDEX_URL),
            reverse(GROUP_URL, args=[self.post.group.slug]),
            reverse(PROFILE_URL, args=[self.post.author])
        ]
        for url in urls_expected_post_number:
            response = self.client.get(url + '?page=2')
            self.assertEqual(response.status_code, HTTPStatus.OK)
            page_obj = response.context.get('page_obj')
            self.assertIsNotNone(page_obj)
            self.assertIsInstance(page_obj, Page)
            self.assertEqual(len(response.context['page_obj']), 3)
