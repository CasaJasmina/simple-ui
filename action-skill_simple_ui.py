#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from snipsTools import SnipsConfigParser
from hermes_python.hermes import Hermes
from hermes_python.ontology import *
import io
import requests

CONFIG_INI = "config.ini"

# If this skill is supposed to run on the satellite,
# please get this mqtt connection info from <config.ini>
# Hint: MQTT server is always running on the master device
MQTT_IP_ADDR = "localhost"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))
databaseurl = ""
class SimpleUI(object):

    def __init__(self):
        # get the configuration
        try:
            global databaseurl
            self.config = SnipsConfigParser.read_configuration_file(CONFIG_INI)
	        databaseurl = self.config.get("secret").get("database")
        except :
            self.config = None

        # start listening to MQTT
        self.start_blocking()
    def food_callback(self, hermes, intent_message):
        global databaseurl
        good_category = requests.get(databaseurl).json().get("food").get("categories")
        category = None
        if intent_message.slots:
            category = intent_message.slots.category.first().value
            if category.encode("utf-8") not in good_category:
                category = None

        if category is None:
            Answer = "Sorry I didn't understand. Say "+", ".join(good_category)+" to get help."
            hermes.publish_continue_session(intent_message.session_id,Answer, ["casajasmina:Food"])
        else:
            Answer = str(requests.get(databaseurl).json().get("food").get(category))
            hermes.publish_end_session(intent_message.session_id,Answer)

    def emergency_callback(self, hermes, intent_message):
        global databaseurl
        good_category = requests.get(databaseurl).json().get("emergency").get("categories")
        category = None
        if intent_message.slots:
            category = intent_message.slots.category.first().value
            if category.encode("utf-8") not in good_category:
                category = None

        if category is None:
            Answer = "Sorry I didn't understand. Say "+", ".join(good_category)+" to get help."
            hermes.publish_continue_session(intent_message.session_id,Answer, ["casajasmina:emergency"])
        else:
            Answer = str(requests.get(databaseurl).json().get("emergency").get(category))
            hermes.publish_end_session(intent_message.session_id,Answer)


    def whereIs_callback(self, hermes, intent_message):
        global databaseurl
        good_category = requests.get(databaseurl).json().get("categories")
        category = None
        if intent_message.slots:
            category = intent_message.slots.category.first().value
            if category.encode("utf-8") not in good_category:
                category = None

        if category is None:
            Answer = "Sorry I didn't understand. Say "+", ".join(good_category)+" to get help."
            hermes.publish_continue_session(intent_message.session_id,Answer, ["casajasmina:WhereIs"])
        else:
	    subcategory = requests.get(databaseurl).json().get(category).get("categories")
	    if subcategory is None:
	        Answer = requests.get(databaseurl).json().get(category).get(category)
            action_url = requests.get(databaseurl).json().get(category).get("url")
                if action_url is not None:
                    requests.get(action_url)
      	        hermes.publish_end_session(intent_message.session_id,Answer)
            else:
                Answer = "You asked for "+category+", Do you want to "+", ".join(subcategory)+" "+category+"?"
                hermes.publish_continue_session(intent_message.session_id,Answer, ["casajasmina:Food","casajasmina:emergency"])


    def askHelp_callback(self, hermes, intent_message):
        global databaseurl
	    good_category = requests.get(databaseurl).json().get("categories")
       	Answer = "Hey User, I'm here for you. I can help you with "+", ".join(good_category)
        user =  self.config.get("secret").get("name")
        if user is not None and user is not "":
            Answer = Answer.replace('User', user)

        hermes.publish_continue_session(intent_message.session_id, Answer,["casajasmina:WhereIs"])

    def master_intent_callback(self,hermes, intent_message):
        coming_intent = intent_message.intent.intent_name
        if coming_intent == 'casajasmina:WhereIs':
            self.whereIs_callback(hermes, intent_message)
	    elif coming_intent == 'casajasmina:ConnectMe':
            self.askHelp_callback(hermes, intent_message)
	    elif coming_intent == 'casajasmina:Food':
            self.food_callback(hermes, intent_message)
        elif coming_intent == 'casajasmina:emergency':
            self.emergency_callback(hermes, intent_message)
        # more callback and if condition goes here...

    # --> Register callback function and start MQTT
    def start_blocking(self):
        with Hermes(MQTT_ADDR) as h:
            h.subscribe_intents(self.master_intent_callback).start()

if __name__ == "__main__":
    SimpleUI()
