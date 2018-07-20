
# coding: utf-8

# In[1]:


#Python libraries that we need to import for our bot
import sys
sys.path.append('C:\\Users\\126266\\AppData\\Local\\Programs\\Python\\Python36-32\\Lib\\site-packages')
import os
from flask import Flask, request
#from fbmessenger import BaseMessenger
#from fbmessenger import quick_replies
#from fbmessenger import *
#from fbmessenger.elements import Text
#from fbmessenger.thread_settings import GreetingText, GetStartedButton, MessengerProfile
from fbmq import *
get_ipython().magic('run fonctionsAPI.ipynb')
get_ipython().magic('run parameters_chatbot.ipynb')
#%run appelApiMSW.ipynb



i=0 #i est utilisé pour savoit où on se trouve dans l'arbre de décision
sport=str()
randomAnswer,listeSpot = liste_spot_bot() #on initialise la liste des spots qui seront utilisés
#minWaveHeight=0 #hauteur vague mini en metres
#minPeriod=0 #Periode vague mni en seconds
#windMin=5 #min kite wind speed in knts

#List of the spots available for quick replies
quick_replies = []
list_options=[]
reponse,listeSpot = liste_spot_bot()

for a in listeSpot:
    quick_replies.append(fbmq.QuickReply(title=a.nomSpot, payload="PICK_"+a.nomSpot.upper()))

list_options=[
    fbmq.QuickReply(title="Surf", payload="SURF"),
    fbmq.QuickReply(title="Kitesurf", payload="KITESURF"),
]
    
#FB tokens for communication and verifications
FB_PAGE_TOKEN = 'EAAXAUtKxWnUBAG3DqlaKQ7yMoTVHd72r2ZC0mbyl73iqhhK4tEfZB0FoPnIH5IqUHZCOrIZBZC2whHauOQCpMyFdbrVNDOEqBMuYZALREAnyIy1UcHzzrMTHqy5iJunCTVsYqKvKeXvsm0yDlWyy9UZCYRXCZCtPbodufbwvneZCnFwZDZD'
FB_VERIFY_TOKEN = 'coucoulesloulous'


#Definition of the chatbot
page = Page(FB_PAGE_TOKEN)





##Flask App
app = Flask(__name__)

@app.route('/', methods=['GET'])
def validate():
    if request.args.get('hub.mode', '') == 'subscribe' and                     request.args.get('hub.verify_token', '') == FB_VERIFY_TOKEN:

        print("Validating webhook")

        return request.args.get('hub.challenge', '')
    else:
        return 'Failed validation. Make sure the validation tokens match.'



@app.route("/", methods=['POST'])

def webhook():
  page.handle_webhook(request.get_data(as_text=True))
  return "ok"

@page.handle_message
def message_handler(event):
    """:type event: fbmq.Event"""
    global i
    global listeSpot
    global minWaveHeight
    global minPeriod
    global windMin
    global quick_replies
    global list_options
    global sport
    
    sender_id = event.sender_id
    message = event.message_text
    answer=0
    
    
    #page.send(sender_id, "thank you! your message is '%s'" % message)
    
    #We start by assigning sport depending on the message
    if message=="Surf" or message=="Kitesurf":
        answer=1
        sport=message
        page.send(sender_id, 
                  "Quel spot t'intéresse ?",
                  quick_replies=quick_replies,
                  metadata="DEVELOPER_DEFINED_METADATA")
        
    if answer==0:
        #If no sport selected, need to ask what sport to be selected
        if sport!="Surf" and sport!="Kitesurf":
            answer=1
            page.send(sender_id, "Quel sport veux tu faire aujourd'hui ?",
                      quick_replies=list_options,
                      metadata="DEVELOPER_DEFINED_METADATA")
        
                        
    #If the user sends a spot name, we reply with the forecast for the spot based on the applicable sport
    if answer==0:
        for a in listeSpot:
                if message==a.nomSpot:#Le message envoyé est le nom du spot
                    answer=1
                    spotChoisi=a
                    forecastMSW=get_forecast_MSW(spotChoisi.idSpot)  #Télécharment données spot
                    reponse = prochaine_bonne_session_bot(spotChoisi,forecastMSW,minWaveHeight,minPeriod,windMin,sport) #Envoi du forecast prochaine bonne session

                    page.send(sender_id, reponse)
                
                
    #Otherwise we suggest a list of sport
    if answer==0:
        page.send(sender_id, "Quel sport veux tu faire aujourd'hui ?",
          quick_replies=list_options,
          metadata="DEVELOPER_DEFINED_METADATA")
    
    print("le message est {} et le sport choisi est {}".format(message,sport))     
    

@page.after_send
def after_send(payload, response):
  """:type payload: fbmq.Payload"""
  print("complete")

@page.callback(['PICK_ACTION', 'PICK_COMEDY'])
def callback_picked_genre(payload, event):
  print(payload, event)
 
if __name__ == '__main__':
    app.run()

    
    ##Ngrok relancer ngrok et modifier l'adresse de redirection dans les paramètres Facebook (adresse https):https://developers.facebook.com/apps/1618836838242933/messenger/settings/
    


# In[8]:




