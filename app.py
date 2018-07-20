
# coding: utf-8

# In[ ]:


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
#%run fonctionsAPI.ipynb
#%run parameters_chatbot.ipynb
#%run appelApiMSW.ipynb

##Parameters for surf
minWaveHeight=0.9 #hauteur vague mini en metres
minPeriod=8 #Periode vague mni en seconds

##Parameters for kitesurf
windMin=14 #Minimum windspeed to consider in knots

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


import datetime
def unix_to_date(dateUnix):
    '''convertis une date UNIX en date utilisable par un homme'''

    
    return datetime.datetime.fromtimestamp(dateUnix).strftime('%Y-%m-%d %H:%M:%S')


# In[4]:


def get_forecast_MSW(spotId):
    import pickle 
    #On télécharge le forecast à 6 jours pour le spot
    url='http://magicseaweed.com/api/YOURAPIKEY/forecast/?spot_id=YY&units=eu'
    key='a575278d6f20d415fabe8acf110fc2f3'
    secret='cd96e7c2153e00204a91df814352fd0c'
    
    surfUrl=url.replace("YOURAPIKEY",key).replace('YY',spotId)
  
    #On récupère la donnée de l'API
    r = requests.get(surfUrl)
    #On transforme le fichier json en liste contenant des bibliothèques
    data=r.json()

      
    return data


# In[10]:


class surfSpot:
    
    def __init__(self, nomSpot, idSpot, orientationSpot):
        """Constructeur de notre classe"""
        self.nomSpot = nomSpot
        self.idSpot = idSpot
        self.orientationSpot=orientationSpot #Orientation est la direction de la cote quand la mer est àgauche et la terre à droite. En france la cote des landes a une orientation zéro. La cote Est des USA a une orientation proche de 90
        


# In[3]:


import requests
import json  
import datetime

   

def prochaine_bonne_session(spotChoisi,dataMSW,minWaveHeight,minPeriod):
    '''This method will give us the next good surf session date based on a surf spot (surfSpot), the data from MSW for this spot, the minimum wave height the user wants and the min period of wave the user wants'''
    
    data=dataMSW
    
    #On prepare la liste avec les forecast sur chaque date avec la donnée voulue: date, heuteur swell, period swell,sweel direction, witnd power, wind direction
    prevision=list()
    i=0
    while i < len(data):
        prevision.append([datetime.datetime.fromtimestamp(data[i]['localTimestamp']).ctime(),data[i]['swell']['components']["primary"]['height'],data[i]['swell']['components']["primary"]['period'],data[i]['swell']['components']["primary"]['direction'],data[i]['wind']['direction'],data[i]['wind']['speed']])
        i+=1
   

    ##Prevision qualité surf :il faut que vent et vagues  soient d'une certaine taille mini
    hauteurMin=minWaveHeight
    periodeMin=minPeriod


    h=0
    while h < len(prevision):

        if prevision[h][1]>=hauteurMin and prevision[h][2]>=periodeMin:
            prevision[h].append('Bon surf')
        else:
            prevision[h].append('Mauvais surf')
        h=h+1

        
    ## Identifier si le vent sera offshore, onshore, sideshore ou pas de vent
    h=0
    angleSideshore=45 #On définit un angle par repport à la cote à partir duquel on considèle vent vent est offshore ou onShore
    vitesseVentNegligeable=10 #Vitesse de vent en dessous de laquelle la session n'est pas génée en kmh
    
    while h < len(prevision):

            if prevision[h][5]<vitesseVentNegligeable:
                prevision[h].append('Nul')
                
            elif ((spotChoisi.orientationSpot-prevision[h][4])%360)>angleSideshore and ((spotChoisi.orientationSpot-prevision[h][4])%360)<(180-angleSideshore):
                prevision[h].append('Offshore')
                #print((spotChoisi.orientationSpot-prevision[h][4])%360,"Offshore")

            elif ((spotChoisi.orientationSpot-prevision[h][4])%360)>180+angleSideshore and ((spotChoisi.orientationSpot-prevision[h][4])%360)<(360-angleSideshore):
                prevision[h].append('Onshore')
                #print((spotChoisi.orientationSpot-prevision[h][4])%360,"Onshore")

            else:
                prevision[h].append('Sideshore')
                #print((spotChoisi.orientationSpot-prevision[h][4])%360,"Sideshore")

            h=h+1

 
    
     ## Identifier la prochaine bonne session et donner l'info
    try:
        # Bloc à essayer

        testSwell=""
        testWind="Onshore"
        i=0
        indexBonSurf=int() #on veut identifier l'index de la prochaine bonne session

        while (testSwell,testWind)!=("Bon surf","Sideshore") and (testSwell,testWind)!=("Bon surf","Offshore") and (testSwell,testWind)!=("Bon surf","Nul"):
            testSwell=prevision[i][6]
            testWind=prevision[i][7]
            i+=1

        indexBonSurf=i-1 #On a identifié le premier "Bon surf" de la liste

        indexBonSurf

        print("La prochaine bonne session aura lieu le {} avec des vagues de {}m et une période de {} secondes. Le vent sera {}".format(prevision[indexBonSurf][0],prevision[indexBonSurf][1],prevision[indexBonSurf][2],prevision[indexBonSurf][7]))

    except:
        # Bloc qui sera exécuté en cas d'erreur
        print("Pas de bon surf en vue dans les 5 prochains jours, mets toi à la pétanque !")


