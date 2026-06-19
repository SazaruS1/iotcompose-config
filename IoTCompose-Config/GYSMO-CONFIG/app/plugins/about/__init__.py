from core.plugin import Plugin


class AboutPlugin(Plugin):

    def webapps(self):
        from .webapp import create_webapp
        webapp = create_webapp(self.pid)

        return [webapp]



