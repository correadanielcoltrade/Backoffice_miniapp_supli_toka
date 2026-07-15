from django.contrib import admin

from .models import Carousel, CarouselImage


class CarouselImageInline(admin.TabularInline):
    model = CarouselImage
    extra = 0
    max_num = 4


@admin.register(Carousel)
class CarouselAdmin(admin.ModelAdmin):
    list_display = ("name", "width", "height", "is_active", "created_at")
    list_filter = ("is_active",)
    inlines = [CarouselImageInline]
