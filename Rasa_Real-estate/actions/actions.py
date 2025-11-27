from typing import Any, Dict, Text, List
from rasa_sdk import Action, Tracker
from rasa_sdk import FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import FollowupAction, AllSlotsReset, ActiveLoop, SessionStarted, ActionExecuted, SlotSet, UserUttered, EventType
import re   # added regex for parsing free text price ranges
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
# Get the secrets from environment variables
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

##############################
# Fallback Action
##############################

class ActionHandleFallback(Action):
    def name(self) -> str:
        return "action_handle_fallback"

    def run(self, dispatcher, tracker, domain):
        # Get the fallback intent and handle it
        dispatcher.utter_message(text="Sorry, I didn't understand that. Can you please rephrase?")
        return []


##############################
# Action on start - set the buttons on starting the conversation
##############################
# (ActionSessionStart remains unchanged)
class ActionSessionStart(Action):
    def name(self) -> Text:
        return "action_session_start"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        # 1. Start session
        events = [SessionStarted()]

        # 2. Trigger the welcome action
        # events.append(FollowupAction("action_welcome_message"))

        # 3. Let Rasa listen
        events.append(ActionExecuted("action_listen"))
        return events

class ActionWelcomeMessage(Action):
    def name(self) -> Text:
        return "action_welcome_message"

    def run(self, dispatcher, tracker, domain):
        
        dispatcher.utter_message(
            text="Welcome to the service! Please select an option to begin.",
            buttons=[
                {"title": "Rent a property", "payload": "/rent_property"},
                {"title": "Buy a property", "payload": "/buy_property"},
                {"title": "Sell a property", "payload": "/sell_property"},
                {"title": "Book Appointment", "payload": "/show_appointment_options"},
                {"title": "Filing a complaint", "payload": "/file_complaint"},
                {"title": "Maintenance issue", "payload": "/maintenance_issue"},
                {"title": "Company Info", "payload": "/ask_info_type"},
            ]
        )

        return []


