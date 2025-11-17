# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []
from typing import Any, Text, Dict, List

import arrow
# import datapreser
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, ActiveLoop
from rasa_sdk.types import DomainDict

city_db = {
    'brussels': 'Europe/Brussels',
    'zagreb': 'Europe/Zagreb',
    'london': 'Europe/Dublin',
    'lisbon': 'Europe/Lisbon',
    'amsterdam': 'Europe/Amsterdam',
    'seattle': 'US/Pacific',
    'tel-aviv': 'Asia/Jerusalem',
}

ALLOWED_PIZZA_SIZES = {
    "small",
    "medium",
    "large",
    "extra-large",
    "extra large",
    "s",
    "m",
    "l",
    "xl",
}
ALLOWED_PIZZA_TYPES = [
    "margherita",
    "pepperoni",
    "veggie",
    "hawaiian",
    "four cheese"
]
VEGETARIAN_PIZZAS = ["mozzarella", "fungi", "veggie"]
MEAT_PIZZAS =["pepperoni", "hawaii"]

class ActionTellTime(Action):

    def name(self) -> Text:
        return "action_tell_time"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        current_place = next(tracker.get_latest_entity_values("place"), None) #  gets the "place" if its empty it will fill with "None" 

        utc = arrow.utcnow()  # get current UTC time

        # if current_place is empty it return a utc time - a fallback
        if not current_place:
            msg = f"It's {utc.format('HH:mm')} utc now. You can also give me a place."
            dispatcher.utter_message(text=msg)
            return []

        # if current_place not found in the database - a fallback
        tz_string = city_db.get(current_place, None)
        if not tz_string:
            msg = f"I didn't recognize {current_place}. Is it spelled correctly?"
            dispatcher.utter_message(text=msg)
            return []

        # Convert utc to the timezone of the city
        local_time = utc.to(tz_string).format('HH:mm')
        msg = f"It's {local_time} in {current_place} now."
        dispatcher.utter_message(text=msg)

        return []
    
class ActionRememberWhere(Action):
    def name(self) -> Text:
        return "action_remember_where"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        current_place = next(tracker.get_latest_entity_values("place"), None) # gets the "place" if its empty it will fill with "None"
        # utc.arrow.utcnow()
        if current_place:
            current_place = current_place.lower()
        print("DEBUG current_place =", repr(current_place))
        # if current_place is empty it return a utc time - a fallback
        if not current_place:
            msg = f"I didn't get where you live. Are you sure it's spelled correctly?"
            dispatcher.utter_message(text=msg)
            return []

        # if current_place not found in the database - a fallback
        tz_string = city_db.get(current_place, None)
        if not tz_string:
            msg = f"I didn't recognize {current_place}. Is it spelled correctly?"
            dispatcher.utter_message(text=msg)
            return []

        msg = f"Sure thing! I'll remember that you live in {current_place}."
        dispatcher.utter_message(text=msg)

        return [SlotSet("location", current_place)]
        
class ValidationSimplePizzaForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_simple_pizza_form"

    def validate_pizza_size(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> Dict[Text, Any]:
        """Validate 'pizza_size' value"""

        if slot_value.lower() not in ALLOWED_PIZZA_SIZES:
            dispatcher.utter_message(text=f"We only accept pizza sizes: s/m/l/xl.")
            return {"pizza_size": None}
        dispatcher.utter_message(text=f"OK! You want to have a {slot_value} pizza.")
        # Multi-slot capture for pizza_type in the same message
        pizza_type = next(tracker.get_latest_entity_values("pizza_type"), None)
        result = {"pizza_size": slot_value}
        if pizza_type and pizza_type.lower() in ALLOWED_PIZZA_TYPES:
            result["pizza_type"] = pizza_type
            dispatcher.utter_message(text=f"Got it! You also want {pizza_type}.")
        return result

    def validate_pizza_type(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> Dict[Text, Any]:
        """Validate 'pizza_type' value"""

        if slot_value.lower() not in ALLOWED_PIZZA_TYPES:
            dispatcher.utter_message(text=f"I don't recognize that pizza. we serve: {','.join(ALLOWED_PIZZA_TYPES)}.")
            return {"pizza_type": None}
        dispatcher.utter_message(text=f"OK! You want to have a {slot_value} pizza.")
        return {"pizza_type": slot_value}

# Reset the values of the slots 'pizza_type' and 'pizza_size' - after the form is close    
class ActionResetPizzaSlots(Action):
    def name(self) -> Text:
        return "action_reset_pizza_slots"

    def run(self, dispatcher, tracker, domain):
        return [
            SlotSet("pizza_size", None),
            SlotSet("pizza_type", None)
        ]

class ActionDeactivateLook(Action):
    def name(self) -> Text:
        return "action_deactivate_loop"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="Okay, I stopped the form.")
        return [ActiveLoop(None)]

class AskForVegetarianAction(Action):
    def name(self) -> Text:
        return "action_ask_vegetarian"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> Dict[Text, Any]:
        dispatcher.utter_message(text="Would you like to order a vegetarian pizza?",
            buttons=[{"title": "yes", "payload": "/affirm"}, {"title": "no", "payload": "/deny"}])
        return []
    
class ValidateFancyPizzaForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_fancy_pizza_form"

    def validation_vegetarian(self, alot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> Dict[Text, Any]:
        """ Validate 'pizza_size' value."""
        if tracker.get_intent_of_latest_message() == "affirm":
            dispatcher.utter_message(text="I'll remember you prefer vegetarian.")
            return {"vegetarian": True}
        if tracker.get_intent_of_latest_message() == "deny":
            dispatcher.utter_message(text="I'll remember you DON'T want a vegetarian pizza.")
            return {"vegetarian": False}
        dispatcher.utter_message(text="I didn't get that.")
        return {"vegetarian": None}

    def validate_pizza_size(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> Dict[Text, Any]:
        """Validate 'pizza_size' value"""

        if slot_value.lower() not in ALLOWED_PIZZA_SIZES:
            dispatcher.utter_message(text=f"We only accept pizza sizes: s/m/l/xl.")
            return {"pizza_size": None}
        dispatcher.utter_message(text=f"OK! You want to have a {slot_value} pizza.")
        # Multi-slot capture for pizza_type in the same message
        pizza_type = next(tracker.get_latest_entity_values("pizza_type"), None)
        result = {"pizza_size": slot_value}
        if pizza_type and pizza_type.lower() in ALLOWED_PIZZA_TYPES:
            result["pizza_type"] = pizza_type
            dispatcher.utter_message(text=f"Got it! You also want {pizza_type}.")
        return result

class AskFroPizzaTypeAction(Action):
    def name(self) -> Text:
        return "action_ask_pizza_type"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> Dict[Text, Any]:
        if tracker.get_slot("vegetarian"):
            dispatcher.utter_message(text=" what kind of pizza do you want?",
                buttons=[{"title": p, "payload": p} for p in VEGETARIAN_PIZZAS])
        elif tracker.get_slot("vegetarian") == False:
            dispatcher.utter_message(text=" what kind of pizza do you want?",
                buttons=[{"title": p, "payload": p} for p in MEAT_PIZZAS])
        else:
            dispatcher.utter_message(text=" what kind of pizza do you want to buy?")
        return []