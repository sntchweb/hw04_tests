from http import HTTPStatus

from django.core.paginator import Page
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from django import forms

from posts.forms import CommentForm, PostForm
from posts.models import Group, Post, User
from posts.utils import NUMBER_OF_POSTS


INDEX_URL = 'posts:index'
GROUP_URL = 'posts:group_list'
PROFILE_URL = 'posts:profile'
POST_DETAIL_URL = 'posts:post_detail'
POST_CREATE_URL = 'posts:post_create'
POST_EDIT_URL = 'posts:post_edit'
FOLLOW_URL = 'posts:profile_follow'
UNFOLLOW_URL = 'posts:profile_unfollow'
FOLLOW_INDEX_URL = 'posts:follow_index'

INDEX_TEMPLATE = 'posts/index.html'
GROUP_TEMPLATE = 'posts/group_list.html'
PROFILE_TEMPLATE = 'posts/profile.html'
POST_DETAIL_TEMPLATE = 'posts/post_detail.html'
POST_CREATE_TEMPLATE = 'posts/create_post.html'
POST_EDIT_TEMPLATE = 'posts/create_post.html'
FOLLOW_INDEX_TEMPLATE = 'posts/follow.html'


class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ufollowing_user = User.objects.create_user(username='unfollowing')
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
        self.unfollowing_user = Client()
        self.unfollowing_user.force_login(self.ufollowing_user)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_post_author = Client()
        self.authorized_post_author.force_login(self.post.author)
        cache.clear()

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
        self.assertIsNotNone(context_object.image)
        self.assertEqual(
            context_object.author.username,
            self.post.author.username
        )

    def test_group_list_context(self):
        """Шаблон group_list/ сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(GROUP_URL, kwargs={'slug': self.post.group.slug})
        )
        context_object = response.context['page_obj'][0]
        context_object_group = response.context['group']
        self.assertEqual(context_object.text, self.post.text)
        self.assertEqual(context_object.group.title, self.post.group.title)
        self.assertEqual(context_object_group.title, self.post.group.title)
        self.assertEqual(context_object_group.slug, self.post.group.slug)
        self.assertIsNotNone(context_object.image)

    def test_profile_context(self):
        """Шаблон profile/ сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(PROFILE_URL, kwargs={'username': self.post.author})
        )
        context_object = response.context['page_obj'][0]
        context_object_author = response.context['author']
        self.assertEqual(context_object.text, self.post.text)
        self.assertEqual(context_object.group.title, self.post.group.title)
        self.assertIsNotNone(context_object.image)
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
        self.assertIsNotNone(context_object.image)
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

    def test_cache_index_page(self):
        """Главная страница кешируется."""
        response1 = self.client.get(reverse(INDEX_URL) + '?page=2')
        Post.objects.create(
            text=self.post.text,
            author=self.post.author,
        )
        response2 = self.client.get(reverse(INDEX_URL) + '?page=2')
        self.assertEqual(response1.content, response2.content)
        cache.clear()
        response3 = self.client.get(reverse(INDEX_URL) + '?page=2')
        self.assertNotEqual(response1.content, response3.content)

    def test_authorized_user_can_follow_and_unfollow(self):
        """Авторизованный пользователь может подписываться на
        других пользователей и удалять их из подписок."""
        follower = User.objects.get(username=self.user)
        follows_count = follower.follower.all().count()
        response_follow = self.authorized_client.get(
            reverse(
                FOLLOW_URL,
                kwargs={'username': self.post.author})
        )
        self.assertEqual(follower.follower.all().count(), follows_count + 1)
        follows_before_unfollow = follower.follower.all().count()
        response_unfollow = self.authorized_client.get(
            reverse(
                UNFOLLOW_URL,
                kwargs={'username': self.post.author})
        )
        self.assertEqual(
            follower.follower.all().count(),
            follows_before_unfollow - 1
        )

    def test_new_post_on_followers_page(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан."""
        follower = User.objects.get(username=self.user)
        response_follow = self.authorized_client.get(
            reverse(
                FOLLOW_URL,
                kwargs={'username': self.post.author})
        )
        Post.objects.create(
            text=self.post.text,
            author=self.post.author,
        )
        response_new_post_in_feed = self.authorized_client.get(
            reverse(FOLLOW_INDEX_URL)
        )
        new_post_in_context = response_new_post_in_feed.context['page_obj'][0]
        self.assertEqual(new_post_in_context.text, self.post.text)
        
        response_unfollow_user = self.unfollowing_user.get(
            reverse(FOLLOW_INDEX_URL)
        )
        context_unfollowing = response_unfollow_user.context['page_obj']
        self.assertEqual(len(context_unfollowing), 0)
