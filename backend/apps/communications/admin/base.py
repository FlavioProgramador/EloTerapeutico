from unfold.admin import ModelAdmin


class ReadOnlyHistoryAdmin(ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False
