from django.shortcuts import get_object_or_404
from django.http import Http404
from django.db.models import Count
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (CreateView, DeleteView, ListView,
                                  UpdateView, DetailView)
from django.urls import reverse_lazy

from .forms import CommentForm, PostForm, UserProfileForm
from .models import Post, Category, Comment
from .mixins import UserCommentAuthorMixin, UserPostMixin

COUNT_POSTS_ON_MAIN = 10


def get_posts(add_filter=False, add_comments=False):
    """Получение базового кверисета постов"""
    query_set = Post.objects.select_related('category', 'location', 'author')

    if add_filter:
        query_set = query_set.filter(
            category__is_published=True, is_published=True,
            pub_date__lte=timezone.now())
    if add_comments:
        query_set = query_set.annotate(
            comment_count=Count('comments')).order_by('-pub_date')

    return query_set


class Index(ListView):
    """Отображает главную страницу"""

    template_name = 'blog/index.html'
    paginate_by = COUNT_POSTS_ON_MAIN

    def get_queryset(self):
        return get_posts(add_filter=True, add_comments=True)


class CategoryPosts(ListView):
    """Страница категории постов"""

    model = Post
    template_name = 'blog/category.html'
    paginate_by = COUNT_POSTS_ON_MAIN

    def get_queryset(self):
        return get_posts(
            add_filter=True,
            add_comments=True).filter(category=self.get_category())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.get_category()
        return context

    def get_category(self):
        """Получение категории"""
        return get_object_or_404(
            Category, slug=self.kwargs.get(
                'category_slug'), is_published=True)


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


class PostEditView(UserPostMixin, UpdateView):
    """Редактирование поста"""

    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']})


class PostDeleteView(UserPostMixin, DeleteView):
    """Удаление поста"""

    model = Post
    success_url = reverse_lazy('blog:index')
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Создание комментарией к посту"""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']})


class CommentEditView(UserCommentAuthorMixin, UpdateView):
    """Редактирование комментарием"""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'


class CommentDeleteView(UserCommentAuthorMixin, DeleteView):
    """Удаление комментариев"""

    model = Comment
    template_name = 'blog/comment.html'


class ProfileUser(ListView):
    """Страница профиля пользователя"""

    model = get_user_model()
    template_name = 'blog/profile.html'
    paginate_by = COUNT_POSTS_ON_MAIN

    def get_queryset(self):
        user = self.get_user()
        query_set = get_posts(
            add_filter=self.request.user != user, add_comments=True)
        return query_set.filter(author=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.get_user()
        return context

    def get_user(self):
        """Получение объекта пользователя"""
        return get_object_or_404(get_user_model(),
                                 username=self.kwargs.get('username'))


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
