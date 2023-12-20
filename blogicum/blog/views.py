from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from .forms import CommentForm, PostForm
from .models import Category, Comment, Post, User

POSTS_PER_PAGE = 10


class UserMixin:
    model = User
    slug_url_kwarg = 'username'


class PostMixin:
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'


class PostDispatchMixin:

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs['post_id'])
        if instance.author != request.user:
            return redirect('blog:post_detail', post_id=instance.pk)
        return super().dispatch(request, *args, **kwargs)


class CommentMixin:
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Comment, pk=kwargs['comment_id'])
        if instance.author != request.user:
            return redirect('blog:post_detail', post_id=instance.post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.post.pk}
        )


class UserDetailView(UserMixin, DetailView):
    """Класс для страницы пользователя"""

    template_name = 'blog/profile.html'
    slug_field = User.USERNAME_FIELD

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = get_object_or_404(
            User,
            **{User.USERNAME_FIELD: self.kwargs['username']}
        )
        post_list = profile.posts.all().order_by(
            '-pub_date'
        ).annotate(
            comment_count=Count('comments')
        )

        paginator = Paginator(post_list, POSTS_PER_PAGE)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context["profile"] = profile
        context["page_obj"] = page_obj
        context["user"] = self.request.user
        return context


class UserEditUpdateView(UserMixin, LoginRequiredMixin, UpdateView):
    """Класс для редактирования страницы пользователя"""

    fields = ('username', 'first_name', 'last_name', 'email')
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        username = self.kwargs['username']
        return get_object_or_404(User.objects.filter(username=username))

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class IndexListView(ListView):
    """Класс обработки запроса для главной страницы приложения"""

    model = Post
    template_name = 'blog/index.html'
    today = timezone.now()
    queryset = Post.objects.filter(
        pub_date__lte=today,
        is_published=True,
        category__is_published=True
    ).select_related(
        'category',
        'location',
        'author',
    ).order_by(
        '-pub_date'
    ).annotate(comment_count=Count('comments'))
    paginate_by = POSTS_PER_PAGE


class CategoryPostsListView(ListView):
    """Класс обработки запроса для категории"""

    model = Category
    template_name = 'blog/category.html'
    paginate_by = POSTS_PER_PAGE

    def get_queryset(self):
        category_slug = self.kwargs['category_slug']
        today = timezone.now()
        return Post.objects.filter(
            category__slug=category_slug,
            is_published=True,
            pub_date__lte=today
        ).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        context['category'] = category
        return context


class PostCreateView(PostMixin, LoginRequiredMixin, CreateView):
    """Класс для создания публицаии"""

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(
    PostMixin,
    PostDispatchMixin,
    LoginRequiredMixin,
    UpdateView
):
    """Класс редактирования публикации"""

    pk_url_kwarg = 'post_id'


class PostDetailView(DetailView):
    """Класс обработки запроса для поста"""

    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/detail.html'

    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=kwargs['post_id'])
        today = timezone.now()
        if (
            not post.is_published
            or not post.category.is_published
            or not post.pub_date <= today
        ):
            if request.user == post.author:
                return super().dispatch(request, *args, **kwargs)
            else:
                return HttpResponseNotFound("Страница не найдена")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.comments.select_related('author')
        )
        return context


class PostDeleteView(
    PostMixin,
    PostDispatchMixin,
    LoginRequiredMixin,
    DeleteView
):
    """Класс удаления поста"""

    pk_url_kwarg = 'post_id'
    success_url = reverse_lazy('blog:index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instance = get_object_or_404(Post, pk=kwargs['object'].id)
        form = PostForm(instance=instance)
        context['form'] = form
        return context


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Класс для создания комментария"""

    post_object = None
    model = Comment
    form_class = CommentForm
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        self.post_object = get_object_or_404(Post, pk=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.post_object
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.post_object.pk}
        )


class CommentUpdateView(LoginRequiredMixin, CommentMixin, UpdateView):
    """Класс для редактирования комментария"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instance = get_object_or_404(Comment, pk=self.kwargs['comment_id'])
        form = CommentForm(instance=instance)
        context['form'] = form
        return context


class CommentDeleteView(LoginRequiredMixin, CommentMixin, DeleteView):
    """Класс для удаления комментария"""

    pass
