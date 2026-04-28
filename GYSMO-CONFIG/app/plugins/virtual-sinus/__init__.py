import datetime

from flask import Blueprint, render_template

from core.plugin import Plugin


class VirtualSinusPlugin(Plugin):

    def webapps(self):
        from .webapp import webapp
        webapp.name=self.pid
        return [webapp]


    def tasks(self):
        from .task import VirtualSinusTask
        task = VirtualSinusTask(f"{self.pid}-task", f"{self.pid}")
        return [task]

    # def start(self):
    #     # On enr egistre la partie web
    #     from .webapp import webapp
    #
    #     # On configure la webApp si nécessaire
    #     webapp.name = self.uid
    #     WebService().register(webapp,self)
    #
    #     # On configure les Tasks si nécessaire
    #
    #
    #
    #
    #
