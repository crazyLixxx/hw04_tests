from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm
from .models import Group, Post

User = get_user_model()


def posts_on_page(request, posts):
    paginator = Paginator(posts, 10)
    page = request.GET.get('page')
    return paginator.get_page(page)


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.all()
    context = {
        'page_obj': posts_on_page(request, posts),
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    context = {
        'group': group,
        'page_obj': posts_on_page(request, posts),
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', username=request.user.username)
        return render(request, template, {'form': form})
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        instance=post
    )
    if request.user == post.author:
        if request.method == 'POST':
            if form.is_valid():
                post = form.save(commit=False)
                post.author = request.user
                post.save()
                return redirect('posts:post_detail', post_id=post_id)
            return render(request, template, {'form': form})
        context = {
            'form': form,
            'is_edit': 'is_edit'
        }
        return render(request, template, context)
    return redirect('posts:post_detail', post_id=post_id)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    context = {'post': post}
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    context = {
        'author': author,
        'page_obj': posts_on_page(request, posts),
    }
    return render(request, template, context)
