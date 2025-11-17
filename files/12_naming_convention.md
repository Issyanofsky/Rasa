<div align="center">

# **Rasa 3 Naming Conventions (Quick Reference)**
</div>

This section lists usfull naming patterns that Rasa automatically recognizes.

## 1. Form Validation Class Name

Rasa automatically loads validation classes ONLY if they follow this pattern:
```kotlin
class Validation<FormName>(FormValidationAction):
```
Example"
```python
class ValidationSimplePizzaForm(FormValidationAction):
    ...
```

🔹 Why?
Rasa scans for classes starting with Validation to automatically attach validation to the form.

## 2. Slot Validation Functions

Inside the validation class, each slot must follow this naming pattern:
```php-template
validate_<slot_name>(...)
```
Example:
```python
def validate_pizza_size(self, slot_value, dispatcher, tracker, domain):
    ...
```

🔹 Rasa automatically calls this when a value is mapped to the slot.

## 3. Automatic Slot Asking

Rasa looks for these names when asking for the next slot inside a __Form__:

Default ask action (utterance):
```php-template
utter_ask_<slot_name>
```
Custom action ask handler:
```php-template
action_ask_<slot_name>
```
Example:
```yaml
utter_ask_pizza_type:
  - text: "What pizza type would you like?"
```

🔹 Used every time the form requests a slot value.

__* Note:__
if utter_ask_<slot_name> __exists, Rasa will not trigger__ the action_ask_<slot_name>.
It follow thos priority:
1. If action_ask_<slot_name> __exists → use it__
2. Else if utter_ask_<slot_name> __exists → use it__
3. Else → Rasa uses a fallback, like “What is pizza_type?

## 4. required_slots

Inside the forms section of your domain.yml, you list the slots your form must fill:
```yaml
forms:
  simple_pizza_form:
    required_slots:
      - pizza_size
      - pizza_type
```
What this means:

* The form needs two pieces of information from the user:
    1. pizza_size
    2. pizza_type

* Until both are filled, the form keeps asking questions.

__*Note:__ The order you list them in controls the order of the questions.

## 5. Form Deactivation (stop the form early)

This action name is fixed and must be exactly, Rasa specifically looks for this exact name when stopping a form.:
```nginx
action_deactivate_loop
```
This action __Stop the form. It should no longer ask for slots__ (There is no active form anymore. Turn the form off).

Example:
```python
from rasa_sdk import Action
from rasa_sdk.events import ActiveLoop

class ActionDeactivateLoop(Action):
    def name(self):
        return "action_deactivate_loop"

    def run(self, dispatcher, tracker, domain):
        # This stops the form
        return [ActiveLoop(None)]
```

## 6. Submit Rule Required Names 

When the Form is finishes to submit the form, Rasa expects these __exact keys__ when a form finishes:
```yaml
active_loop: null
slot_was_set:
  - requested_slot: null
```
What they mean:

__1.__ active_loop: null
* Tells Rasa: “__No form is active anymore__”.
* Essentially, it __turns off the form__ .

__2.__ slot_was_set:
* Contains requested_slot: null
* Tells Rasa: “__We are not asking for any more slots__”
* It clears the requested_slot that the form was waiting for.

Both are __mandatory__; if you forget them, the form might __keep running__ or not submit properly.

Example:
```yaml
- rule: Submit Pizza Form
  condition:
    - active_loop: simple_pizza_form
  steps:
    - action: simple_pizza_form
    - active_loop: null
    - slot_was_set:
        - requested_slot: null
    - action: utter_submit
    - action: utter_pizza_slot
```

## 7. Story / Rule Conditions in Rasa Forms

When you write __rules__ or __stories__ for forms, you sometimes need to check the __state of the form__ or __track which slot is being requested__.

Rasa has __special keywords__ for this:

1. slot_was_set:
2. active_loop:

These __cannot be renamed__ — Rasa looks for them exactly.

### 1. slot_was_set

It tracks __slots that have just changed__:
* Inside a form, it’s often used to track requested_slot, e.g., which question is being asked.
* Outside a form, you can use it to __detect when any slot was set__, not just the requested one.

Example (for form):
```yaml
- rule: Ask pizza type only if size is requested
  condition:
    - active_loop: simple_pizza_form
    - slot_was_set:
        - requested_slot: pizza_size
  steps:
    - action: utter_ask_pizza_type
```
Example (outside a form):
```yaml
- rule: Greet after user sets favorite drink
  condition:
    - slot_was_set:
        - favorite_drink: coffee
  steps:
    - action: utter_confirm_drink
```

