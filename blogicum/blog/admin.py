from django.contrib import admin

from .models import Post, Category, Location


class PostAdmin(admin.ModelAdmin):
    list_display = ('is_published',
                    'created_at',
                    'title',
                    'pub_date',
                    'author',
                    'location',
                    'category',
                    )

    list_editable = ('is_published',
                     'location',
                     'category')

    search_fields = ('title',)
    list_filter = ('category', 'location')
    list_display_links = ('title', )


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('is_published',
                    'title',
                    'description',
                    'slug',
                    )

    list_editable = ('is_published',)

    search_fields = ('title',)
    list_filter = ('title', 'is_published')
    list_display_links = ('title',)


class LocationAdmin(admin.ModelAdmin):
    list_display = ('is_published',
                    'name',
                    )

    list_editable = ('is_published',)

    search_fields = ('name',)
    list_filter = ('name', 'is_published')
    list_display_links = ('name',)


admin.site.register(Post, PostAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Location, LocationAdmin)

admin.site.empty_value_display = 'Не задано'
