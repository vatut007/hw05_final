from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow
from .utils import get_page_context


def index(request):
    posts = Post.objects.select_related('group').all()
    context = get_page_context(posts, request)
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    context = {
        'group': group,
    }
    context.update(get_page_context(group.posts.all(), request))
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = request.user.is_authenticated and (
        Follow.objects.filter(
            user=request.user,
            author=author
        ).exists())
    context = {
        'author': author,
        'following': following
    }
    context.update(get_page_context(author.posts.all(), request))
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm()
    comments = post.comments.all()
    count_of_posts = post.author.posts.count()
    if request.user != post.author:
        author_is_user = False
    else:
        author_is_user = True
    context = {
        'post': post,
        'count_of_posts': count_of_posts,
        'author_is_user': author_is_user,
        'comments': comments,
        'form': form}
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user)
    else:
        form = PostForm()
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post.id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    is_edit = True
    template = 'posts/create_post.html'
    context = {'form': form,
               'post': post,
               'is_edit': is_edit
               }
    if not form.is_valid():
        return render(request, template, context)
    form.save()
    return redirect('posts:post_detail', post_id=post.id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.select_related(
        'group').filter(author__following__user=request.user)
    context = get_page_context(posts, request)
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author == request.user:
        return redirect(
            'posts:profile',
            username=username
        )
    Follow.objects.get_or_create(user=request.user, author=author)
    return redirect(
        'posts:profile',
        username=username
    )


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)

    if author == request.user:
        return redirect(
            'posts:profile',
            username=username
        )
    following = get_object_or_404(Follow, user=request.user, author=author)
    following.delete()
    return redirect(
        'posts:profile',
        username=username
    )
