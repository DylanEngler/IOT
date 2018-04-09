#!/usr/bin/python3
###############################################
#                                             #
#                le 19/03/2018                #
#                Crypto Money                 #
#               by Dylan Engler               #
#                                             #
###############################################

import requests
while(True):
    requete_Dylan = requests.get("https://www.cryptocompare.com/api/data/coinlist/")
    page_Dylan = requete_Dylan.json()

    liste_Dylan = page_Dylan['Data']
    choix_Dylan = str(input("mettre list pour la liste des Money, quit pour quitter ou le nom de la monnaie pour la conversion\n"))

    if (choix_Dylan == 'list'):
        for n in liste_Dylan :
            print(liste_Dylan[n]['Symbol'])
    if (choix_Dylan == 'quit'):
        print ("adieux l'ami")
        break

    else :
        compteur_Dylan = 0
        verif_Dylan = 0
        for n in liste_Dylan :
            compteur_Dylan +=1
            if(liste_Dylan[n]['Symbol'] == choix_Dylan):
                requetes_Dylan = requests.get("https://min-api.cryptocompare.com/data/price?fsym="+choix_Dylan+"&tsyms=" + choix_Dylan + ",USD")
                valeurs_Dylan= requetes_Dylan.json()
                valeur_Dylan = valeurs_Dylan['USD']
                print ('USD : ' + str(valeur_Dylan))
                print (choix_Dylan + ' : ' + str(valeurs_Dylan[choix_Dylan]))
            else :
                verif_Dylan +=1
        if(compteur_Dylan == verif_Dylan) :
            print("veillez choisir une Money prposer dans la list")

