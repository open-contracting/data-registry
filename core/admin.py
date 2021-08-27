from django.contrib import admin


class CoreAdminSite(admin.AdminSite):
    site_header = 'Data registry administration'
    site_title = 'Data registry administration'

    def get_app_list(self, request):
        """
        Sorts the data registry's models in a logical order.
        """
        order = [
            'Collection',
            'Issue',
            'License',
            'Job',
            'Task',
        ]

        def sort(model):
            try:
                return str(order.index(model['object_name']))
            except ValueError:
                return model['name']

        app_list = super().get_app_list(request)

        if app_list:
            app = next(app for app in app_list if app['app_label'] == 'data_registry')
            app['models'].sort(key=sort)

        return app_list
