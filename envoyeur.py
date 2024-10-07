import socket
import json
import struct
import threading

# Lire les adresses des machines à partir du fichier machines.txt
with open('machines.txt', 'r') as file:
    machines = [line.strip() for line in file.readlines()]

# Convertir la liste des machines en JSON
machines_json = json.dumps(machines)

# Les messages spécifiques à envoyer
messages_specifiques = ["bonjour", "hello", "hola", "hi"]

# Dictionnaire pour stocker les connexions
connexions = {}

# Créer les connexions à toutes les machines
for machine in machines:
    try:
        # Créer un socket TCP/IP
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Se connecter à la machine
        client_socket.connect((machine, 3457))
        
        # Stocker la connexion
        connexions[machine] = client_socket
        print(f"Connexion établie avec {machine}")
    except Exception as e:
        print(f"Erreur lors de la connexion à {machine}: {e}")

def envoyer_message(client_socket, message):
    # Convertir le message en bytes
    message_bytes = message.encode('utf-8')
    # Envoyer la taille du message en utilisant send
    taille_message = struct.pack('!I', len(message_bytes))

    total_envoye = 0
    while total_envoye < len(taille_message):
        envoye = client_socket.send(taille_message[total_envoye:])
        if envoye == 0:
            raise RuntimeError("La connexion a été fermée")
        total_envoye += envoye
    # Envoyer le message
    client_socket.sendall(message_bytes)

def envoyer_messages():
    # Envoyer la liste des machines à chaque machine
    # for machine, client_socket in connexions.items():
    #     try:
    #         envoyer_message(client_socket, machines_json)
    #         print(f"Envoyé la liste des machines à {machine}")
    #     except Exception as e:
    #         print(f"Erreur lors de l'envoi à {machine}: {e}")

    # Envoyer les messages spécifiques de manière cyclique
    for index, message in enumerate(messages_specifiques):
        machine_index = index % len(machines)
        machine = machines[machine_index]
        try:
            client_socket = connexions[machine]
            envoyer_message(client_socket, message)
            print(f"Envoyé '{message}' à {machine}")
        except Exception as e:
            print(f"Erreur lors de l'envoi à {machine}: {e}")

    # Envoyer le message de fin de phase à chaque machine
    for machine, client_socket in connexions.items():
        try:
            envoyer_message(client_socket, "FIN PHASE 1")
            print(f"Envoyé 'FIN PHASE 1' à {machine}")
        except Exception as e:
            print(f"Erreur lors de l'envoi à {machine}: {e}")

def recevoir_exactement(client_socket, n):
    data = b''
    while len(data) < n:
        packet = client_socket.recv(n - len(data))
        if not packet:
            raise ConnectionError("Connexion fermée par le client")
        data += packet
    return data

def recevoir_message(client_socket):
    # Recevoir la taille du message
    taille_message = struct.unpack('!I', recevoir_exactement(client_socket, 4))[0]
    # Recevoir le message en utilisant la taille
    data = recevoir_exactement(client_socket, taille_message)
    return data.decode('utf-8')

def recevoir_messages():
    for machine, client_socket in connexions.items():
        try:
            message_reçu = recevoir_message(client_socket)
            if message_reçu == "OK FIN PHASE 1":
                print(f"Reçu '{message_reçu}' de {machine}")
        except Exception as e:
            print(f"Erreur lors de la réception de {machine}: {e}")

    # Fermer les connexions après les réceptions
    for machine, client_socket in connexions.items():
        try:
            client_socket.close()
            print(f"Connexion fermée avec {machine}")
        except Exception as e:
            print(f"Erreur lors de la fermeture de la connexion à {machine}: {e}")

# Créer et démarrer les threads pour envoyer et recevoir les messages
thread_envoi = threading.Thread(target=envoyer_messages)
thread_reception = threading.Thread(target=recevoir_messages)

thread_envoi.start()
thread_reception.start()

# Attendre que les threads se terminent
thread_envoi.join()
thread_reception.join()