### 2. active_loop (Form)

Check if a form is currently active.
```yaml
active_loop: simple_pizza_form
```
Tells Rasa: “This rule or step should only apply if the simple_pizza_form is running.”

If no form is running, active_loop would be null (active_loop: null).

This is important to prevent actions from triggering when the form isn’t active.

Example:
```yaml
- rule: Ask pizza type only if size is requested
  condition:
    - active_loop: simple_pizza_form
    - slot_was_set:
        - requested_slot: pizza_size
  steps:
    - action: utter_ask_pizza_type
```
## 8. Events in Python

In Rasa, actions can __return events__ to tell the bot to do something, like fill a slot or start/stop a form.

These __event names are fixed__ — you cannot rename them.

1. __ActiveLoop(None)__ - Stop the current form.
2. __ActiveLoop("form_name")__ - start a form.
3. __SlotSet("slot", value)__ - manually fill a slot (Can be used __inside or outside forms__).
4. __FollowupAction("action_name")__ - Force the next action to run (Can be used __inside or outside forms__).

### 1. ActiveLoop(None)

__Stops__ a form (e.g. canceling the form) that is currently running.

Example:
```python
from rasa_sdk.events import ActiveLoop

return [ActiveLoop(None)]
```

Think of it as __turning off the form “simple_pizza_form”__.

### 2. ActiveLoop("form_name")

__Starts__ a form manually.

Example:
```python
return [ActiveLoop("simple_pizza_form")]
```

Think of it as __activating the form “simple_pizza_form”__ so it starts asking questions.

### 3. SlotSet("slot", value)

__Sets a slot__ to a specific value manually.

Example:
```python
from rasa_sdk.events import SlotSet

return [SlotSet("pizza_size", "large")]
```

Use it when you want to __fill a slot without asking the user__.

### 4. FollowupAction("action_name")

Forces Rasa to run a specific action __next__, no matter what was planned before.

Example:
```python
from rasa_sdk.events import FollowupAction

return [FollowupAction("utter_ask_pizza_type")]
```

It forces the bot to do a specific action, skipping the usual flow.

Useful for:
* Skipping a step in a form
* Triggering a confirmation message right away
* Changing the next action based on some condition

__Example 1 (Skipping a step in a form):__

You have a pizza form with slots: pizza_size, pizza_type, crust_type, toppings.
You want to skip pizza_type and crust_type if the user has already told you some preference.
```python
from rasa_sdk import Action
from rasa_sdk.events import SlotSet, FollowupAction

class ActionSkipToToppings(Action):
    def name(self):
        return "action_skip_to_toppings"

    def run(self, dispatcher, tracker, domain):
        # Skip pizza_type and crust_type
        events = [
            SlotSet("pizza_type", "skipped"),
            SlotSet("crust_type", "skipped"),
            FollowupAction("utter_ask_toppings")  # Jump directly to next slot
        ]
        return events
```
Explanation:
* SlotSet marks skipped slots as filled (to avoid the form may later return to the __missing slots__ (depending on your version and form behavior).
* FollowupAction jumps to the next step in the form.
* Form will complete normally once all required slots have a value.

__Example 2 (Triggering a confirmation message right away):__

__Outside a form__, you want to __send a confirmation message__ after some condition is met.
```python
from rasa_sdk import Action
from rasa_sdk.events import FollowupAction

class ActionCheckOrder(Action):
    def name(self):
        return "action_check_order"

    def run(self, dispatcher, tracker, domain):
        order_complete = tracker.get_slot("order_complete")
        
        if order_complete:
            # Immediately confirm the order
            return [FollowupAction("utter_confirm_order")]
        return []
```
Explanation:
* FollowupAction immediately triggers the utter_confirm_order message.
* Skips any intermediate steps that might normally follow.

__Example 2 (Changing the next action based on some condition):__

You want the bot to __ask for pizza type__ only if the user hasn’t chosen a vegetarian option yet.  
```python
from rasa_sdk import Action
from rasa_sdk.events import FollowupAction

class ActionDecideNextStep(Action):
    def name(self):
        return "action_decide_next_step"

    def run(self, dispatcher, tracker, domain):
        vegetarian = tracker.get_slot("vegetarian")
        
        if vegetarian is True:
            # Skip asking pizza type
            return [FollowupAction("utter_ask_toppings")]
        else:
            # Ask for pizza type
            return [FollowupAction("utter_ask_pizza_type")]
```
Explanation:
* Bot decides dynamically which action to run next, based on slot values or any other condition.
* Very useful for __branching logic__ in conversations.
