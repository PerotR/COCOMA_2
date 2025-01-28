from Partie1 import *

def generate_file_yaml(env,nom_fic):
    list_taxis_env=env.taxis
    list_taches_env=env.tasks
    list_taxi=[]
    list_taches=[]
    for i in range(1,len(list_taxis_env)+1):
        list_taxi.append(f"taxi_{i}")
    
    for i in range(1,len(list_taches_env)+1):
        list_taches.append(f"task_{i}")
        
    with open(nom_fic,"w") as f:
        f.write("name: Taxi Task Allocation Problem \n")
        f.write("objective: min \n")
        f.write("\n")

        #Ecriture des domaines dans le fichier yaml
        f.write("domains: \n")
        f.write("   taxis: \n" )
        f.write("      values: ")
        f.write("[")
        for i in range(len(list_taxi)):
            f.write(list_taxi[i])
            if i<len(list_taxi)-1:
                f.write(",")
        f.write("]\n")
        f.write("\n")

        #Ecriture des variables dans le fichier yaml
        f.write("variables: \n")
        for tache in list_taches:
            f.write("   ")
            f.write(tache)
            f.write(" : \n")
            f.write("      domain: taxis \n")
        f.write("\n")

        f.write("constraints: \n")
        for i in range(len(list_taches)):
            f.write(f"   pref_{i+1}: \n")
            f.write("      type: extensional \n")
            f.write(f"      variables: {list_taches[i]} \n")
            f.write("      values: \n")
            for j in range(len(list_taxi)):
                f.write(f"         {j+1}: {list_taxi[j]} \n")
            f.write("\n")
        
        for i in range(len(list_taches)):
            for j in range(len(list_taches)):
                if i<j:
                    f.write(f"   different_{list_taches[i]}_{list_taches[j]}: \n")
                    f.write("      type: intention \n")
                    cout=list_taches_env[i].calculate_distance(list_taches_env[i].end,list_taches_env[j].start)
                    f.write(f"      function: {cout} if {list_taches[i]}=={list_taches[j]} else 0 \n")
                    f.write("\n")
        
        for i in range(len(list_taxi)):
            f.write(f"   cout_{list_taxi[i]}: \n")
            f.write("      type: intention \n")
            f.write(f"      function: {list_taches_env[0].cost+list_taxis_env[i].calculate_distance(list_taxis_env[i].position,list_taches_env[0].start)} if {list_taches[0]}=='{list_taxi[i]}'")
            for j in range(1,len(list_taches)-1):
                f.write(f" else {list_taches_env[j].cost+list_taxis_env[i].calculate_distance(list_taxis_env[i].position,list_taches_env[j].start)} if {list_taches[j]}=='{list_taxi[i]}'")
            if len(list_taches)>1:
                f.write(f" else {list_taches_env[-1].cost+list_taxis_env[i].calculate_distance(list_taxis_env[i].position,list_taches_env[-1].start)}")
            f.write("\n")
        
        f.write("\n")
        f.write(f"agents: \n")
        for i in range(len(list_taches)):
            f.write(f"   {list_taches[i]}: \n")
            f.write("      capacity: 1 \n")
            


GRID_SIZE = 20
NUM_TAXIS = 3
TASK_FREQUENCY = 5
NUM_ITERATIONS = 30
DELAY = 500  # Délai de 500 millisecondes (0.5 seconde) entre chaque itération
TASK_NUMBER = 6 # Nombre de tâches à générer, >= NUM_TAXIS

env=Environment(grid_size=GRID_SIZE, num_taxis=NUM_TAXIS, task_frequency=TASK_FREQUENCY, task_number=TASK_NUMBER,num_iterations=NUM_ITERATIONS, delay=DELAY)
env.generate_tasks()
generate_file_yaml(env,"freq.yaml")