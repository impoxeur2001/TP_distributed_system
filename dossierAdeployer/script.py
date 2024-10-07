import socket
import json
import struct
import threading
import os
import time

# Obtenir le nom de la machine
nom_machine = socket.gethostname()
PORT = 3466
PORT2 = 3467
print(f"'{nom_machine}' : Bonjour, je suis la machine ")

# Créer un socket TCP/IP
serveur_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Lier le socket à l'adresse et au port avec un maximum de 5 tentatives
for tentative in range(5):
    try:
        serveur_socket.bind(('0.0.0.0', PORT))
        print(f"'{nom_machine}' : Le socket est lié au port {PORT} après {tentative + 1} tentative(s).")
        break
    except OSError:
        if tentative < 4:
            # Si le port est déjà utilisé, libérer le port en utilisant la commande kill
            print(f"'{nom_machine}' : Le port {PORT} est déjà utilisé. Tentative de libération du port ({tentative + 1}/5)...")
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
            raise Exception(f"'{nom_machine}' : Impossible de lier le socket au port {PORT} après 5 tentatives.")

# Créer un socket TCP/IP
serveur_socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Lier le socket à l'adresse et au port avec un maximum de 5 tentatives
for tentative in range(5):
    try:
        serveur_socket2.bind(('0.0.0.0', PORT2))
        print(f"'{nom_machine}' : Le socket est lié au port {PORT2} après {tentative + 1} tentative(s).")
        break
    except OSError:
        if tentative < 4:
            # Si le port est déjà utilisé, libérer le port en utilisant la commande kill
            print(f"'{nom_machine}' : Le port {PORT2} est déjà utilisé. Tentative de libération du port ({tentative + 1}/5)...")
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
    # Recevoir la taille du message
    taille_message_bytes = recevoir_exactement(client_socket, 4)
    if taille_message_bytes is None:
        print("Connexion fermée lors de la réception de la taille du message.")
        return None

    taille_message = struct.unpack('!I', taille_message_bytes)[0]

    # Recevoir le message en utilisant la taille
    data = recevoir_exactement(client_socket, taille_message)
    if data is None:
        print("Connexion fermée lors de la réception du message.")
        return None
    return data.decode('utf-8')

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

    while etat!=3:
        message_reçu = recevoir_message(client_socket)
        print(f"'{nom_machine}' : Message reçu: {message_reçu}")
        if etat==1 and nb_message==0:
            machines_reçues = json.loads(message_reçu)
            nb_message+=1
            continue
        if etat==1 and nb_message>0 and message_reçu != "FIN PHASE 1":
            mots.append(message_reçu)
            nb_message+=1
            continue
        if message_reçu == "FIN PHASE 1":
            etat=2
            thread_accepter_phase2 = threading.Thread(target=accepter_connexion_phase2)
            thread_accepter_phase2.start()
            #envoyer "OK FIN PHASE 1"
            envoyer_message(client_socket, "OK FIN PHASE 1")
            # Créer les connexions à toutes les machines
            for machine in machines_reçues:
                try:
                    # Créer un socket TCP/IP
                    client_socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    
                    # Se connecter à la machine
                    client_socket2.connect((machine, PORT))

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
                print(f"{nom_machine}: Envoi de {mot} à {machines_reçues[machine_number]}")
                envoyer_message(connexions_phase_2[machines_reçues[machine_number]], mot)
            break

          
def gerer_phase_2(client_socket, adresse_client):
    print(f"'PHASE 2 {nom_machine}' : Gérer phase 2 pour {adresse_client}")
    # Recevoir des messages spécifiques dans une boucle
    while True:
        message_reçu = recevoir_message(client_socket)
        print(f"'PHASE 2 {nom_machine}' : Message reçu: {message_reçu} de {adresse_client}")
        

def accepter_connexion_phase1():
    # Accepter une nouvelle connexion
    client_socket, adresse_client = serveur_socket.accept()
    # Créer un thread pour gérer la connexion
    thread_connexion = threading.Thread(target=gerer_connexion, args=(client_socket, adresse_client))
    thread_connexion.start()

def accepter_connexion_phase2():
    while True:
        # Accepter une nouvelle connexion
        print(f"'PHASE 2 {nom_machine}' : En attente de connexion...")
        client_socket2, adresse_client = serveur_socket2.accept()
        print(f"'PHASE 2 {nom_machine}' : Connexion acceptée de {adresse_client}")
        # Créer un thread pour gérer la connexion
        thread_connexion = threading.Thread(target=gerer_phase_2, args=(client_socket2, adresse_client))
        thread_connexion.start()


# Créer et démarrer le thread pour accepter les connexions
thread_accepter = threading.Thread(target=accepter_connexion_phase1)
thread_accepter.start()

# Attendre que les threads se terminent (ce qui n'arrivera probablement jamais)
thread_accepter.join()
