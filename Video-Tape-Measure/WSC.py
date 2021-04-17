# -*- coding: utf-8 -*-
"""
Created on Tue Feb 23 19:30:42 2021

@author: slalo
"""

from socketio import Client
import json

class WSC(object):
        
    def __init__(self):
        self = Client()
    
    @self.event
    def connect():
        print('\nconnection established using SID', self.sid)

    def get_pin(self, loggingdetail, mode, eventid, eventsubid, provider, application, version, username):
        
#           "loggingdetail": "no", // if yes then message contents will be logged
#           "mode": "Tournament", // Tournament or Standalone - normally Tournament
#           "eventid": "20E016", // The official Tournament Id
#           "eventsubid": "North Lake", // Blank UNLESS you there are multiple scoring systems in use at a single event
#           "provider": "SplashEye", // The manufacturer of the application that is connecting
#           "application": "Lion Simulator", // The application name of the application that is connecting
#           "version": "4.5.6", // The version of the application that is connecting
#           "username": "lionsim@splasheye.com" // The current user of the connecting application
        data = {
           "loggingdetail": loggingdetail, 
           "mode": mode, 
           "eventid": eventid, 
           "eventsubid": eventsubid, 
           "provider": provider, 
           "application": application, 
           "version": version, 
           "username": username}
        datajson = json.dumps(data)

        self.connect('http://localhost:5000', headers=datajson)
        
    def get_athlete_data(self):
        self.emit('athlete_data', callback = 'athleteData')
        
    @self.event
    def athleteData(self, athleteJSON):
        athleteDict = json.loads(athleteJSON)
        self.skier = athleteDict['athleteName']
        self.division = athleteDict['athleteDivision']
        self.round = athleteDict['round']
        
    def get_running_order(self):
        self.emit('start_list', callback = 'runningOrder')
        
    self@event
    def running_order(self, orderJSON):
        orderDict = json.loads(orderJSON)
        
        
        
        
        
if __name__ == '__main__':
    sio = WSC()
        