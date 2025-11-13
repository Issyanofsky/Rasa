<div align="center">

# **Custom Forms (Slot filling)**
</div>

Custom forms let you handle unexpected user answers and create more flexible, dynamic conversations by controlling exactly how and when slots are asked, validated, or skipped. makes the  conversations flexible, letting you handle surprises and guide users dynamically.

## Examples of dealing with Un-Happy path

### 1. Here the conversation is disturbed by asking out of the form questions - we want to answer it and go back to fill the form:

![Pipline & Policy](../images/custom_froms1100.gif)

To do this we configure an extra __Rule__:
```yaml
    - rule: Interruption in Pizza Form
      condition:
      # Condition that form is active
      - active_loop: simple_pizza_form
      steps:
      # The case of an intent 'bot_challenge'
      - intent: bot_challenge
      - action: utter_iababot
      # Return to form
      - action: simple_pizza_form
      - active_loop: simple_pizza_form
```
This rule triggered if only if the form was interupted (active_loop). and there is an intent (bot_challenge) that follow by the action (utter_iamabot). that will answer the intrupt question. once is done, we mention that the form is active and continue from there ( action: simple_pizza_form and active_loop: simple_pizza_form)

__*note__ in order for it to work you have to add intent (bot_challenge).

### 2. Stoping the form if the user ask - canceling the form

![Pipline & Policy](../images/custom_froms1101.gif)

we want not just stopping the form but also to get the user confirm. the best way of doing it its by stories (you need more then one). rules cant apply here becouse they build for __one__ set at a time while here we need more then one (intent: stop) and he confirmation (ontent: stop and affirm)

```yaml
    - story: User don't want tp continue form
      steps:
      - intent: greet
      - action: utter_greet
      - intent: buy_pizza
      - action: simple_pizza_form
      - active_loop: simple_pizza_form
      - intent: stop
      - action: utter_ask_continue
      - or:
        - intent: stop
        - intent: affirm
      - action: action_deactivate_loop
      - action_loop: null
```
for better learnign its recommended to add more stories:
```yaml
    - story: User interrupts the form and doesn't want to continue
        steps: 
        - intent: greet
        - action: utter_greet
        - intent: buy_pizza
        - action: simple_pizza_form
        - active_loop: simple_pizza_form
        - intent: stop
        - action: utter_ask_continue
        - or:
            - intent: stop
            - intent: affirm
        - action: action_deactivate_loop
        - active_loop: null

    - story: interactive story 2
        steps:
        - intent: greet
        - action: utter_greet
        - intent: buy_pizza
        - action: simple_pizza_form
        - active_loop: simple_pizza_form
        - slot_was_set:
            - requested_slot: pizza_size
        - intent: stop
        - action: utter_ask_continue
        - intent: stop
        - action: action_deactivate_loop
        - active_loop: null
        - slot_was_set: 
            - requested_slot: null
        - intent: goodbye
        - action: utter_goodbye
        
    - story: interactive story 3
        steps:
        - intent: greet
        - action: utter_greet
        - intent: buy_pizza
        - action: simple_pizza_form
        - active_loop: simple_pizza_form
        - slot_was_set:
            - requested_slot: pizza_size
        - slot_was_set:
            - pizza_size: s
        - slot_was_set:
            - requested_slot: pizza_type
        - intent: stop
        - action: utter_ask_continue
        - intent: affirm
        - action: action_deactivate_loop
        - active_loop: null
        - slot_was_set:
            - requested_slot: null
        - intent: goodbye
        - action: utter_goodbye

    - story: interactive story 4
        steps:
        - intent: greet
        - action: utter_greet
        - intent: buy_pizza
        - action: simple_pizza_form
        - active_loop: simple_pizza_form
        - slot_was_set:
            - requested_slot: pizza_size
        - intent: stop
        - action: utter_ask_continue
        - intent: affirm
        - action: action_deactivate_loop
        - active_loop: null
        - slot_was_set:
            - requested_slot: null
        - intent: buy_pizza
        - action: simple_pizza_form
        - active_loop: simple_pizza_form
        - slot_was_set:
            - requested_slot: pizza_size
         - slot_was_set:
             - pizza_size: large
         - slot_was_set:
             - pizza_size: large
         - slot_was_set:
            - requested_slot: pizza_type
         - slot_was_set:
             - pizza_size: pepperoni
         - slot_was_set:
             - pizza_size: pepperoni            
         - slot_was_set:
             - requested_slot: null
         - active_loop: null
         - action: utter_submit
         - action: utter_pizza_slots

    - story: interactive story 5
        steps:
        - intent: greet
        - action: utter_greet
        - intent: buy_pizza
        - action: simple_pizza_form
        - active_loop: simple_pizza_form
        - slot_was_set:
            - requested_slot: pizza_size
        - intent: bot_challange
        - action: utter_iamabot
        - action: simple_pizza_form
        - slot_was_set:
            - requested_slot: pizza_size
        - intent: stop
        - action: utter_ask_continue
        - intent: affirm
        - action: action_deactivate_loop
        - active_loop: null
        - slot_was_set:
            - requested_slot: null
        - intent: goodbye
        - action: utter_goodbye
```

### 3. Unintended Slots
There are cases where the assistant may fill a slot not related ( confusing medium to be the pizza size).
In cases like this you need to define the slots not to aquiere entites if they out-side the form entering (note that there are cases you want the conversation to fill slots even if they appear out-side the form loop)


![Pipline & Policy](../images/custom_froms1102.gif)
