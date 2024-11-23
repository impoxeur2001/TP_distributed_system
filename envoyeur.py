import socket
import json
import struct
import threading

# Lire les adresses des machines à partir du fichier machines.txt
with open('machines.txt', 'r') as file:
    machines = [line.strip() for line in file.readlines()]
print(machines)

tab_fin_phase_1 = [False]*len(machines)
tab_fin_phase_2 = [False]*len(machines)
tab_fin_phase_3 = [False]*len(machines)
tab_fin_phase_4 = [False]*len(machines)

# Convertir la liste des machines en JSON
machines_json = json.dumps(machines)

# Text à envoyer 
with open("example.txt", "r") as file:
    # Read the entire file into a string variable
    text = file.read()
# Les messages spécifiques à envoyer
messages_specifiques = text.split()

# Dictionnaire pour stocker les connexions
connexions = {}


# Créer les connexions à toutes les machines
for machine in machines:
    try:
        # Créer un socket TCP/IP
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Se connecter à la machine
        client_socket.connect((machine, 3466))
        
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
    #Envoyer la liste des machines à chaque machine
    for machine in machines:
        try:
            client_socket = connexions[machine]
            envoyer_message(client_socket, machines_json)
            print(f"Envoyé la liste des machines à {machine}")
        except Exception as e:
            print(f"Erreur lors de l'envoi à {machine}: {e}")

    # Envoyer les splits de messages spécifiques de manière cyclique
    len_splits=3
    index_m=0
    index=0
    l=len(messages_specifiques)
    while (index_m<len(messages_specifiques)):
        machine_index = index % len(machines)
        machine = machines[machine_index]
        try:
            message= json.dumps(messages_specifiques[index_m:min(index_m + len_splits,l-1)])
            client_socket = connexions[machine]
            envoyer_message(client_socket, message)
            index_m+=len_splits
            index+=1
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
            break

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

def bucket_range(dict_frequency):
    buckets = [[] for _ in range(3)]
    bucket_frequencies = [0] * 3
    current_bucket = 0

    sorted_counts = sorted(dict_frequency.items(), key=lambda x: x[0])
    total_frequency = sum(freq for _, freq in sorted_counts)
    target_frequency = total_frequency // 3

    for count,frequency in sorted_counts:
         while frequency > 0:
            remaining_capacity = target_frequency - bucket_frequencies[current_bucket]

            if frequency <= remaining_capacity:
                # Add the entire count to the current bucket
                buckets[current_bucket].append((int(count), frequency))
                bucket_frequencies[current_bucket] += frequency
                frequency = 0
            else:
                # Fill the current bucket and move to the next one
                buckets[current_bucket].append((int(count), remaining_capacity))
                bucket_frequencies[current_bucket] += remaining_capacity
                frequency -= remaining_capacity
                current_bucket += 1

                # If all buckets are used, overflow into the last bucket
                if current_bucket >= 3:
                    current_bucket = 3 - 1

    return buckets
    

def recevoir_messages():
    while True:
        etat=0
        
        dict_frequency={}
        buckets=[]
        for machine, client_socket in connexions.items():
            try:
                message_reçu = recevoir_message(client_socket)
                if message_reçu == "OK FIN PHASE 1":
                    print(f"Reçu '{message_reçu}' de {machine}")
                    tab_fin_phase_1[machines.index(machine)] = True
                    # si toutes les machines ont fini la phase 1
                    if all(tab_fin_phase_1):
                        for machine, client_socket in connexions.items():
                            envoyer_message(client_socket, "GO PHASE 2")
                            print(f"Envoyé 'GO PHASE 2' à {machine}")
                elif message_reçu == "OK FIN PHASE 2":
                    print(f"Reçu '{message_reçu}' de {machine}")
                    tab_fin_phase_2[machines.index(machine)] = True
                    # si toutes les machines ont fini la phase 2
                    if all(tab_fin_phase_2):
                        for machine, client_socket in connexions.items():
                            envoyer_message(client_socket, "GO PHASE 3")
                            print(f"Envoyé 'GO PHASE 3' à {machine}")
                elif message_reçu == "OK FIN PHASE 3":
                    print(f"Reçu '{message_reçu}' de {machine}")
                    tab_fin_phase_3[machines.index(machine)] = True
                    # si toutes les machines ont fini la phase 3
                    if all(tab_fin_phase_3):
                        for machine, client_socket in connexions.items():
                            envoyer_message(client_socket, "GO PHASE 4")
                            print(f"Envoyé 'GO PHASE 4' à {machine}")
                            etat=1
                elif etat==1 and message_reçu == "OK FIN PHASE 4":
                    
                    print(f"Reçu '{message_reçu}' de {machine}")
                    tab_fin_phase_4[machines.index(machine)] = True
                    
                    # si toutes les machines ont fini la phase 3
                    if all(tab_fin_phase_3):
                        buckets=bucket_range(dict_frequency)
                        buckets_json = json.dumps(buckets)
                        
                        for machine, client_socket in connexions.items():
                            envoyer_message(client_socket, buckets_json)
                            envoyer_message(client_socket, "GO PHASE 5")
                            print(f"Envoyé 'GO PHASE 5' à {machine}")
                elif etat==1 and message_reçu != "OK FIN PHASE 4":
                    count,frequency= message_reçu.strip().split(":")
                    if int(count) not in dict_frequency:
                        dict_frequency[int(count)]=int(frequency)
                    else:
                        dict_frequency[int(count)]+=int(frequency)


            except Exception as e:
                print(f"Erreur lors de la réception de {machine}: {e}")

# Créer et démarrer les threads pour envoyer et recevoir les messages
thread_envoi = threading.Thread(target=envoyer_messages)
thread_reception = threading.Thread(target=recevoir_messages)

thread_envoi.start()
thread_reception.start()

# Attendre que les threads se terminent
thread_envoi.join()
thread_reception.join()