##############################
# Validate Form - property
##############################
class ValidatePropertyInfoForm(FormValidationAction):

    def name(self) -> Text:
        return "validate_property_info_form"

    # -----------------------------------------
    # CONSTANTS
    # -----------------------------------------
    VALID_CITIES = ["cancun", "tulum", "playa del carmen"]
    VALID_PROPERTY_TYPES = ["apartment", "house", "office", "land", "store", "warehouse", "hotel"]
    ROOM_TYPES = ["apartment", "house", "hotel"]
    AREA_TYPES = ["land", "office", "warehouse", "store"]

    # -----------------------------------------
    # HELPER METHOD: Normalize Input
    # -----------------------------------------
    def normalize_input(self, value: Text) -> Text:
        print(f"[DEBUG] Normalizing input: '{value}'")
        return str(value).strip().lower()

    # -------------------------------------------------------------
    # CITY VALIDATION (Robust: Already handles non-list input by failing validation)
    # -------------------------------------------------------------
    def validate_city(self, value: Text, dispatcher, tracker, domain: DomainDict) -> Dict[Text, Any]:
        print(f"[DEBUG] Validating city with value: {value}")

        value = self.normalize_input(value)
        print(f"[DEBUG] Normalized city value: '{value}'")

        if value in ["stop", "cancel"]:
            dispatcher.utter_message(text="Okay, stopping")
            return {"city": None}

        if value in self.VALID_CITIES:
            dispatcher.utter_message(text=f"Okay, looking in {value.title()}.")
            return {"city": value}

        dispatcher.utter_message(
            text=f"Sorry, we support only: {', '.join(self.VALID_CITIES)}. Please choose one.")
        return {"city": None}

    # -------------------------------------------------------------
    # PROPERTY TYPE VALIDATION (Robust)
    # -------------------------------------------------------------
    def validate_property_type(self, value: Text, dispatcher, tracker, domain: DomainDict) -> Dict[Text, Any]:
        print(f"[DEBUG] Validating property type with value: {value}")
        value = self.normalize_input(value)

        if value in self.VALID_PROPERTY_TYPES:
            dispatcher.utter_message(text=f"Searching for a {value}.")
            return {"property_type": value}

        dispatcher.utter_message(text=f"I didn't quite catch the property type. Please specify one from: {', '.join(self.VALID_PROPERTY_TYPES)}.")
        return {"property_type": None}

    # -------------------------------------------------------------
    # PRICE RANGE VALIDATION (FORTIFIED against non-numeric gibberish)
    # -------------------------------------------------------------
    def validate_price_min(self, value: Any, dispatcher, tracker, domain: DomainDict) -> Dict[Text, Any]:
        print(f"[DEBUG] Validating price_min with value: {value}")
        price_min, price_max = None, None

        # 1. Try to extract entities normally (from NLU)
        entities = tracker.latest_message.get("entities", [])
        for e in entities:
            try:
                if e.get("entity") == "price_min":
                    price_min = float(e.get("value"))
                if e.get("entity") == "price_max":
                    price_max = float(e.get("value"))
            except (ValueError, TypeError):
                print(f"[DEBUG] NLU entity for price could not be converted to float: {e.get('value')}")
                continue

        print(f"[DEBUG] Extracted entities: price_min={price_min}, price_max={price_max}")

        # 2. If NLU failed, try to parse numbers from free text with regex
        if price_min is None or price_max is None:
            msg = tracker.latest_message.get("text", "").lower()
            numbers = re.findall(r"\d+", msg)

            if len(numbers) >= 2:
                try:
                    price_min = float(numbers[0])
                    price_max = float(numbers[1])
                except (ValueError, TypeError):
                    dispatcher.utter_message(text="Sorry, I could not understand the price range. Please provide valid numbers.")
                    return {"price_min": None, "price_max": None}

        print(f"[DEBUG] Final extracted price_min={price_min}, price_max={price_max}")

        # 3. Final Validation: Ensure both values are positive
        if price_min is None or price_max is None:
            dispatcher.utter_message(text="Please provide a full price range (e.g., 800 to 1200) using only numbers.")
            return {"price_min": None, "price_max": None}

        if price_min < 0 or price_max < 0:
            dispatcher.utter_message(text="Prices cannot be negative. Please enter a valid range.")
            return {"price_min": None, "price_max": None}

        # Ensure price_min <= price_max
        if price_max < price_min:
            price_min, price_max = price_max, price_min
            dispatcher.utter_message(text="Swapping values: Minimum price should be less than or equal to maximum price.")

        # 4. Return valid values
        return {"price_min": price_min, "price_max": price_max}

    # -------------------------------------------------------------
    # PROPERTY DESCRIPTION VALIDATION (FORTIFIED to ensure `value` is a string)
    # -------------------------------------------------------------
    def validate_property_description(self, value: Text, dispatcher, tracker, domain: DomainDict) -> Dict[Text, Any]:
        print(f"[DEBUG] Validating property description with value: {value}")
        property_type = tracker.get_slot("property_type")
        value = self.normalize_input(value)

        # Handle non-string values gracefully
        if not isinstance(value, str):
            dispatcher.utter_message(text="Please provide a valid description.")
            return {"property_description": None}

        print(f"[DEBUG] Validating property description for property_type: {property_type}")

        # Validate based on property type
        if property_type in self.ROOM_TYPES:
            if any(word in value for word in ["room", "bedroom", "rooms", "bedrooms"]):
                return {"property_description": value}

            dispatcher.utter_message(text="For this property type, please include the number of rooms or bedrooms (e.g., '3 rooms').")
            return {"property_description": None}

        if property_type in self.AREA_TYPES:
            if any(unit in value for unit in ["sqm", "square meter", "square meters", "m2"]):
                return {"property_description": value}

            dispatcher.utter_message(text="For this property type, please include the area in square meters (e.g., '500 sqm').")
            return {"property_description": None}

        return {"property_description": value}  # Default case, accept any description

