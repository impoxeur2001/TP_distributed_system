import socket
import json
import struct
import threading
import os
import time
from collections import Counter
import random

# Obtenir le nom de la machine
nom_machine = socket.gethostname()
PORT = 3466
PORT2 = 3467
print(f"'{nom_machine}' : Bonjour, je suis la machine ")

# Créer un socket TCP/IP
serveur_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Lier le socket à l'adresse et au port avec un maximum de 5 tentatives
for tentative in range(7):
    try:
        serveur_socket.bind(('0.0.0.0', PORT))
        print(f"'{nom_machine}' : Le socket est lié au port {PORT} après {tentative + 1} tentative(s).")
        break
    except OSError:
        if tentative < 6:
            # Si le port est déjà utilisé, libérer le port en utilisant la commande kill
            print(f"'{nom_machine}' : Le port {PORT} est déjà utilisé. Tentative de libération du port ({tentative + 1}/7)...")
            # Afficher avec print le PID du processus qui utilise le port
            pid = os.popen(f'lsof -t -i:{PORT}').read().strip()
            print(f"'{nom_machine}' : PID du processus qui utilise le port {PORT} : {pid}")
            if pid:
                # Libérer le port et afficher le résultat de kill
                os.system(f'kill -9 {pid}')
                print(f"'{nom_machine}' : Tentative de tuer le processus {pid}.")
            else:
                print(f"'{nom_machine}' : Aucun processus n'utilise le port {PORT}.")
            time.sleep(5)
        else:
            raise Exception(f"'{nom_machine}' : Impossible de lier le socket au port {PORT} après 7 tentatives.")

# Créer un socket TCP/IP
serveur_socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Lier le socket à l'adresse et au port avec un maximum de 5 tentatives
for tentative in range(7):
    try:
        serveur_socket2.bind(('0.0.0.0', PORT2))
        print(f"'{nom_machine}' : Le socket est lié au port {PORT2} après {tentative + 1} tentative(s).")
        break
    except OSError:
        if tentative < 6:
            # Si le port est déjà utilisé, libérer le port en utilisant la commande kill
            print(f"'{nom_machine}' : Le port {PORT2} est déjà utilisé. Tentative de libération du port ({tentative + 1}/7)...")
            # Afficher avec print le PID du processus qui utilise le port
            pid = os.popen(f'lsof -t -i:{PORT2}').read().strip()
            print(f"'{nom_machine}' : PID du processus qui utilise le port {PORT2} : {pid}")
            if pid:
                # Libérer le port et afficher le résultat de kill
                os.system(f'kill -9 {pid}')
                print(f"'{nom_machine}' : Tentative de tuer le processus {pid}.")
            else:
                print(f"'{nom_machine}' : Aucun processus n'utilise le port {PORT2}.")
            time.sleep(5)
        else:
            raise Exception(f"'{nom_machine}' : Impossible de lier le socket au port {PORT2} après 5 tentatives.")


# Écouter les connexions entrantes
serveur_socket.listen(5)
print(f"'{nom_machine}' : PHASE 1 Le serveur écoute sur le port {PORT}...")

serveur_socket2.listen(5)
print(f"'{nom_machine}' : PHASE 2 Le serveur écoute sur le port {PORT2}...")

connexions = {}
connexions_phase_2 = {}

def recevoir_exactement(client_socket, n):
    data = b''
    while len(data) < n:
        packet = client_socket.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

def recevoir_message(client_socket):
    try:
        # Recevoir la taille du message
        taille_message_bytes = client_socket.recv(4)
        if not taille_message_bytes:
            return None

        taille_message = struct.unpack('!I', taille_message_bytes)[0]

        # Recevoir le message en utilisant la taille
        data = client_socket.recv(taille_message)
        if not data:
            return None
        return data.decode('utf-8')
    except:
        return None

def envoyer_message(client_socket, message):
    # Convertir le message en bytes
    message_bytes = message.encode('utf-8')
    # Envoyer la taille du message
    client_socket.sendall(struct.pack('!I', len(message_bytes)))
    # Envoyer le message
    client_socket.sendall(message_bytes)

