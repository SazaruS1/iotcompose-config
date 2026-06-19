from core.plugin import Plugin


class TaskListPlugin(Plugin):
    def webapps(self):
        # On enregistre la partie web
        from .webapp import webapp
        webapp.name = self.pid

        return [webapp]