#####################################
# Cancel Form and reset it 
#####################################
# (ActionCancelForm remains unchanged)
class ActionCancelForm(Action):
    def name(self) -> Text:
        return "action_cancel_form"

    async def run(
        self, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain: Dict[Text, Any]
    ) -> list:
        # Stop active form
        dispatcher.utter_message(text="Form canceled. All information cleared.")
        return [
            ActiveLoop(None),  # deactivate any active form
            SlotSet("property_type", None), 
            SlotSet("city", None),
            SlotSet("price_min", None),
            SlotSet("price_max", None),
            SlotSet("property_description", None),
            SlotSet("data_type", None),
            FollowupAction("action_welcome_message")  # Ensure session is started after cancel
        ]



#####################################
# Retive properties From Excel
#####################################
# ======================================================
#                  CONSTANTS
# ======================================================

FILE_MAP = {
    "rent": r"C:\Users\ec\Documents\Rasa\real-estate\code\rent_property_list.xlsx",
    "buy": r"C:\Users\ec\Documents\Rasa\real-estate\code\buy_properties.xlsx",
}

SHEET_NAME1 = 'sheet1'

ID_COLUMN = "ID"
TYPE_COLUMN = "Type"
CITY_COLUMN = "City"
PRICE_COLUMN = "Price (MXN)"
DESCRIPTION_COLUMN = "Description"
# ======================================================


class ActionSearchProperties(Action):

    def name(self) -> Text:
        return "action_search_properties"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        # ======================================================
        #               GET SLOT VALUES
        # ======================================================
        property_type = tracker.get_slot("property_type")
        city = tracker.get_slot("city")
        price_min = tracker.get_slot("price_min")
        price_max = tracker.get_slot("price_max")
        property_description = tracker.get_slot("property_description")

        # NEW: dynamic file selection
        data_type = tracker.get_slot("data_type") or "rent"
        excel_file = FILE_MAP.get(data_type, FILE_MAP["rent"])


        # ======================================================
        #               LOAD EXCEL FILE
        # ======================================================
        if not os.path.exists(excel_file):
            dispatcher.utter_message(
                text=f"⚠ The database file was not found:\n`{excel_file}`"
            )
            return []

        try:
            df = pd.read_excel(excel_file, sheet_name=SHEET_NAME1)
        except Exception as e:
            dispatcher.utter_message(text=f"⚠ Failed to read Excel file: {e}")
            return []

        # ======================================================
        #               FILTER PROPERTIES
        # ======================================================
        df_filtered = df.copy()

        # Filter by type
        if property_type:
            df_filtered = df_filtered[
                df_filtered[TYPE_COLUMN].str.lower() == property_type.lower()
            ]

        # Filter by city
        if city:
            df_filtered = df_filtered[
                df_filtered[CITY_COLUMN].str.lower() == city.lower()
            ]

        # Filter by price range
        if price_min:
            df_filtered = df_filtered[df_filtered[PRICE_COLUMN] >= float(price_min)]

        if price_max:
            df_filtered = df_filtered[df_filtered[PRICE_COLUMN] <= float(price_max)]

        # Filter by description contains
        # if property_description:
        #     df_filtered = df_filtered[
        #         df_filtered[DESCRIPTION_COLUMN]
        #         .astype(str)
        #         .str.contains(property_description, case=False, na=False)
        #     ]

        # ======================================================
        #               NO RESULTS FOUND
        # ======================================================
        if df_filtered.empty:
            dispatcher.utter_message(
                text="❌ No properties found that match your search criteria. Would you like to meet with an agent who will help you find what you're looking for?"
            )
            return []

        # ======================================================
        #               FORMAT RESULTS
        # ======================================================

        # Check number of properties found
        num_properties = len(df_filtered)
        
        if num_properties > 5:
            # Limit the results to 5 if more than 5 properties found
            df_filtered = df_filtered.head(5)  # Marked line: limit to 5

        # Store the results in the tracker slot for future use
        # You can store important fields like 'ID', 'Type', 'City' or the entire row data
        property_results = df_filtered[[ID_COLUMN, TYPE_COLUMN, CITY_COLUMN, PRICE_COLUMN, DESCRIPTION_COLUMN]].to_dict(orient='records')
        # Marked line: store filtered property details in the slot 'property_results'
        tracker.slots["property_results"] = property_results

        # Format the properties to display
        message = f"🔎 We have found {num_properties} properties for {data_type} here are the first 5 properties I found:\n\n"
        
        for _, row in df_filtered.iterrows():
            message += (
                f"🏠 ID: {row[ID_COLUMN]}\n"
                f"• Type: {row[TYPE_COLUMN]}\n"
                f"• City: {row[CITY_COLUMN]}\n"
                f"• Price: {row[PRICE_COLUMN]}\n"
                f"• Description: {row[DESCRIPTION_COLUMN]}\n\n"
            )

        dispatcher.utter_message(text=message)

        # ======================================================
        #               AGENT REMARK MESSAGE
        # ======================================================

        if num_properties > 5:
            # Commercial message for more than 5 properties found
            dispatcher.utter_message(
                text=f"I found a variety of {num_properties} properties. For a better fit, would you like to meet with an agent?"
            )  # Marked line: commercial message for more than 5 properties

        elif num_properties > 0:
            # Commercial message for less than 5 properties found
            dispatcher.utter_message(
                text=f"Found {num_properties} properties in the database. We have additional properties to offer you that are not in the database. Would you like to meet with an agent who will help you find what you're looking for?"
            )  # Marked line: commercial message for less than 5 properties

        return [SlotSet("property_results", property_results)]
    

