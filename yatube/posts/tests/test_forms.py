import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Group, Post, Comment, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

PROFILE_URL = 'posts:profile'
POST_CREATE_URL = 'posts:post_create'
INDEX_URL = 'posts:index'
POST_ID_URL = 'posts:post_detail'
POST_EDIT_URL = 'posts:post_edit'
POST_DETAIL_URL = 'posts:post_detail'
ADD_COMMENT_URL = 'posts:add_comment'


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_forms1')
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
        cls.test_text = 'Test form text'
        cls.test_changed_text = 'Changed test form text'
        cls.comment_text = 'Test comment text'

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_post_author = Client()
        self.authorized_post_author.force_login(self.post.author)

    def test_create_post_from(self):
        """Валидная форма создает запись."""
        posts_count = Post.objects.count()
        small_gif = (
             b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': self.test_text,
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
            Post.objects.filter(text=form_data['text']).exists()
        )
        self.assertTrue(
            Post.objects.filter(group=form_data['group']).exists()
        )
        new_post_author = Post.objects.get(author=self.user)
        self.assertEqual(
            new_post_author.author.username,
            self.user.username
        )

    def test_author_can_edit_post(self):
        """Автор поста может редактировать текст и менять группу."""
        form_data = {
            'text': self.test_changed_text,
            'group': self.new_group.id
        }
        response_edit = self.authorized_post_author.post(
            reverse(POST_EDIT_URL, kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True,
        )
        post_change = Post.objects.get(pk=self.post.pk)
        self.assertEqual(post_change.text, form_data['text'])
        self.assertEqual(post_change.group.id, form_data['group'])
        self.assertRedirects(
            response_edit,
            reverse(POST_DETAIL_URL, kwargs={'post_id': self.post.pk})
        )

    def test_write_comment_can_only_authorized_user(self):
        """Писать комментарии может только авторизованный пользвоатель."""
        form_data = {'text': self.comment_text}
        response_comment_guest = self.guest_client.post(
            reverse(ADD_COMMENT_URL, kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertFalse(
            Comment.objects.filter(text=form_data['text']).exists()
        )
        response_comment_authorized = self.authorized_client.post(
            reverse(ADD_COMMENT_URL, kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertTrue(
            Comment.objects.filter(text=form_data['text']).exists()
        )

    def test_comment_on_post_page(self):
        """После отправки комментарий появляется на странице поста."""
        form_data = {'text': self.comment_text}
        post_comments = 0
        response_comment = self.authorized_client.post(
            reverse(ADD_COMMENT_URL, kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True,
        )
        post = Post.objects.get(pk=self.post.pk)
        total_post_comments = post.comments.count()
        self.assertEqual(total_post_comments, post_comments + 1)
