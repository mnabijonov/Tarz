
from django.contrib import admin
from .models import Category, District


class SubcategoryInline(admin.TabularInline):
    """Kategoriya ichidagi aniq xizmat turlari (masalan Elektrik → Rozetka va o'chirgich)."""

    model = Category
    fk_name = 'parent'
    extra = 1
    fields = ('name', 'name_ru', 'position', 'is_active')
    verbose_name = 'Xizmat turi'
    verbose_name_plural = "Xizmat turlari (mijoz buyurtmada shulardan birini tanlaydi)"


class TopLevelFilter(admin.SimpleListFilter):
    title = 'Daraja'
    parameter_name = 'level'

    def lookups(self, request, model_admin):
        return (('top', 'Asosiy kategoriyalar'), ('sub', 'Xizmat turlari'))

    def queryset(self, request, queryset):
        if self.value() == 'top':
            return queryset.filter(parent__isnull=True)
        if self.value() == 'sub':
            return queryset.filter(parent__isnull=False)
        return queryset


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'name',
        'name_ru',
        'parent',
        'icon',
        'position',
        'is_active',
    )

    list_display_links = (
        'id',
        'name',
    )

    list_editable = ('position', 'is_active')

    search_fields = (
        'name',
        'name_ru',
    )

    list_filter = (
        TopLevelFilter,
        'parent',
        'is_active',
    )

    list_select_related = ('parent',)
    inlines = [SubcategoryInline]
    list_per_page = 50


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'name_ru', 'city')
    list_editable = ('name_ru',)
    search_fields = ('name', 'name_ru')