#####################################
# Meeting action's Form
#####################################    
class ActionSetCallbackPurpose(Action):
    def name(self) -> Text:
        return "action_set_callback_purpose"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> list:
        return [SlotSet("meeting_purpose", "callback")]

class ActionSetMeetingPurpose(Action):
    def name(self) -> Text:
        return "action_set_meeting_purpose"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> list:
        return [SlotSet("meeting_purpose", "meeting")]
    
class ActionSetSellPurpose(Action):
    def name(self) -> Text:
        return "action_set_sell_purpose"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> list:
        return [SlotSet("meeting_purpose", "sell")]

class ActionSetFileComplaintPurpose(Action):
    def name(self) -> Text:
        return "action_set_file_complaint_purpose"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> list:
        return [SlotSet("meeting_purpose", "complaint")]

class ActionSetMaintenancePurpose(Action):
    def name(self) -> Text:
        return "action_set_maintenance_purpose"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> list:
        return [SlotSet("meeting_purpose", "maintenance")]

               
# Form validatin 
#####################################    
class ValidateUserInfoForm(FormValidationAction):

    def name(self) -> Text:
        return "validate_user_info_form"
    
    # -------------------------------------------------------
    # Dynamic Required Slots
    # -------------------------------------------------------
    async def required_slots(
        self,
        slots_mapped_in_domain: List[Text],
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Text]:

        purpose = tracker.get_slot("meeting_purpose")
        base_slots = ["user_name", "user_phone", "user_email"]

        if purpose == "meeting":
            return base_slots + ["meeting_time"]
        if purpose in ["sell", "complaint", "maintenance"]:
            return base_slots + ["meeting_free_text"]
        return base_slots

    # -------------------------------------------------------
    # user_name extraction + validation
    # -------------------------------------------------------
    def extract_user_name(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:
    
        # Only extract if this is the currently requested slot
        if tracker.get_slot("requested_slot") != "user_name":
            return {}

        slot_value = tracker.latest_message.get("text")
        if slot_value and slot_value.strip():
            return {"user_name": slot_value.strip()}

        return {}

        # if tracker.get_slot("user_name") is not None:
        #     return {}

        # text = tracker.latest_message.get("text")
        # if text and text.strip():
        #     return {"user_name": text.strip()}
    
        # # Return nothing if user didn't type anything
        # return {}

    def validate_user_name(
        self, slot_value: Any, dispatcher: CollectingDispatcher,
        tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:
        # Extract latest intent safely
        intent = tracker.latest_message.get("intent", {}).get("name")

        # 1️⃣ Cancel on "cancel" or "stop"
        if intent in ["cancel", "stop"]:
            dispatcher.utter_message(text="Form canceled. Starting over.")

            # Clear ALL slots (including those outside the form)
            return {
                "user_name": None,
                "user_phone": None,
                "user_email": None,
                "meeting_time": None,
                "meeting_purpose": None,
                "meeting_free_text": None,
                "requested_slot": None,
                "form_cancelled": True
            }
        
        pattern = r"^[A-Za-z]+ [A-Za-z]+$"

        if slot_value and re.fullmatch(pattern, slot_value.strip()):
            return {"user_name": slot_value.title()}

        # Retrieve the requested_slot and the value of the user_name slot
        requested_slot = tracker.get_slot("requested_slot")
        user_name = tracker.get_slot("user_name")

        if requested_slot == "user_name" and user_name is not None:
            dispatcher.utter_message(text="Please enter your full name (e.g., John Doe).")
        return {"user_name": None}

    # -------------------------------------------------------
    # user_phone extraction + validation
    # -------------------------------------------------------
    def extract_user_phone(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:

        # Only extract if this is the currently requested slot
        if tracker.get_slot("requested_slot") != "user_phone":
            return {}

        slot_value = tracker.latest_message.get("text")
        if slot_value and slot_value.strip():
            return {"user_phone": slot_value.strip()}

        return {}
    
        # # Only extract if this is the currently requested slot
        # if tracker.get_slot("requested_slot") != "user_phone":
        #     return {}

        # slot_value = tracker.latest_message.get("text")
        # if slot_value and slot_value.strip():
        #     return {"user_phone": slot_value.strip()}

        # return {}
    
        # if tracker.get_slot("user_phone") is not None:
        #     return {}
        # text = tracker.latest_message.get("text")
        # if text and text.strip():
        #     return {"user_phone": text.strip()}
    
        # # Return nothing if user didn't type anything
        # return {}

    def validate_user_phone(
        self, slot_value: Any, dispatcher: CollectingDispatcher,
        tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:
        # Extract latest intent safely
        intent = tracker.latest_message.get("intent", {}).get("name")

        # 1️⃣ Cancel on "cancel" or "stop"
        if intent in ["cancel", "stop"]:
            dispatcher.utter_message(text="Form canceled. Starting over.")

            # Clear ALL slots (including those outside the form)
            return {
                "user_name": None,
                "user_phone": None,
                "user_email": None,
                "meeting_time": None,
                "meeting_purpose": None,
                "meeting_free_text": None,
                "requested_slot": None,
                "form_cancelled": True
            }
        
        pattern = r"^\+?\d[\d\- ]{7,15}$"
        if slot_value and re.fullmatch(pattern, slot_value.strip()):
            return {"user_phone": slot_value}
        
        # Retrieve the requested_slot and the value of the user_name slot
        requested_slot = tracker.get_slot("requested_slot")
        user_name = tracker.get_slot("user_phone")
                
        if requested_slot == "user_phone" and user_name is not None:
            dispatcher.utter_message(text="This doesn't look like a valid phone number.")
        return {"user_phone": None}

    # -------------------------------------------------------
    # user_email extraction + validation
    # -------------------------------------------------------
    def extract_user_email(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:

        # Only extract if this is the currently requested slot
        if tracker.get_slot("requested_slot") != "user_email":
            return {}

        slot_value = tracker.latest_message.get("text")
        if slot_value and slot_value.strip():
            return {"user_email": slot_value.strip()}

        return {}
    
        # # Only extract if this is the currently requested slot
        # if tracker.get_slot("requested_slot") != "user_email":
        #     return {}

        # slot_value = tracker.latest_message.get("text")
        # if slot_value and slot_value.strip():
        #     return {"user_email": slot_value.strip()}

        # return {}
    
        # if tracker.get_slot("user_email") is not None:
        #     return {}
        # text = tracker.latest_message.get("text")
        # if text and text.strip():
        #     return {"user_email": text.strip()}
    
        # # Return nothing if user didn't type anything
        # return {}

    def validate_user_email(
        self, slot_value: Any, dispatcher: CollectingDispatcher,
        tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:

        # Extract latest intent safely
        intent = tracker.latest_message.get("intent", {}).get("name")

        # 1️⃣ Cancel on "cancel" or "stop"
        if intent in ["cancel", "stop"]:
            dispatcher.utter_message(text="Form canceled. Starting over.")

            # Clear ALL slots (including those outside the form)
            return {
                "user_name": None,
                "user_phone": None,
                "user_email": None,
                "meeting_time": None,
                "meeting_purpose": None,
                "meeting_free_text": None,
                "requested_slot": None,
                "form_cancelled": True
            }        

        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if slot_value and re.fullmatch(pattern, slot_value.strip()):
            return {"user_email": slot_value}
        
        # Retrieve the requested_slot and the value of the user_name slot
        requested_slot = tracker.get_slot("requested_slot")
        user_name = tracker.get_slot("user_email")
                
        if requested_slot == "user_email" and user_name is not None:
            dispatcher.utter_message(text="Please provide a valid email address.")
        return {"user_email": None}

    # -------------------------------------------------------
    # meeting_time extraction + validation
    # -------------------------------------------------------
    def extract_meeting_time(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:

        # Only extract if this is the currently requested slot
        if tracker.get_slot("requested_slot") != "meeting_time":
            return {}

        slot_value = tracker.latest_message.get("text")
        if slot_value and slot_value.strip():
            return {"meeting_time": slot_value.strip()}

        return {}
    
        # Only extract if this is the currently requested slot
        # if tracker.get_slot("requested_slot") != "meeting_time":
        #     return {}

        # slot_value = tracker.latest_message.get("text")
        # if slot_value and slot_value.strip():
        #     return {"meeting_time": slot_value.strip()}

        # return {}

        # if tracker.get_slot("meeting_time") is not None:
        #     return {}
        # text = tracker.latest_message.get("text")
        # if text and text.strip():
        #     return {"meeting_time": text.strip()}
    
        # # Return nothing if user didn't type anything
        # return {}

    def validate_meeting_time(
        self, slot_value: Any, dispatcher: CollectingDispatcher,
        tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:
        
        # Extract latest intent safely
        intent = tracker.latest_message.get("intent", {}).get("name")

        # 1️⃣ Cancel on "cancel" or "stop"
        if intent in ["cancel", "stop"]:
            dispatcher.utter_message(text="Form canceled. Starting over.")

            # Clear ALL slots (including those outside the form)
            return {
                "user_name": None,
                "user_phone": None,
                "user_email": None,
                "meeting_time": None,
                "meeting_purpose": None,
                "meeting_free_text": None,
                "requested_slot": None,
                "form_cancelled": True
            }

        if not slot_value:
            return {"meeting_time": None}
        date_pattern = r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b"
        time_pattern = r"\b\d{1,2}:\d{2}\b"
        # Find all matches
        dates = re.findall(date_pattern, slot_value)
        times = re.findall(time_pattern, slot_value)

        if dates or times:
            # Combine all matches into one string
            combined = " ".join(dates + times)
            return {"meeting_time": combined}
        
        # Retrieve the requested_slot and the value of the user_name slot
        requested_slot = tracker.get_slot("requested_slot")
        user_name = tracker.get_slot("meeting_time")
                
        if requested_slot == "meeting_time" and user_name is not None:
            dispatcher.utter_message(text="I couldn't understand that date/time. Try '25/11 14:00'.")
        return {"meeting_time": None}

    # -------------------------------------------------------
    # Free Text extraction + validation
    # -------------------------------------------------------
    def extract_meeting_free_text(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:
        # Only extract if this is the currently requested slot
        if tracker.get_slot("requested_slot") != "meeting_free_text":
            return {}

        slot_value = tracker.latest_message.get("text")
        if slot_value and slot_value.strip():
            return {"meeting_free_text": slot_value.strip()}

        return {}
 
        # if tracker.get_slot("meeting_free_text") is not None:
        #     return {}
        # text = tracker.latest_message.get("text")
        # if text and text.strip():
        #     return {"meeting_free_text": text.strip()}

        # # Return nothing if user didn't type anything
        # return {}
    
    def validate_meeting_free_text(
        self, slot_value: Any, dispatcher: CollectingDispatcher,
        tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:

        # Extract latest intent safely
        intent = tracker.latest_message.get("intent", {}).get("name")

        # 1️⃣ Cancel on "cancel" or "stop"
        if intent in ["cancel", "stop"]:
            dispatcher.utter_message(text="Form canceled. Starting over.")

            # Clear ALL slots (including those outside the form)
            return {
                "user_name": None,
                "user_phone": None,
                "user_email": None,
                "meeting_time": None,
                "meeting_purpose": None,
                "meeting_free_text": None,  # Reset the new slot as well
                "requested_slot": None,
                "form_cancelled": True
            }

#        pattern = r"/\S+"  # Match words that start with /

        # Check if slot_value is an Intent
#        if slot_value:
            # Remove words that start with "/" using re.sub
#            cleaned_text = re.sub(pattern, "", slot_value.strip())

            # If cleaned_text is not empty after removing "/words", return the slot value
#            if cleaned_text:
#                return [SlotSet("meeting_free_text", cleaned_text)]

        if slot_value and len(slot_value.strip()) > 0:
            return {"meeting_free_text": slot_value}

        # Retrieve the requested_slot and the value of the meeting_free_text slot
        requested_slot = tracker.get_slot("requested_slot")
        meeting_free_text = tracker.get_slot("meeting_free_text")
        
        if requested_slot == "meeting_free_text" and not meeting_free_text:
            dispatcher.utter_message(text="Please provide some text for the meeting.")
        
        return {"meeting_free_text": None}

# Form After Submit 
#####################################    
class ActionHandleSubmitUserForm(Action):
    def name(self) -> str:
        return "action_handle_submit_user_form"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: dict
    ) -> list[EventType]:

        form_cancelled = tracker.get_slot("form_cancelled")
        meeting_purpose = tracker.get_slot("meeting_purpose")

        # --- User canceled the form ---
        if form_cancelled:
            dispatcher.utter_message(response="utter_welcome_message")
            # Stop the form and reset form_cancelled for next session
            return [
 #               SlotSet("requested_slot", None),
                SlotSet("form_cancelled", False),
                FollowupAction("action_welcome_message")
            ]

        meeting_purpose_responses = {
            "callback": "utter_user_info_callback_confirm",
            "meeting": "utter_user_info_meeting_confirm",
            "sell": "utter_user_info_sell_confirm",  
            "complaint": "utter_user_info_complaint_confirm",  
            "maintenance": "utter_user_info_maintenance_confirm",  
        }

        # --- User completed the form ---
        if meeting_purpose in meeting_purpose_responses:
            dispatcher.utter_message(response=meeting_purpose_responses[meeting_purpose])
        else:
            # Something went wrong → stop the form immediately
            dispatcher.utter_message("Sorry, something went wrong.")
            return [SlotSet("requested_slot", None)]

        # Continue with saving meeting info
        return [FollowupAction("action_save_meeting_info")]

    
#####################################
####### save meeting into an excel
#####################################
# Constants (top of the file)
EXCEL_FILE_PATH = r"C:\Users\ec\Documents\Rasa\real-estate\code\meeting_info.xlsx"
SHEET_NAME = 'Meetings'
COLUMNS = ['date', 'Metting Type', 'Name', 'Phone', 'Email', 'Meeting Time', 'Purpose', 'Property Results', 'Text']

class ActionSaveMeetingInfo(Action):
    def name(self) -> str:
        return "action_save_meeting_info"

    def run(self, dispatcher, tracker, domain) -> list:
        # Retrieve user details
        meeting_type = tracker.get_slot('meeting_purpose')
        name = tracker.get_slot('user_name')
        phone_number = tracker.get_slot('user_phone')
        email = tracker.get_slot('user_email')
        property_results = tracker.get_slot('property_results')
        meeting_time = tracker.get_slot('meeting_time')
        purpose = tracker.get_slot('data_type')
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        meeting_free_text = tracker.get_slot('meeting_free_text')

        # Format property_results
        properties_str = ''
        if property_results:
            for prop in property_results:
                properties_str += f"ID: {prop.get('ID')}, City: {prop.get('City')}, Price: {prop.get('Price (MXN)')}, Description: {prop.get('Description')}\n"

        new_row = [date, meeting_type, name, phone_number, email, meeting_time, purpose, properties_str, meeting_free_text]

        try:
            # If file exists, load it; else create new DataFrame
            if os.path.exists(EXCEL_FILE_PATH):
                df = pd.read_excel(EXCEL_FILE_PATH, sheet_name=SHEET_NAME)
            else:
                df = pd.DataFrame(columns=COLUMNS)

            # Append the new row
            df.loc[len(df)] = new_row

            # Save the dataframe back to Excel
            df.to_excel(EXCEL_FILE_PATH, sheet_name=SHEET_NAME, index=False)

            dispatcher.utter_message(text="Your meeting request has been saved. An agent will contact you soon.")

        except Exception as e:
            dispatcher.utter_message(text=f"Failed to save the meeting info: {e}")

        # Reset slots
        # Get all slot names from the tracker
        slot_names = tracker.slots.keys()

        # Dynamically create SlotSet events to reset each slot to None
        reset_events = [SlotSet(slot_name, None) for slot_name in slot_names]
        return reset_events + [FollowupAction("action_welcome_message")]

#####################################
####### Buy Property 
#####################################

class ActionSetBuyPropertyType(Action):
    def name(self) -> str:
        return "action_set_buy_property_type"

    def run(self, dispatcher, tracker, domain) -> list:
        # Set the slot 'data_type' to 'buy'
        return [SlotSet("data_type", "buy")]
    
##############################
# Contact Info
##############################

class ActionValidateUserEmail(Action):
    def name(self) -> str:
        return "action_validate_user_email"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        """Validate the user_email slot."""
        # Get the current value of the slot from tracker
        slot_value = tracker.get_slot("user_email")
        email_pattern = r"[^@]+@[^@]+\.[^@]+"

        if slot_value and re.match(email_pattern, slot_value):
            # valid email, set the slot (optional, could already be set)
            return [SlotSet("user_email", slot_value)]
        else:
            # invalid email
            dispatcher.utter_message(text="That doesn't look like a valid email. Please try again.")
            return [SlotSet("user_email", None)]

class ActionSendContactEmail(Action):
    def name(self) -> str:
        return "action_send_contact_email"
    def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict,
    ) -> list[EventType]:

        # Get slots from tracker
        recipient = tracker.get_slot("user_email")
        user_name = tracker.get_slot("user_name")

        # Check if recipient email exists
        if not recipient:
            dispatcher.utter_message(text="I need your email to send a message. Please provide it first.")
            return []  # Stop the action if email is missing


        # Email details
        subject = "Maya Real Estate Information"
        # Prepare the email body
        if user_name:
            body = f"""Hello {user_name},

        Maya Real Estate is a trusted property agency serving the vibrant Cancún region of Mexico. 
        We specialize in helping clients find exceptional homes, vacation properties, and investment opportunities 
        tailored to their lifestyle and goals. With local expertise and a commitment to personalized service, 
        Maya Real Estate provides a smooth, reliable experience from property search to closing.

        Here is the contact information:
        You can reach us at support@example.com or +1 234 567 890.

        Best regards,
        The Maya Real Estate Team
        """
        else:
            body = """Maya Real Estate is a trusted property agency serving the vibrant Cancún region of Mexico. 
        We specialize in helping clients find exceptional homes, vacation properties, and investment opportunities 
        tailored to their lifestyle and goals. With local expertise and a commitment to personalized service, 
        Maya Real Estate provides a smooth, reliable experience from property search to closing.

        Here is the contact information:
        You can reach us at support@example.com or +1 234 567 890.

        Best regards,
        The Maya Real Estate Team
        """

        # Create MIME email
        msg = MIMEText(body)
        msg['From'] = EMAIL_USER
        msg['To'] = recipient
        msg['Subject'] = subject

        try:
            # Connect to Gmail SMTP server
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            dispatcher.utter_message(text=f"Email sent successfully to {recipient}!")
        except Exception as e:
            dispatcher.utter_message(text=f"Failed to send email: {str(e)}")
            return [AllSlotsReset(), UserUttered(text="/get_started")]

        return []