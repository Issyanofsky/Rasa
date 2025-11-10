<div align="center">

# **Slots**
</div>

## Slots are your assistant's memory

Slots enable your assistant to store important details and later use them in specific context.

![Slots](../images/slots600.gif)

## Configure slots
Slots are defined inside of the domain.yml file

![Slots](../images/slots601.gif)

The slots includes:
  - __Slots name__ (in the ex."destination")
  - __Slots type__ (in the ex. text)
  - __influence_conversation__ - a parameter describe wheter the slots influence the conversation (in the ex. false).
  - __mappings__ (in the ex. custom).

### There are two main ways how slots can be set in process;
  1. __using NLU__

![Slots](../images/slots602.gif)

depending how you configure the slots mappings. slots can be set using values of the extracting entities. in other cases slots may be set using specific values if a certain intent has been predicted or similar.

  2. __Using custom actions__ (look on page 9 - custom actions).

### Influencing the conversation
Slots can be configured to influence the flow of the conversation. how and when this should happen depends on the type of slot.

![Slots](../images/slots602.gif)

__* Note__ the way slots influence the conversation depends on the type of the slot.