# In[8]:


def liste_spot_bot():
    get_ipython().magic('run fonctionsAPI.ipynb')
    #On définit nos différents spots
    listeSpot=list()
    listeSpot.append(surfSpot('Lizay','4320',45))
    listeSpot.append(surfSpot('Gohaud','4409',0))

    listeNomSpot=[]
    for j in listeSpot:
        listeNomSpot.append(j.nomSpot)

    #print(listeNomSpot)
    choixNomSpot=', '.join(listeNomSpot)


    p=' '.join(["Quel spot t'intéresse:",choixNomSpot])
    return p,listeSpot


# In[4]:


import requests
import json  
import datetime

   

def prochaine_bonne_session_bot(spotChoisi,dataMSW,minWaveHeight,minPeriod,windMin,sport):
    '''This method will give us the next good surf session date based on a surf spot (surfSpot), the data from MSW for this spot, the minimum wave height the user wants and the min period of wave the user wants'''
    
####Code prévision kitesurf
###Données entrée:
 #windMin
 #spotChoisi
 #dataMSW 
 #sport

    data=dataMSW

    #On prepare la liste avec les forecast sur chaque date avec la donnée voulue: date, heuteur swell, period swell,sweel direction, witnd power, wind direction
    prevision=list()
    i=0
    while i < len(data):
        prevision.append([datetime.datetime.fromtimestamp(data[i]['localTimestamp']).ctime(),data[i]['swell']['components']["primary"]['height'],data[i]['swell']['components']["primary"]['period'],data[i]['swell']['components']["primary"]['direction'],data[i]['wind']['direction'],round(data[i]['wind']['speed']*0.54,1)])
        i+=1


    ##Prevision qualité surf :il faut que vent et vagues  soient d'une certaine taille mini
    hauteurMin=minWaveHeight
    periodeMin=minPeriod
    windMin=windMin

    h=0
    while h < len(prevision):

        if prevision[h][1]>=hauteurMin and prevision[h][2]>=periodeMin:
            prevision[h].append('Bon surf')
        else:
            prevision[h].append('Mauvais surf')
        h=h+1


    ## Identifier si le vent sera offshore, onshore, sideshore ou pas de vent
    h=0
    anglesideShore=20
    if sport=="Surf":
        angleSideshore=20 #On définit un angle par repport à la cote à partir duquel on considèle vent vent est offshore ou onShore
    elif sport=="Kitesurf":
        angleSideshore=0

    vitesseVentNegligeable=3 #Vitesse de vent en dessous de laquelle la session n'est pas génée en knts

    while h < len(prevision):

            if prevision[h][5]<vitesseVentNegligeable:
                prevision[h].append('Nul')

            elif ((spotChoisi.orientationSpot-prevision[h][4])%360)>angleSideshore and ((spotChoisi.orientationSpot-prevision[h][4])%360)<(180-angleSideshore):
                prevision[h].append('Offshore')
                #print((spotChoisi.orientationSpot-prevision[h][4])%360,"Offshore")

            elif ((spotChoisi.orientationSpot-prevision[h][4])%360)>180+angleSideshore and ((spotChoisi.orientationSpot-prevision[h][4])%360)<(360-angleSideshore):
                prevision[h].append('Onshore')
                #print((spotChoisi.orientationSpot-prevision[h][4])%360,"Onshore")

            else:
                prevision[h].append('Sideshore')
                #print((spotChoisi.orientationSpot-prevision[h][4])%360,"Sideshore")

            h=h+1

    h=0
    while h < len(prevision):

        if prevision[h][5]>=windMin:
            prevision[h].append('Kite OK')
        else:
            prevision[h].append('Kite NOK')
        h=h+1


     ## Identifier la prochaine bonne session et donner l'info
    try:
        # Bloc à essayer
        if sport=="Surf":

            testSwell=""
            testWind="Onshore"
            i=0
            indexBonSurf=int() #on veut identifier l'index de la prochaine bonne session

            while (testSwell,testWind)!=("Bon surf","Sideshore") and (testSwell,testWind)!=("Bon surf","Offshore"):
                testSwell=prevision[i][6]
                testWind=prevision[i][7]
                i+=1

            indexBonSurf=i-1 #On a identifié le premier "Bon surf" de la liste

            indexBonSurf

            return("La prochaine bonne session aura lieu le {} avec des vagues de {}m et une période de {} secondes. Le vent sera {}".format(prevision[indexBonSurf][0],prevision[indexBonSurf][1],prevision[indexBonSurf][2],prevision[indexBonSurf][7]))

        elif sport=="Kitesurf":
            testKite="Kite NOK"
            testWind="Offshore"
            i=0
            indexBonKite=int() #on veut identifier l'index de la prochaine bonne session

            while (testKite,testWind)!=("Kite OK","Onshore"):
                testKite=prevision[i][8]
                testWind=prevision[i][7]
                i+=1

            indexBonKite=i-1 #On a identifié le premier "Bon surf" de la liste

            indexBonKite

            return("La prochaine bonne session aura lieu le {} avec un vent de {} noeuds. Le vent sera {}".format(prevision[indexBonKite][0],prevision[indexBonKite][5],prevision[indexBonKite][7]))




    except:
        # Bloc qui sera exécuté en cas d'erreur
        return("Pas de session en vue dans les 5 prochains jours, mets toi à la pétanque !")


# In[10]:


def answers_bot(int ,str ,list ):
    
    return()
    

