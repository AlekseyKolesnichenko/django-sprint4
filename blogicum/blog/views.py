from django.shortcuts import get_object_or_404, redirect
from django.http import Http404
from django.db.models import Count
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (CreateView, DeleteView, ListView,
                                  UpdateView, DetailView)
from django.urls import reverse_lazy

from .forms import CommentForm, PostForm, UserProfileForm
from .models import Post, Category, Comment

COUNT_POSTS_ON_MAIN = 10


def get_queryset_posts(
        is_published=False,
        category_is_published=False,
        deferred=False):
    """Получение базового кверисета постов"""
    query_set = Post.objects.select_related('category', 'location', 'author')

    if category_is_published:
        query_set = query_set.filter(category__is_published=True)
    if is_published:
        query_set = query_set.filter(is_published=True)
    if deferred:
        query_set = query_set.filter(pub_date__lte=timezone.now())

    return query_set


def get_category(request):
    """Получение категории"""
    category = get_object_or_404(
        Category, slug=request.kwargs.get('category_slug'), is_published=True)
    return category


def get_user(request):
    """Получение объекта пользователя"""
    username = request.kwargs.get('username')
    return get_object_or_404(get_user_model(), username=username)


class Index(ListView):
    """Отображает главную страницу"""

    template_name = 'blog/index.html'
    paginate_by = COUNT_POSTS_ON_MAIN

    def get_queryset(self):
        return get_queryset_posts(
            is_published=True,
            category_is_published=True,
            deferred=True).annotate(
            comment_count=Count('comments')).order_by('-pub_date')


class CategoryPosts(ListView):
    """Страница категории постов"""

    model = Post
    template_name = 'blog/category.html'
    paginate_by = COUNT_POSTS_ON_MAIN

    def get_queryset(self):
        posts = get_queryset_posts(
            is_published=True,
            category_is_published=True,
            deferred=True).filter(
                category=get_category(self),).annotate(
                comment_count=Count('comments')).order_by('-pub_date')
        return posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_category(self)
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    """Создание поста"""

    template_name = 'blog/create.html'
    model = Post
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile', kwargs={'username': self.request.user.username})


class PostDetailView(DetailView):
    """Подробное описание поста"""

    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        post = super().get_object(queryset)
        if self.request.user != post.author:
            if (
                not post.is_published
                or not post.category.is_published
                or post.pub_date > timezone.now()
            ):
                raise Http404("Объект не найден")
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.comments.select_related('author')
        )
        return context


class PostEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование поста"""

    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm
    pk_url_kwarg = 'post_id'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def handle_no_permission(self):
        return redirect(
            reverse(
                'blog:post_detail',
                kwargs={'post_id': self.kwargs['post_id']}))

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']})


class PostDeleteView(UserPassesTestMixin, DeleteView):
    """Удаление поста"""

    model = Post
    success_url = reverse_lazy('blog:index')
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def handle_no_permission(self):
        return redirect(
            reverse(
                'blog:post_detail',
                kwargs={'post_id': self.kwargs['post_id']}))


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Создание комментарией к посту"""

    post_ = None
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        post_obj = get_object_or_404(Post, pk=self.kwargs['post_id'])
        form.instance.post = post_obj
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']})


class CommentEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование комментарием"""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def get_object(self):
        comment_obj = get_object_or_404(
            Comment, pk=self.kwargs['comment_id'],
            post_id=self.kwargs['post_id'])
        return comment_obj

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def handle_no_permission(self):
        return redirect(
            reverse('blog:post_detail',
                    kwargs={'post_id': self.kwargs['post_id']}))

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']})


class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Удаление комментариев"""

    model = Comment
    template_name = 'blog/comment.html'

    def get_object(self):
        comment_obj = get_object_or_404(
            Comment, pk=self.kwargs['comment_id'],
            post_id=self.kwargs['post_id'])
        return comment_obj

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']})

    def handle_no_permission(self):
        return redirect(reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']}))


class ProfileUser(ListView):
    """Страница профиля пользователя"""

    model = get_user_model()
    template_name = 'blog/profile.html'
    paginate_by = COUNT_POSTS_ON_MAIN

    def get_queryset(self):
        user = get_user(self)
        if self.request.user.is_authenticated:
            query_set = get_queryset_posts(
                is_published=False, category_is_published=False,
                deferred=False)
        else:
            query_set = get_queryset_posts(
                is_published=True, category_is_published=True, deferred=True)
        posts = query_set.filter(author=user).order_by('-pub_date').annotate(
            comment_count=Count('comments'))
        return posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_user(self)
        return context


class EditProfileView(LoginRequiredMixin, UpdateView):
    """Редактирование профиля пользователя"""

    model = get_user_model()
    template_name = 'blog/user.html'
    form_class = UserProfileForm

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse(
            'blog:profile', kwargs={'username': self.request.user.username})
