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
databaseurl = "" #http rest url from config.ini


class SimpleUI(object):

    def __init__(self):
        # get the configuration
        try:
            global databaseurl
            self.config = SnipsConfigParser.read_configuration_file(CONFIG_INI)
            databaseurl = self.config.get("secret").get("database")
        except:
            self.config = None

        # start listening to MQTT
        self.start_blocking()
#callback for food intent, use it as a template for subcategory intents
    def food_callback(self, hermes, intent_message):
        global databaseurl
        #get categories from database
        good_category = requests.get(
            databaseurl).json().get("food").get("categories")
        category = None
        if intent_message.slots: #check is user request match subcategory
            category = intent_message.slots.category.first().value
            if category.encode("utf-8") not in good_category:
                category = None

        if category is None:
            Answer = "Sorry I didn't understand. Say " + \
                ", ".join(good_category) + " to get help."
            hermes.publish_continue_session(
                intent_message.session_id, Answer, ["casajasmina:Food"])
        else:
            #get the answer from the database
            Answer = str(requests.get(
                databaseurl).json().get("food").get(category))
            hermes.publish_end_session(intent_message.session_id, Answer)

#emergency callback is identical to food callback
    def emergency_callback(self, hermes, intent_message):
        global databaseurl
        good_category = requests.get(databaseurl).json().get(
            "emergency").get("categories")
        category = None
        if intent_message.slots:
            category = intent_message.slots.category.first().value
            if category.encode("utf-8") not in good_category:
                category = None

        if category is None:
            Answer = "Sorry I didn't understand. Say " + \
                ", ".join(good_category) + " to get help."
            hermes.publish_continue_session(intent_message.session_id, Answer, [
                                            "casajasmina:emergency"])
        else:
            Answer = str(requests.get(databaseurl).json().get(
                "emergency").get(category))
            hermes.publish_end_session(intent_message.session_id, Answer)

#generic callback for every category in the database, handles single and multi category topics
    def whereIs_callback(self, hermes, intent_message):
        global databaseurl
        #get categories from database
        good_category = requests.get(databaseurl).json().get("categories")
        category = None
        #handling user request
        if intent_message.slots:
            category = intent_message.slots.category.first().value
            if category.encode("utf-8") not in good_category:
                category = None

        if category is None:
            Answer = "Sorry I didn't understand. Say " + \
                ", ".join(good_category) + " to get help."
            hermes.publish_continue_session(
                intent_message.session_id, Answer, ["casajasmina:WhereIs"])
        else:
            #get subcategory
            subcategory = requests.get(databaseurl).json().get(
                category).get("categories")
            if subcategory is None:
                Answer = requests.get(databaseurl).json().get(
                    category).get(category)
                action_url = requests.get(
                    databaseurl).json().get(category).get("url")
                #call an action if specified
                if action_url is not None:
                    requests.get(action_url)
                hermes.publish_end_session(intent_message.session_id, Answer)
            else:
                #multi category handling
                Answer = "You asked for " + category + \
                    ", I can give you tips on " + ", ".join(subcategory)
                hermes.publish_continue_session(intent_message.session_id, Answer, [
                                                "casajasmina:Food", "casajasmina:emergency"])

#first interaction callback
    def askHelp_callback(self, hermes, intent_message):
        global databaseurl
        #get categories from database
        good_category = requests.get(databaseurl).json().get("categories")
        Answer = "Hey friend, I'm here for you. I can help you with " + \
            ", ".join(good_category)
        #get user name from database
        user = requests.get(databaseurl).json().get("user")
        if user is not None and user is not "":
            Answer = Answer.replace('firend', user)

        hermes.publish_continue_session(
            intent_message.session_id, Answer, ["casajasmina:WhereIs"])

    def master_intent_callback(self, hermes, intent_message):
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
