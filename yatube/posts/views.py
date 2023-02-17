from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Group, Post, Comment, User, Follow
from .utils import get_pages


@cache_page(20, key_prefix='index_page')
def index(request):
    posts = Post.objects.select_related(
        'author').select_related(
        'group').all()
    page_obj = get_pages(request, posts)
    return render(request, 'posts/index.html', {'page_obj': page_obj})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = get_pages(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    page_obj = get_pages(request, posts)
    context = {
                'author': author,
                'page_obj': page_obj,
            }
    if request.user.is_authenticated:
        follower = Follow.objects.filter(user=request.user,author=author).exists()
        if not follower:
            return render(request, 'posts/profile.html', context)
        context = {
            'author': author,
            'page_obj': page_obj,
            'following': True,
        }
        return render(request, 'posts/profile.html', context)
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', username=request.user)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        instance=post,
        files=request.FILES or None,
    )
    if not form.is_valid():
        context = {'form': form, 'is_edit': True}
        return render(request, 'posts/create_post.html', context)
    post = form.save()
    post.author = request.user
    post.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if not form.is_valid():
        return redirect('posts:post_detail', post_id=post_id)
    comment = form.save(commit=False)
    comment.author = request.user
    comment.post = post
    comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = get_pages(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    following = Follow.objects.filter(user=request.user, author=author)
    if following.exists():
        following.delete()
    return redirect('posts:profile', username=username)
