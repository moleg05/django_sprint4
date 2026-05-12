from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from blog.models import Post, Category, Comment
from .forms import CommentForm
from django.contrib.auth.models import User
from .forms import PostForm, UserEditForm
from django.core.paginator import Paginator
from django.http import Http404
from django.contrib.auth import logout


def profile(request, username):
    user = get_object_or_404(User, username=username)
    if request.user == user:
        posts = Post.objects.filter(author=user).order_by("-pub_date")
    else:
        posts = Post.objects.filter(
            author=user, is_published=True, category__is_published=True
        ).order_by("-pub_date")
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "profile": user,
        "page_obj": page_obj,
        "user": user,
    }
    return render(request, "blog/profile.html", context)


def post_detail(request, id):
    template_name = "blog/detail.html"
    if request.user.is_authenticated:
        post = get_object_or_404(Post, id=id)
        if not post.is_published and post.author != request.user:
            raise Http404("Пост не найден")
        if post.pub_date > timezone.now() and post.author != request.user:
            raise Http404("Пост не найден")
        if not post.category.is_published and post.author != request.user:
            raise Http404("Пост не найден")
    else:
        post = get_object_or_404(
            Post,
            id=id,
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True,
        )
    comments = post.comments.select_related("author").order_by("created_at")
    context = {
        "post": post,
        "comments": comments,
        "form": CommentForm(),
    }
    return render(request, template_name, context)


def index(request):

    template_name = "blog/index.html"
    posts = Post.objects.filter(
        is_published=True, pub_date__lte=timezone.now(),
        category__is_published=True
    ).order_by("-pub_date")
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {"page_obj": page_obj}
    return render(request, template_name, context)


def category_posts(request, category_slug):
    template_name = "blog/category.html"
    category = get_object_or_404(Category, slug=category_slug,
                                 is_published=True)
    posts = Post.objects.filter(
        category=category, is_published=True, pub_date__lte=timezone.now()
    ).order_by("-pub_date")

    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {"category": category, "page_obj": page_obj}
    return render(request, template_name, context)


@login_required
def add_comment(request, pk, pk_c=None):
    post = get_object_or_404(Post, pk=pk)
    if pk_c is not None:
        comment = get_object_or_404(Comment, pk=pk_c)
        if comment.author != request.user:
            return redirect("blog:post_detail", id=post.id)
        if request.method == "GET":
            form = CommentForm(instance=comment)
            context = {"form": form, "post": post, "comment": comment}
            return render(request, "blog/comment.html", context)
        if request.method == "POST":
            form = CommentForm(request.POST, instance=comment)
            if form.is_valid():
                form.save()
                post.comment_count = post.comments.count()
                post.save(update_fields=['comment_count'])
                return redirect("blog:post_detail", id=post.id)
            context = {"form": form, "post": post, "comment": comment}
            return render(request, "blog/comment.html", context)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            post.comment_count = post.comments.count()
            post.save(update_fields=['comment_count'])
            return redirect("blog:post_detail", id=post.id)
    return redirect("blog:post_detail", id=post.id)


@login_required
def create_post(request, pk=None):
    if pk is not None:
        post = get_object_or_404(Post, pk=pk)
        if post.author != request.user:
            return redirect("blog:post_detail", id=post.id)
        form = PostForm(request.POST or None,
                        request.FILES or None,
                        instance=post)
    else:
        post = None
        form = PostForm(request.POST or None, request.FILES or None)

    context = {"form": form}

    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("blog:profile", username=request.user.username)

    return render(request, "blog/create.html", context)


@login_required
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user:
        return redirect("blog:post_detail", id=post.id)
    if request.method == "POST":
        post.delete()
        return redirect("blog:profile", username=request.user.username)
    context = {"form": PostForm(instance=post)}
    return render(request, "blog/create.html", context)


@login_required
def delete_comment(request, pk, pk_c):
    comment = get_object_or_404(Comment, pk=pk_c)
    post = comment.post
    if comment.author != request.user:
        return redirect("blog:post_detail", id=post.id)
    if request.method == "GET":
        context = {"comment": comment, "post": post}
        return render(request, "blog/comment.html", context)
    if request.method == "POST":
        comment.delete()
        post.comment_count = post.comments.count()
        post.save(update_fields=['comment_count'])
        return redirect("blog:post_detail", id=post.id)
    return redirect("blog:post_detail", id=post.id)


@login_required
def edit_profile(request, username):
    """Редактирование профиля пользователя"""
    user = get_object_or_404(User, username=username)
    if request.user != user:
        return redirect("blog:profile", username=username)
    if request.method == "POST":
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect("blog:profile", username=username)
    else:
        form = UserEditForm(instance=user)
    context = {"form": form, "profile": user}
    return render(request, "blog/create.html", context)


def custom_logout(request):
    logout(request)
    return render(request, 'registration/logged_out.html')
# Create your views here.
