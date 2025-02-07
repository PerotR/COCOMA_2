from Simulation import *


def generate_dcop(taxis,tasks, nom):

    with open(nom,"w") as f:
        f.write("name: Allocation en ligne de taches \n")
        f.write("objective: min \n")
        f.write("\n")

        #Ecriture des domaines dans le fichier yaml
        f.write("domains: \n")
        f.write("   taxis: \n" )
        f.write("      values: ")
        f.write("[")
        for i in range(len(taxis)):
            print(taxis[i].id)
            f.write(taxis[i].id)
            if i<len(taxis)-1:
                f.write(",")
        f.write("]\n")
        f.write("\n")

        #Ecriture des variables dans le fichier yaml
        f.write("variables: \n")
        for tache in tasks:
            f.write("   ")
            f.write("Tache "+str(tache.id))
            f.write(" : \n")
            f.write("      domain: taxis \n")
        f.write("\n")


        f.write("constraints: \n")
        for i in range(len(tasks)):
            f.write(f"   pref_{i+1}: \n")
            f.write("      type: extensional \n")
            f.write(f"      variables: {tasks[i].id} \n")
            f.write("      values: \n")
            for j in range(len(taxis)):
                f.write(f"         {j+1}: {taxis[j].id} \n")
            f.write("\n")
        
        for i in range(len(tasks)):
            for j in range(len(tasks)):
                if i<j:
                    f.write(f"   different_{tasks[i].id}_{tasks[j].id}: \n")
                    f.write("      type: intention \n")
                    cout=math.dist(tasks[i].destination,tasks[j].start)
                    f.write(f"      function: {cout} if {tasks[i].id}=={tasks[j].id} else 0 \n")
                    f.write("\n")
        
        for i in range(len(taxis)):
            f.write(f"   cout_{taxis[i].id}: \n")
            f.write("      type: intention \n")
            f.write(f"      function: {math.dist(tasks[0].start, tasks[0].destination)+math.dist(taxis[i].position,tasks[0].start)} if {tasks[0].id}=='{taxis[i].id}'")
            for j in range(1,len(tasks)-1):
                f.write(f" else {math.dist(tasks[j].start, tasks[j].destination)+math.dist(taxis[i].position, tasks[j].destination)} if {tasks[j].id}=='{taxis[i].id}'")
            if len(tasks)>1:
                f.write(f" else {math.dist(tasks[-1].start, tasks[-1].destination)+math.dist(taxis[i].position, tasks[-1].start)}")
            f.write("\n")
        
        f.write("\n")
        f.write(f"agents: \n")
        for i in range(len(tasks)):
            f.write(f"   {tasks[i].id}: \n")
            f.write("      capacity: 1 \n")



WIDTH, HEIGHT = 800, 600         # Taille de l'environnement (pixels)
NUM_TAXIS = 2                    # Nombre de taxis
TASK_INTERVAL = 10000             # Intervalle de génération d'une nouvelle tâche en millisecondes
TAXI_SPEED = 100                 # Vitesse du taxi (pixels par seconde)
NUM_TASKS_SPAWN = 5  
sim = Simulation(WIDTH, HEIGHT, NUM_TAXIS, TASK_INTERVAL, NUM_TASKS_SPAWN)

tasks=sim.generate_task()
generate_dcop(sim.taxis,tasks,"test.yaml")