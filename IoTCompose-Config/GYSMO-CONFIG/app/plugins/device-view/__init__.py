import datetime

from flask import Blueprint, render_template

from core.plugin import Plugin


class DeviceViewWelcomePlugin(Plugin):

    def webapps(self):
        from .webapp import webapp
        webapp.name = self.pid

        return [webapp]

