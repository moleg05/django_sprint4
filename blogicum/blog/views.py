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
from django.db.models import Count


def get_posts_with_comments(queryset=None, filter_published=True, order_by="-pub_date"):
    if queryset is None:
        queryset = Post.objects.all()
    if filter_published:
        queryset = queryset.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        )
    queryset = queryset.annotate(comment_count=Count("comments"))
    if order_by:
        queryset = queryset.order_by(order_by)
    return queryset


def paginate_set(request, queryset, per_page=10):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get("page")
    return paginator.get_page(page_number)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    if request.user == user:
        posts = get_posts_with_comments(
            Post.objects.filter(author=user),
            filter_published=False,
            order_by="-pub_date"
        )
    else:
        posts = get_posts_with_comments(
            Post.objects.filter(author=user),
            filter_published=True,
            order_by="-pub_date"
        )
    page_obj = paginate_set(request, posts)
    context = {"profile": user, "page_obj": page_obj, "user": user}
    return render(request, "blog/profile.html", context)


def post_detail(request, post_id):
    template_name = "blog/detail.html"
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        if (
            not post.is_published
            or post.pub_date > timezone.now()
            or not post.category.is_published
        ):
            raise Http404("Пост не найден")
    comments = post.comments.select_related("author")
    comments = comments.order_by("created_at")
    context = {
        "post": post,
        "comments": comments,
        "form": CommentForm(),
    }
    return render(request, template_name, context)


def index(request):
    template_name = "blog/index.html"
    posts = get_posts_with_comments(order_by="-pub_date")
    page_obj = paginate_set(request, posts)
    context = {"page_obj": page_obj}
    return render(request, template_name, context)


def category_posts(request, category_slug):
    template_name = "blog/category.html"
    category = get_object_or_404(Category, slug=category_slug,
                                 is_published=True)
    posts = get_posts_with_comments(Post.objects.filter(category=category),
                                    filter_published=True,
                                    order_by="-pub_date")
    page_obj = paginate_set(request, posts)
    context = {"category": category, "page_obj": page_obj}
    return render(request, template_name, context)


@login_required
def add_comment(request, post_id, comment_id=None):
    post = get_object_or_404(Post, pk=post_id)
    if comment_id is not None:
        comment = get_object_or_404(Comment, pk=comment_id)
        if comment.author != request.user:
            return redirect("blog:post_detail", post_id=post.id)
        if request.method == "GET":
            form = CommentForm(instance=comment)
            context = {"form": form, "post": post, "comment": comment}
            return render(request, "blog/comment.html", context)
        if request.method == "POST":
            form = CommentForm(request.POST, instance=comment)
            if form.is_valid():
                form.save()
                return redirect("blog:post_detail", post_id=post.id)
            context = {"form": form, "post": post, "comment": comment}
            return render(request, "blog/comment.html", context)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect("blog:post_detail", post_id=post.id)
    return redirect("blog:post_detail", post_id=post.id)


@login_required
def create_post(request, post_id=None):
    if post_id is not None:
        post = get_object_or_404(Post, pk=post_id)
        if post.author != request.user:
            return redirect("blog:post_detail", post_id=post.id)
        form = PostForm(request.POST or None, request.FILES or None,
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
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect("blog:post_detail", post_id=post.id)
    if request.method == "POST":
        post.delete()
        return redirect("blog:profile", username=request.user.username)
    context = {"form": PostForm(instance=post)}
    return render(request, "blog/create.html", context)


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    post = comment.post
    if comment.author != request.user:
        return redirect("blog:post_detail", post_id=post.id)
    if request.method == "GET":
        context = {"comment": comment, "post": post}
        return render(request, "blog/comment.html", context)
    if request.method == "POST":
        comment.delete()
        return redirect("blog:post_detail", post_id=post.id)
    return redirect("blog:post_detail", post_id=post.id)


@login_required
def edit_profile(request, username):
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
    return render(request, "registration/logged_out.html")


# Create your views here.
