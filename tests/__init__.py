from data_registry.models import Task


class TestTask:
    def run(self):
        pass

    def get_status(self):
        return Task.Status.COMPLETED

    def wipe(self):
        pass
