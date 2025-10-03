from django.shortcuts import get_object_or_404, redirect
from django.http import Http404
from django.core.paginator import Paginator
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


def get_queryset_posts(is_published=True,
                       category_is_published=True, deferred=True):
    """Получение базового кверисета постов"""
    filters = {}

    if category_is_published:
        filters['category__is_published'] = True
    if is_published:
        filters['is_published'] = True
    if deferred:
        filters['pub_date__lte'] = timezone.now()

    return Post.objects.filter(**filters).select_related('category',
                                                         'location', 'author')


class Index(ListView):
    """Отображает главную страницу"""

    template_name = 'blog/index.html'
    paginate_by = COUNT_POSTS_ON_MAIN

    def get_queryset(self):
        return get_queryset_posts().annotate(
            comment_count=Count('comments')).order_by('-pub_date')


class CategoryPosts(ListView):
    """Страница категории постов"""

    model = Post
    template_name = 'blog/category.html'

    def get_context_data(self, **kwargs):
        category = get_object_or_404(Category,
                                     slug=self.kwargs.get('category_slug'),
                                     is_published=True)
        context = super().get_context_data(**kwargs)
        posts = get_queryset_posts().filter(
            category=category,).annotate(
                comment_count=Count('comments')).order_by('-pub_date')

        paginator = Paginator(posts, COUNT_POSTS_ON_MAIN)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['page_obj'] = page_obj
        context['posts'] = page_obj.object_list
        context['category'] = category
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
        return reverse('blog:profile', kwargs={'username':
                                               self.request.user.username})


class PostDetailView(DetailView):
    """Подробное описание поста"""

    model = Post
    template_name = 'blog/detail.html'

    def get_object(self):
        post = super().get_object()
        if self.request.user != post.author and not post.is_published:
            raise Http404("Объект не найден")
        else:
            return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['user'] = self.request.user
        context['comments'] = (
            self.object.comments.select_related('author')
        )
        return context


class PostEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование поста"""

    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def handle_no_permission(self):
        post = self.get_object()
        return redirect(reverse('blog:post_detail', kwargs={'pk': post.pk}))

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.object.pk})


class PostDeleteView(UserPassesTestMixin, DeleteView):
    """Удаление поста"""

    model = Post
    success_url = reverse_lazy('blog:index')
    template_name = 'blog/create.html'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Создание комментарией к посту"""

    post_ = None
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        self.post_ = get_object_or_404(Post, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.post_
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.post_.pk})


class CommentEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование комментарием"""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_pk'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk':
                                                   self.kwargs['post_pk']})


class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Удаление комментариев"""

    model = Comment
    pk_url_kwarg = 'comment_pk'
    template_name = 'blog/comment.html'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk':
                                                   self.kwargs['post_pk']})


class ProfileUser(DetailView):
    """Страница профиля пользователя"""

    model = get_user_model()
    template_name = 'blog/profile.html'
    # context_object_name = 'profile'

    def get_object(self):
        username = self.kwargs.get('username')
        return get_object_or_404(get_user_model(), username=username)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()

        posts = get_queryset_posts(False, False, False).filter(
            author=user).order_by('-pub_date').annotate(
                comment_count=Count('comments'))

        paginator = Paginator(posts, COUNT_POSTS_ON_MAIN)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['page_obj'] = page_obj
        context['posts'] = page_obj.object_list
        context['profile'] = user
        return context


class EditProfileView(LoginRequiredMixin, UpdateView):
    """Редактирование профиля пользователя"""

    model = get_user_model()
    template_name = 'blog/user.html'
    form_class = UserProfileForm

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username':
                                               self.request.user.username})
