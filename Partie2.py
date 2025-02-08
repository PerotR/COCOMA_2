from simulation import *
import subprocess
import json

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
            f.write("T"+str(taxis[i].id))
            if i<len(taxis)-1:
                f.write(",")
        f.write("]\n")
        f.write("\n")

        #Ecriture des variables dans le fichier yaml
        f.write("variables: \n")
        for tache in tasks:
            f.write("   ")
            f.write("Tache_"+str(tache.id))
            f.write(" : \n")
            f.write("      domain: taxis \n")
        f.write("\n")


        f.write("constraints: \n")
        for i in range(len(tasks)):
            f.write(f"   pref_{i+1}: \n")
            f.write("      type: extensional \n")
            f.write(f"      variables: Tache_{tasks[i].id} \n")

            f.write("      values: \n")
            for j in range(len(taxis)):
                f.write(f"         {j+1}: T{taxis[j].id} \n")

            f.write("\n")
        
        for i in range(len(tasks)):
            for j in range(len(tasks)):
                if i<j:
                    f.write(f"   different_Tache_{tasks[i].id}_Tache_{tasks[j].id}: \n")
                    f.write("      type: intention \n")
                    cout=math.dist(tasks[i].destination,tasks[j].start)
                    f.write(f"      function: {cout} if Tache_{tasks[i].id} == Tache_{tasks[j].id} else 0 \n")
                    f.write("\n")
        
        for i in range(len(taxis)):
            f.write(f"   cout_T{taxis[i].id}: \n")
            f.write("      type: intention \n")
            f.write(f"      function: {math.dist(tasks[0].start, tasks[0].destination)+math.dist(taxis[i].position,tasks[0].start)} if Tache_{tasks[0].id} =='T{taxis[i].id}'")
            for j in range(1,len(tasks)-1):
                f.write(f" else {math.dist(tasks[j].start, tasks[j].destination)+math.dist(taxis[i].position, tasks[j].destination)} if Tache_{tasks[j].id} =='T{taxis[i].id}'")
            if len(tasks)>1:
                f.write(f" else {math.dist(tasks[-1].start, tasks[-1].destination)+math.dist(taxis[i].position, tasks[-1].start)}")
            f.write("\n")
        
        f.write("\n")
        f.write(f"agents: \n")
        for i in range(len(tasks)):
            f.write(f"   Tache_{tasks[i].id}: \n")
            f.write("      capacity: 1 \n")

def solve_dcop(yaml_file):
    output_file = "results.json"
    
    # Exécuter la commande PyDCOP
    command = ["pydcop", "--output", output_file, "solve", "--algo", "dpop", yaml_file]
    result = subprocess.run(command, capture_output=True, text=True)
    
    # Vérifier si l'exécution s'est bien passée
    if result.returncode != 0:
        print("Erreur lors de l'exécution de PyDCOP:", result.stderr)
        return None

    # Charger les résultats du fichier JSON
    try:
        with open(output_file, "r") as f:
            solution = json.load(f)
        return solution
    except Exception as e:
        print("Erreur lors de la lecture des résultats:", e)
        return None


WIDTH, HEIGHT = 800, 600         # Taille de l'environnement (pixels)
NUM_TAXIS = 2                    # Nombre de taxis
TASK_INTERVAL = 10000             # Intervalle de génération d'une nouvelle tâche en millisecondes
TAXI_SPEED = 100                 # Vitesse du taxi (pixels par seconde)
NUM_TASKS_SPAWN = 5  
sim = Simulation(WIDTH, HEIGHT, NUM_TAXIS, TASK_INTERVAL, NUM_TASKS_SPAWN)

tasks=sim.generate_task()
generate_dcop(sim.taxis,tasks,"test.yaml")

# Exemple d'utilisation
yaml_file = "test.yaml"
dcop_solution = solve_dcop(yaml_file)

if dcop_solution:
    print("Résultats du DCOP:", dcop_solution)
