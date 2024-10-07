import socket
import json
import struct
import threading
import os
import time

# Obtenir le nom de la machine
nom_machine = socket.gethostname()
PORT = 3457 
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
            os.system(f"lsof -t -i:{PORT} | xargs -r kill -9")
            time.sleep(2)
        else:
            raise Exception(f"'{nom_machine}' : Impossible de lier le socket au port {PORT} après 5 tentatives.")


# Écouter les connexions entrantes
serveur_socket.listen(5)
print(f"'{nom_machine}' : Le serveur écoute sur le port {PORT}...")

connexions = {}

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
        print("Connexion fermée par le client lors de la réception de la taille du message.")
        return None

    taille_message = struct.unpack('!I', taille_message_bytes)[0]

    # Recevoir le message en utilisant la taille
    data = recevoir_exactement(client_socket, taille_message)
    if data is None:
        print("Connexion fermée par le client lors de la réception du message.")
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

    # Recevoir la liste des machines
    # try:
    #     machines_reçues = json.loads(recevoir_message(client_socket))
    #     print(f"'{nom_machine}' : Liste des machines reçues: {machines_reçues}")
    # except json.JSONDecodeError:
    #     print(f"'{nom_machine}' : Erreur de décodage JSON")

    # Recevoir des messages spécifiques dans une boucle
    while True:
        message_reçu = recevoir_message(client_socket)
        print(f"'{nom_machine}' : Message reçu: {message_reçu}")
        if message_reçu == "FIN PHASE 1":
            print(f"'{nom_machine}' : Message reçu: {message_reçu}")
            envoyer_message(client_socket, "OK FIN PHASE 1")
            break
        if message_reçu == "GO PHASE 2":
            print(f"'{nom_machine}' : Message reçu: {message_reçu} de {adresse_client}")
            # Traiter le message "GO PHASE 2" ici
            # ...
            # Fermer la connexion après la phase 2
            client_socket.close()
            del connexions[adresse_client]
            print(f"Connexion fermée avec {adresse_client} après la phase 2")


def accepter_connexions():
    while True:
        # Accepter une nouvelle connexion
        client_socket, adresse_client = serveur_socket.accept()
        # Créer un thread pour gérer la connexion
        thread_connexion = threading.Thread(target=gerer_connexion, args=(client_socket, adresse_client))
        thread_connexion.start()

def recevoir_phase_2():
    while True:
        # Vérifier les connexions existantes pour la phase 2
        for adresse_client, client_socket in list(connexions.items()):
            try:
                message_reçu = recevoir_message(client_socket)

            except Exception as e:
                print(f"Erreur lors de la réception de {adresse_client}: {e}")

# Créer et démarrer le thread pour accepter les connexions
thread_accepter = threading.Thread(target=accepter_connexions)
thread_accepter.start()

# Attendre que les threads se terminent (ce qui n'arrivera probablement jamais)
thread_accepter.join()
