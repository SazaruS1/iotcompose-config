from core.plugin import Plugin


class MessagePlugin(Plugin):

    def webapps(self):
        from .webapp import webapp
        webapp.name = self.pid
        return [webapp]



