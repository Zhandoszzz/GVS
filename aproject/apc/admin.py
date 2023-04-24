from django.contrib import admin
from .models import Query
# Register your models here.
class QueryAdmin(admin.ModelAdmin):
    list_display = ('user', 'query', 'time_create', 'time_update')
    search_fields = ('query',)
admin.site.register(Query, QueryAdmin)