def gerer_connexion(client_socket, adresse_client):
    print(f"'{nom_machine}' : Connexion acceptée de {adresse_client}")

    # Ajouter la connexion au dictionnaire
    connexions[adresse_client] = client_socket

    nb_message=0
    mots=[]
    machines_reçues=[]
    etat=1
    mots_shuffle=[]
    max=0
    buckets=[]
    word_dict_sorted={}
    

    while etat!=7:
        message_reçu = recevoir_message(client_socket)
        if message_reçu is None:
            print(f"'{nom_machine}' : Connexion fermée par le client {adresse_client}")
            break

        #print(f"'{nom_machine}' : Message reçu: {message_reçu}")
        if etat==1 and nb_message==0:
            machines_reçues = json.loads(message_reçu)
            nb_message+=1
            continue
        if etat==1 and nb_message>0 and message_reçu != "FIN PHASE 1":
            mots_recu=json.loads(message_reçu)
            mots=mots+mots_recu
            nb_message+=1

            continue
        if message_reçu == "FIN PHASE 1":
            etat=2
            thread_accepter_phase2 = threading.Thread(target=accepter_connexion_phase2, args=(mots_shuffle,))
            thread_accepter_phase2.start()
            #envoyer "OK FIN PHASE 1"
            print(f"{nom_machine}: Envoi de OK FIN PHASE 1 à {adresse_client}")
            envoyer_message(client_socket, "OK FIN PHASE 1")
            # Créer les connexions à toutes les machines
            for machine in machines_reçues:
                try:
                    # Créer un socket TCP/IP
                    client_socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    
                    # Se connecter à la machine
                    client_socket2.connect((machine, PORT2))

                    #vérifier si la connexion est établie
                    
                    # Stocker la connexion
                    connexions_phase_2[machine] = client_socket2
                    print(f"{nom_machine}:Connexion établie avec {machine}")
                except Exception as e:
                    print(f"Erreur lors de la connexion à {machine}: {e}")
            continue
        if message_reçu == "GO PHASE 2":
            for mot in mots:
                machine_number = len(mot)%len(machines_reçues)
                #print(f"{nom_machine}: Envoi de {mot} à {machines_reçues[machine_number]}")
                try:
                   envoyer_message(connexions_phase_2[machines_reçues[machine_number]], mot)
                except Exception as e:
                    print(f"Erreur lors de l'envoi à {machines_reçues[machine_number]}: {e}")
            print(f"{nom_machine}: Envoi de OK FIN PHASE 2 à {adresse_client}")
            envoyer_message(client_socket, "OK FIN PHASE 2")
            print(f"{nom_machine}: OK FIN PHASE 2 envoyé")
            continue
        if message_reçu == "GO PHASE 3":
            print(f'{nom_machine} received GO PHASE 3')
            etat=3
            word_count_dict = dict(Counter(mots_shuffle))
            """
            path=f'output_{nom_machine}.json'
            with open(path, "w") as file:
                json.dump(word_count_dict, file, indent=4)
            print(f'{path} file created')
            """
            envoyer_message(client_socket, "OK FIN PHASE 3")
            continue
        if message_reçu == "GO PHASE 4":
            etat=4
            print(f'{nom_machine} received GO PHASE 4')
            
            
            dict_frequency_local={}
            for word in word_count_dict:
                if word_count_dict[word] not in dict_frequency_local:
                    dict_frequency_local[word_count_dict[word]]=1
                else:
                    dict_frequency_local[word_count_dict[word]]+=1
            
            for count in dict_frequency_local:
                message=f'{count}:{dict_frequency_local[count]}'
                print(f'{nom_machine} sent {message} to orchestrator')
                envoyer_message(client_socket, message)
            print(f'{nom_machine} sent frequency to orchestrator')
            envoyer_message(client_socket, "OK FIN PHASE 4")
            print(f'{nom_machine} sent OK FIN PHASE 4 to orchestrator')
            continue

        if etat==4 and message_reçu!="GO PHASE 5":
            try:
                buckets = json.loads(message_reçu)
                print(f'{nom_machine} received buckets {buckets}')
            except Exception as error:
                print(f"Erreur lors de la réception de {client_socket}: {error}")
        if message_reçu == "GO PHASE 5":
            etat=5
            #send each count to its bucke (apply the probalistic method for counts that are in multiple buckets)
            for word in word_count_dict:
                count=word_count_dict[word]
                occurences=[]
                index=[]
                for i in range (len(buckets)):
                    for element in buckets[i]:
                        if (count==int(element[0])):
                            occurences.append(element)
                            index.append(i)
                            
                if(len(index)>3):
                    print(f'{len(index)}')        
                if(len(index)==1):
                    message=f'{word}:{count}'
                    envoyer_message(connexions_phase_2[machines_reçues[index[0]]], message)
                    print(f"{nom_machine}: Envoi de {message} à {machines_reçues[index[0]]}")
                if(len(index)>1):
                    message=f'{word}:{count}'
                    probabilities=[0]*len(index)
                    total=0
                    random_value = random.random()
                    for element in occurences:
                        total+=int(element[1])
                    for i in range(len(index)):
                        element=occurences[i]
                        if(i==0):
                            probabilities[i]=int(element[1])/total
                        if(i>0):
                            probabilities[i]=int(element[1])/total + probabilities[i-1]
                    for i in range(len(index)):
                        if(random_value < probabilities[i]):
                           envoyer_message(connexions_phase_2[machines_reçues[index[i]]], message)
                           print(f"{nom_machine}: Envoi de {message} à {machines_reçues[index[i]]}")
                           break
            envoyer_message(client_socket, "OK FIN PHASE 5")
            
        if etat==5 and message_reçu != "GO PHASE 6":
            print(f"{nom_machine}: recieved {message_reçu}")
            word,count= message_reçu.strip().split(":")
            word_dict_sorted[word]=int(count)
        if message_reçu =="GO PHASE 6":
            sorted_dict = dict(sorted(word_dict_sorted.items(), key=lambda item: item[1]))
            print(f'{nom_machine} received sorted dict {sorted_dict}')
            """path=f'output_sorted_{nom_machine}.json'
            with open(path, "w") as file:
                json.dump(sorted_dict, file, indent=4)
            print(f'{path} file created')"""
                    






            



            
            
            
            

          
