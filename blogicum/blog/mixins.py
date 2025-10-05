from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from .models import Comment


class UserCommentAuthorMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Миксин для проверки, что пользователь —
    автор комментария.
    """

    def get_object(self):
        return get_object_or_404(
            Comment, pk=self.kwargs['comment_id'],
            post_id=self.kwargs['post_id'])

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']})

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def handle_no_permission(self):
        return redirect(
            reverse('blog:post_detail',
                    kwargs={'post_id': self.kwargs['post_id']}))


class UserPostMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Миксин для проверки, что пользователь — автор поста."""

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def handle_no_permission(self):
        return redirect(
            reverse(
                'blog:post_detail',
                kwargs={'post_id': self.kwargs['post_id']}))
