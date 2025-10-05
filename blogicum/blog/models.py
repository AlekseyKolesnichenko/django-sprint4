from django.db import models
from django.contrib.auth import get_user_model

from core.models import PublishedModel


MAX_LENGTH_FIELD = 256

User = get_user_model()


class Location(PublishedModel):
    """Модель Географическая метка"""

    name = models.CharField(max_length=MAX_LENGTH_FIELD, blank=True,
                            verbose_name='Название места')

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return self.name


class Category(PublishedModel):
    """Модель Категория"""

    title = models.CharField(max_length=MAX_LENGTH_FIELD, blank=True,
                             verbose_name='Заголовок')
    description = models.TextField(blank=True, verbose_name='Описание')
    slug = models.SlugField(unique=True,
                            verbose_name='Идентификатор',
                            help_text='Идентификатор страницы для URL; '
                            'разрешены символы латиницы, цифры, дефис и '
                            'подчёркивание.')

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.title


class Post(PublishedModel):
    """Модель Публикации"""

    title = models.CharField(max_length=MAX_LENGTH_FIELD, blank=True,
                             verbose_name='Заголовок')
    text = models.TextField(blank=True, verbose_name='Текст')
    pub_date = models.DateTimeField(blank=True,
                                    verbose_name='Дата и время публикации',
                                    help_text='Если установить дату и время в '
                                    'будущем — можно делать отложенные '
                                    'публикации.')

    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               verbose_name='Автор публикации')
    location = models.ForeignKey(Location, null=True,
                                 on_delete=models.SET_NULL,
                                 verbose_name='Местоположение',)
    category = models.ForeignKey(Category, null=True,
                                 on_delete=models.SET_NULL,
                                 verbose_name='Категория',)
    image = models.ImageField('Фото', upload_to='post_images', blank=True)

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ('pub_date',)
        default_related_name = 'posts'

    def __str__(self):
        return self.title


class Comment(models.Model):
    """Модель комментариев"""

    text = models.TextField('Текст комментария')
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ('created_at',)
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        default_related_name = 'comments'

    def __str__(self):
        return self.text