def gerer_phase_2(client_socket, adresse_client,mots_shuffle):
    print(f"'PHASE 2 {nom_machine}' : Gérer phase 2 pour {adresse_client}")
    # Recevoir des messages spécifiques dans une boucle
    while True:
        message_reçu = recevoir_message(client_socket)
        #print(f"'PHASE 2 {nom_machine}' : Message reçu: {message_reçu} de {adresse_client}")
        if(message_reçu!="GO PHASE 2"):
            mots_shuffle.append(message_reçu)
            print(f"{message_reçu}")
        

def accepter_connexion_phase1():
    # Accepter une nouvelle connexion
    client_socket, adresse_client = serveur_socket.accept()
    # Créer un thread pour gérer la connexion
    thread_connexion = threading.Thread(target=gerer_connexion, args=(client_socket, adresse_client))
    thread_connexion.start()

def accepter_connexion_phase2(mots_shuffle):
    while True:
        # Accepter une nouvelle connexion
        print(f"'PHASE 2 {nom_machine}' : En attente de connexion...")
        client_socket2, adresse_client = serveur_socket2.accept()
        print(f"'PHASE 2 {nom_machine}' : Connexion acceptée de {adresse_client}")
        # Créer un thread pour gérer la connexion
        thread_connexion = threading.Thread(target=gerer_phase_2, args=(client_socket2, adresse_client,mots_shuffle))
        thread_connexion.start()


# Créer et démarrer le thread pour accepter les connexions
thread_accepter = threading.Thread(target=accepter_connexion_phase1)
thread_accepter.start()

# Attendre que les threads se terminent (ce qui n'arrivera probablement jamais)
thread_accepter.join()
