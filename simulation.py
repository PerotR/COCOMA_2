from matplotlib import pyplot as plt
import pygame
import random
import math
import itertools
import sys
from copy import deepcopy
from taxi import Taxi
from task import Task
import config
#import dcop
import subprocess
import json

class Simulation:
    """Gère l'environnement, la génération de tâches et l'allocation aux taxis."""
    def __init__(self, width, height, num_taxis, task_interval, num_tasks_spawn, resolutionType, isPenalty, random_task, algo):
        self.width = width  # Largeur de la fenêtre
        self.height = height # Taille de la fenêtre
        self.taxis = [] # Liste des taxis
        self.num_tasks_spawn = num_tasks_spawn # Nombre de tâches générées à chaque intervalle
        self.paused = False 
        self.resolutionType = resolutionType # Type de résolution (greedy, dcop, PSI, SSI, regret)
        for i in range(num_taxis): # Création des taxis au centre de l'environnement
            pos = (config.WIDTH/2 + i, config.HEIGHT/2 + i)
            self.taxis.append(Taxi(i, pos))
        self.task_interval = task_interval # Intervalle de génération de tâches (en ms)
        self.last_task_time = -10000  # Temps (en ms) de la dernière génération de tâche
        self.task_counter = 0    # Compteur pour assigner des ID uniques aux tâches, pour la génération aléatoire
        self.isPenalty = isPenalty # Indique si on utilise une pénalité en fonction de la taille des tâches à effectuer, pour insertion_heuristic
        self.random_task = random_task # Générer des tâches aléatoires ou prédéfinies, True pour aléatoire, False pour prédéfini
        self.algo = algo # Algorithme de résolution (dpop, dsa, etc.)
        self.task_list = [] # Liste des tâches prédéfinies
        with open("task_created.json", "r") as f: # Charger les tâches prédéfinies
            task_json = json.load(f)
        for task in task_json:
            start = task["start"]
            destination = task["end"]
            id = task["task_id"]
            task = Task(start, destination, id)
            self.task_list.append(task)
        self.mean_route_cost = [] # Coût moyen des itinéraires des taxis pour évaluation


    def generate_task(self):
        """Génère une nouvelle tâche avec un départ et une destination aléatoires dans l'environnement."""
        tasks = []
        for _ in range(self.num_tasks_spawn):
            start = (random.randint(0, self.width), random.randint(0, self.height))
            destination = (random.randint(0, self.width), random.randint(0, self.height))
            task = Task(start, destination, self.task_counter)
            self.task_counter += 1
            tasks.append(task)
        return tasks
    
    def created_tasks(self, num_tasks):
        """Génère des tâches prédéfinies pour tester les algorithmes sur les mêmes instances."""

        if self.task_list == []:
            print("Plus de tâches à générer !")

        created_tasks_list = self.task_list[:num_tasks]
        self.task_list = self.task_list[num_tasks:]    
        
        return created_tasks_list



    def greedy_task_assignment(self, taxis, tasks):
        """
        Affecte chacune des tâches de la liste tasks au taxi le plus proche
        (en tenant compte du temps qu'il met à finir ses tâches déjà assignées).
        
        Pour un taxi donné, le coût estimé est calculé en FIFO :
        - Si le taxi est inactif (aucune tâche en attente), le coût est 
            distance(position du taxi, tâche.start) + distance(tâche.start, tâche.destination)
        - Sinon, le coût est égal à la somme des distances le long de la file d'attente 
            distance(position actuelle, tâche.start) + distance(tâche.start, tâche.destination).
        - On test toutes les permutations possibles de la liste des nouvelles tâches et on retient la meilleure.
        """
        

        all_permutation = [list(task) for task in itertools.permutations(tasks)]
        taxi_tmp = deepcopy(taxis)

        best_Permutation = None
        for permutation in all_permutation: # On cherche la meilleure permutation
            best_allocation_cost = float('inf')
            list_estimated_cost = []
            longest_route = 0
            taxi_tmp = deepcopy(taxis) # On remet taxi_tmp à sa valeur initiale à chaque nouvelle permutation

            # Pour chaque tâche à affecter, on choisit le taxi avec le moindre coût estimé.
            for task in permutation:
                best_taxi = None
                best_estimated_cost = float('inf')

                for taxi in taxi_tmp:
                    # Calcul du coût de réalisation si l'on affecte cette tâche au taxi,
                    cost = 0.0
                    current_pos = taxi.position
                    
                    # Calcul du coût de réalisation des tâches deja presentes dans la file
                    for t in taxi.tasks:
                        cost += math.dist(current_pos, t.start) + math.dist(t.start, t.destination)
                        current_pos = t.destination
                    
                    cost += math.dist(current_pos, task.start) + math.dist(task.start, task.destination)
                                        
                    if cost < best_estimated_cost:
                        best_estimated_cost = cost
                        best_taxi = taxi

                best_taxi.tasks.append(task)

            for taxi in taxi_tmp: # On calcule le coût de la permutation

                taxi.calculate_total_route_cost()
                list_estimated_cost.append(taxi.current_route_cost)

            longest_route = max(list_estimated_cost) # On récupère le coût le plus long entre les taxis, pour avoir le coût de la permutation

            if longest_route < best_allocation_cost: # On compare le coût de la permutation avec le meilleur coût trouvé
                best_allocation_cost = longest_route
                best_Permutation = permutation

        for task in best_Permutation: # On parcourt la meilleure permutation pour affecter les tâches aux taxis
            best_taxi = None
            best_estimated_cost = float('inf')

            for taxi in taxis:
  
                cost = 0.0
                current_pos = taxi.position
                
                
                for t in taxi.tasks:
                    cost += math.dist(current_pos, t.start) + math.dist(t.start, t.destination)
                    current_pos = t.destination
                
                # Coût pour la nouvelle tâche
                cost += math.dist(current_pos, task.start) + math.dist(task.start, task.destination)
                
                if cost < best_estimated_cost:
                    best_estimated_cost = cost
                    best_taxi = taxi
            
        
            best_taxi.tasks.append(task)
            
            # Mise à jour de l'itinéraire du taxi :
            # Si le taxi n'avait pas d'itinéraire (pas de tâches en attente), on le crée.
            # Sinon, on ajoute simplement les deux points (start et destination) à la suite.
            if not best_taxi.route:
                best_taxi.route = [task.start, task.destination]
                best_taxi.target_index = 0
            else:
                best_taxi.route.extend([task.start, task.destination])
            
            # mise à jour du coût total estimé de la file
            current_pos = best_taxi.position
            route_cost = 0.0
            for t in best_taxi.tasks:
                route_cost += math.dist(current_pos, t.start) + math.dist(t.start, t.destination)
                current_pos = t.destination
            best_taxi.current_route_cost = route_cost


    def cost_dcop(self, taxi, task):
        cost=100000000000
        if taxi.isWorking:
            cost = math.dist(task.start, task.destination)+math.dist(taxi.tasks[taxi.target_index//2].destination,task.start)
            return cost
        
        else:
            cost= math.dist(task.start, task.destination)+math.dist(taxi.position,task.start)
            for ta in taxi.tasks:
                cost = min(cost,(math.dist(task.start, task.destination)+math.dist(ta.destination,task.start)))
            return cost



    def generate_dcop(self, taxis,tasks, nom):

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
                f.write(f"      function: {self.cost_dcop(taxis[i],tasks[0])} if Tache_{tasks[0].id} =='T{taxis[i].id}'")
                for j in range(1,len(tasks)-1):
                    f.write(f" else {self.cost_dcop(taxis[i],tasks[j])} if Tache_{tasks[j].id} =='T{taxis[i].id}'")
                if len(tasks)>1:
                    f.write(f" else {self.cost_dcop(taxis[i],tasks[-1])}")
                f.write("\n")
            
            f.write("\n")
            f.write(f"agents: \n")
            for i in range(len(tasks)):
                f.write(f"   Tache_{tasks[i].id}: \n")
                f.write("      capacity: 1 \n")

    def solve_dcop(self, yaml_file):
        output_file = "results.json"
        
        # Exécuter la commande PyDCOP
        if self.algo == "dpop":
            command = ["pydcop", "--output", output_file, "solve", "--algo", "dpop", yaml_file]
        if self.algo == "dsa":
            command = ["pydcop", "--output", output_file,"--timeout","1", "solve", "--algo", "dsa", yaml_file]
        if self.algo == "mgm":
            command = ["pydcop", "--output", output_file,"--timeout", "1", "solve", "--algo", "mgm",  yaml_file]

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
        
    def attribution_dcop(self,tasks, taxis, res):

        for task_key, taxi_id in res.items():
            # Trouver la tâche correspondante par son nom (par exemple, 'Tache_0')
            task = next((t for t in tasks if t.id == int(task_key.split('_')[1])), None)
            
            # Trouver le taxi correspondant
            taxi = next((t for t in taxis if t.id == int(taxi_id.split('T')[1])), None)

            if task and taxi:
                taxi.tasks.append(task)
            
                # Mise à jour de l'itinéraire du taxi en mode FIFO :
                # Si le taxi n'avait pas d'itinéraire (pas de tâches en attente), on le crée.
                # Sinon, on ajoute simplement les deux points (start et destination) à la suite.
                if not taxi.route:
                    taxi.route = [task.start, task.destination]
                    taxi.target_index = 0
                else:
                    taxi.route.extend([task.start, task.destination])
                
                # On peut aussi mettre à jour le coût total estimé de la file (pour information)
                current_pos = taxi.position
                route_cost = 0.0
                for t in taxi.tasks:
                    route_cost += math.dist(current_pos, t.start) + math.dist(t.start, t.destination)
                    current_pos = t.destination
                taxi.current_route_cost = route_cost


    def insertion_heuristic(self, taxi, task):
        """simule l'insertion d'une tâche dans la liste des tâches d'un taxi"""

        taxi.calculate_total_route_cost()
        current_route_cost = taxi.current_route_cost

        if not taxi.tasks:
            return math.dist(taxi.position, task.start) + math.dist(task.start, task.destination), 0
        

        best_cost_with_insertion = float('inf')
        best_index = 0
        penalty = 0


        for pos in range(len(taxi.tasks) + 1): # On teste toutes les positions possibles pour l'insertion
            candidate_tasks = deepcopy(taxi.tasks)
            candidate_tasks.insert(pos, task)
            cost = 0
            pos_point = taxi.position
            for t in candidate_tasks:
                cost += math.dist(pos_point, t.start) + math.dist(t.start, t.destination)
                pos_point = t.destination
            if cost < best_cost_with_insertion:
                best_cost_with_insertion = cost
                best_index = pos

        gap_cost = best_cost_with_insertion - current_route_cost

        if self.isPenalty:
            penalty = len(taxi.tasks) * 50 # Coût de pénalité en fonction de la taille de la file d'attente
            gap_cost += penalty
        
        return gap_cost, best_index

    def PSI_task_assignment(self, taxis, tasks):
        """Attribution parallèle des tâches via PSI (enchères parallèles)."""
        bids = {} # Dictionnaire de la forme {task: [(taxi_id, bid, insertion_index)]}
        bid = 0
        insertion_index = 0

        for task in tasks:
            bids[task] = []

            for taxi in taxis:
                bid, insertion_index = self.insertion_heuristic(taxi, task)
                bids[task].append((taxi.id, bid, insertion_index))

        for task, task_bids in bids.items():
            if not task_bids: # Si aucune offre n'a été faite pour cette tâche
                continue

            best_bid = min(task_bids, key=lambda x: x[1]) # Meilleure offre pour la tâche
            best_taxi_id, best_bid, best_index = best_bid

            best_taxi = next(t for t in taxis if t.id == best_taxi_id) # Trouver le taxi correspondant

            best_taxi.tasks.insert(best_index, task)
            best_taxi.allow_reordering = False
            if not best_taxi.isWorking:
                best_taxi.build_route_from_current_tasks()


    def SSI_task_assignment(self, taxis, tasks):
        """Enchères sequentielles, où les offres sont réalisées itérativement sur les items"""
        bid = 0
        index = 0

        for task in tasks:
            best_taxi = None
            best_bid = float('inf')
            for taxi in taxis:
                bid, index = self.insertion_heuristic(taxi, task)
                if bid < best_bid:
                    best_bid = bid
                    best_taxi = taxi 
                    best_index = index         
            
            if best_taxi:
                best_taxi.tasks.insert(best_index, task)
                best_taxi.allow_reordering = False
                if not best_taxi.isWorking:
                    best_taxi.build_route_from_current_tasks()


    def calculate_regret(self, taxis, tasks):
        """Calcul du regret pour chaque tâche"""

        task_regrets = [] # Liste de la forme [(task1, regret1)...]
        for task in tasks:
            bids = [] # Liste de la forme [(bid1, taxi_id1)...]
            for taxi in taxis:
                bid, _ = self.insertion_heuristic(taxi, task)
                bids.append((bid, taxi.id))
                
            bids.sort(key=lambda x: x[0]) # Tri par coût croissant

            if len(bids) > 1:
                best_bid, second_best_bid = bids[0][0], bids[1][0]
                regret = second_best_bid - best_bid
            else:
                regret = float('inf')

            task_regrets.append((task, regret))

        task_regrets.sort(key=lambda x: -x[1]) # Tri par regret décroissant

        return [tr[0] for tr in task_regrets] # On retourne les tâches dans l'ordre décroissant des regrets

    def regret_task_assignment(self, taxis, tasks):
        """Attribution des tâches en fonction du regret, pour SSI basé sur le regret"""

        ordered_tasks = self.calculate_regret(taxis, tasks) # Tâches triées par regret décroissant

        #Puis on fait pareil que SSI mais sur les tâches triées avec le regret
        for task in ordered_tasks:
            best_taxi = None
            best_bid = float('inf')
            best_index = 0

            for taxi in taxis:
                bid, index = self.insertion_heuristic(taxi, task)
                if bid < best_bid:
                    best_bid = bid
                    best_taxi = taxi
                    best_index = index
            
            if best_taxi:
                best_taxi.tasks.insert(best_index, task)
                best_taxi.allow_reordering = False
                if not best_taxi.isWorking:
                    best_taxi.build_route_from_current_tasks()

                    
    def __repr__(self):
        return f"Simulation(width={self.width}, height={self.height}, num_taxis={len(self.taxis)}, task_interval={self.task_interval}, num_tasks_spawn={self.num_tasks_spawn})"

            


    def update(self, current_time, dt):
        """
        Met à jour la simulation :
         - Génère une nouvelle tâche tous les TASK_INTERVAL millisecondes et l'alloue.
         - Resout le problème d'allocation de tâches en utilisant l'algorithme spécifié.
         - Met à jour la position de chaque taxi.
        """
        if not self.paused:
            if current_time - self.last_task_time > self.task_interval:
                if self.random_task:
                    new_tasks = self.generate_task()
                else:
                    new_tasks = self.created_tasks(config.NUM_TASKS_SPAWN)
                match self.resolutionType:
                    case "greedy":
                        self.greedy_task_assignment(self.taxis, new_tasks)
                    case "dcop":
                        if len(new_tasks)!= 0:
                            self.generate_dcop(self.taxis, new_tasks, "dcop.yaml")
                            allocation=self.solve_dcop("dcop.yaml")
                            self.attribution_dcop(new_tasks, self.taxis, allocation['assignment'])
                    case "PSI":
                        self.PSI_task_assignment(self.taxis, new_tasks)
                    case "SSI":
                        self.SSI_task_assignment(self.taxis, new_tasks)
                    case "regret":
                        self.regret_task_assignment(self.taxis, new_tasks)
                    case _:
                        print("Résolution non reconnue, on utilise greedy")
                        self.greedy_task_assignment(self.taxis, new_tasks)
                    
                #Pour python 3.8 pour DCOP
                # if self.resolutionType== "greedy":
                #     self.greedy_task_assignment(self.taxis, new_tasks)
                # elif self.resolutionType=="dcop":
                #     if len(new_tasks)!=0:
                #         self.generate_dcop(self.taxis, new_tasks, "dcop.yaml")
                    
                #         allocation=self.solve_dcop("dcop.yaml")
                #         self.attribution_dcop(new_tasks, self.taxis, allocation['assignment'])
                
                mean_cost = sum([taxi.current_route_cost for taxi in self.taxis]) / len(self.taxis)
                self.mean_route_cost.append(mean_cost)
                
                self.last_task_time = current_time

            for taxi in self.taxis:
                taxi.update(dt)

    def draw(self, screen):
        """Affiche l'environnement, les trajets planifiés et les taxis."""
        screen.fill(config.WHITE)

        # Pour chaque taxi, dessiner son itinéraire et sa position
        for taxi in self.taxis:
            if taxi.route and taxi.target_index < len(taxi.route):
                points = [taxi.position] + taxi.route[taxi.target_index:]

                for i in range(len(points) - 1):
                    # Vérifier si ce segment correspond à une tâche en cours
                    if taxi.isWorking and i == taxi.target_index - 1 and i % 2 == 0:
                        line_color = config.ORANGE  # Segment de la tâche active
                    else:
                        line_color = config.BLACK  # Autres segments

                    pygame.draw.line(screen, line_color, points[i], points[i + 1], 2)

                # Affichage des waypoints : Départ (vert), Destination (bleu)
                for i, point in enumerate(taxi.route[taxi.target_index:], start=taxi.target_index):
                    color = config.GREEN if i % 2 == 0 else config.BLUE
                    pygame.draw.circle(screen, color, (int(point[0]), int(point[1])), 5)
                    if i % 2 == 0:
                        task_index = i // 2
                        if task_index < len(taxi.tasks):
                            task = taxi.tasks[task_index]
                            font = pygame.font.SysFont(None, 20)
                            text = font.render(f"Task {task.id}", True, config.BLACK)                            
                            screen.blit(text, (task.start[0] - 10, task.start[1] - 20))

            # Dessiner le taxi (cercle rouge) et son identifiant
            pygame.draw.circle(screen, config.RED, (int(taxi.position[0]), int(taxi.position[1])), 8)

            font = pygame.font.SysFont(None, 24)
            text = font.render(str(taxi.id), True, (0, 0, 0))
            screen.blit(text, (taxi.position[0] - 10, taxi.position[1] - 20))

    def toggle_pause(self):
        if self.paused:
            # Reprendre : Ajuster last_task_time pour ne pas sauter des tâches
            self.last_task_time += pygame.time.get_ticks() - self.pause_start_time
        else:
            # Mettre en pause : Enregistrer le temps où la pause a commencé
            self.pause_start_time = pygame.time.get_ticks()

        self.paused = not self.paused

def main(resolutionType, isPenalty=False, random_task=True, algo="none"):
    clock_start = pygame.time.get_ticks()
    step = 0
    pygame.init()
    screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
    pygame.display.set_caption("Simulation Allocation en ligne de tâches")
    clock = pygame.time.Clock()

    sim = Simulation(config.WIDTH, config.HEIGHT, config.NUM_TAXIS, config.TASK_INTERVAL, config.NUM_TASKS_SPAWN, resolutionType, isPenalty, random_task, algo)
    print(sim)
    running = True
    tasks_left = True
    taxi_empty = 0
    while running and (sim.task_list != [] or tasks_left):
        tasks_left = True
        dt = clock.tick(config.FPS) / 1000.0  # dt en secondes (60 FPS)
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    sim.toggle_pause()
                elif event.key == pygame.K_ESCAPE:
                    running = False

        sim.update(current_time, dt)
        sim.draw(screen)
        step+=1
        
        taxi_empty = 0
        for taxi in sim.taxis:
            if taxi.tasks == []:
                taxi_empty += 1
        if taxi_empty == len(sim.taxis):
            tasks_left = False
        pygame.display.flip()

    clock_end = pygame.time.get_ticks()
    time_elapsed = (clock_end - clock_start) / 1000  # Temps écoulé en secondes
    mean_cost = sum(sim.mean_route_cost) / len(sim.mean_route_cost)

    if resolutionType != "dcop":
        result = {"resolutionType": resolutionType, "time": time_elapsed, "nombre de tache" : config.NUM_TASKS_SPAWN, "moyenne du cout de route": mean_cost}
        
        try:
            with open("res.json", "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []
        
        data.append(result)
        
        with open("res.json", "w") as f:
            json.dump(data, f, indent=4)
        
        print(f"Step {step}, temps : {time_elapsed}s pour resolutionType = {resolutionType}")

    elif resolutionType == "dcop":
        result_dcop ={"algoDcop": algo, "time": time_elapsed, "nombre de tache": config.NUM_TASKS_SPAWN, "moyenne du cout de route": mean_cost} 


        try:
            with open("res_dcop.json", "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []
        
        data.append(result_dcop)
        
        with open("res_dcop.json", "w") as f:
            json.dump(data, f, indent=4)
        
        print(f"Step {step}, temps : {time_elapsed}s pour resolutionType = {algo}")

    pygame.quit()
    # sys.exit()

def plot_results(type_eval):
    """Affichage sous forme d'histogramme des temps d'exécution par type d'algorithme"""
    try:
        with open("res.json", "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Aucune donnée trouvée.")
        return
    
    # Extraction des données
    algos = [entry["resolutionType"] for entry in data]
    times = [entry["time"] for entry in data]
    mean_costs = [entry["moyenne du cout de route"] for entry in data]
    
    if type_eval == "time":
        # Création de l'histogramme pour le temps
        plt.bar(algos, times, color=['blue', 'green', 'red', 'purple'])
        plt.xlabel("Type d'algorithme")
        plt.ylabel("Temps (secondes)")
        plt.title("Comparaison des performances des algorithmes sur 50 tâches sans pénalité")
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Affichage des valeurs sur les barres
        for i, v in enumerate(times):
            plt.text(i, v + 3, f"{v:.1f}", ha='center', fontsize=10)

    if type_eval == "cost":
        # Création de l'histogramme pour le coût moyen des itinéraires
        plt.bar(algos, mean_costs, color=['blue', 'green', 'red', 'purple'])
        plt.xlabel("Type d'algorithme")
        plt.ylabel("coût moyen des itinéraires (en pixels)")
        plt.title("Comparaison des coûts moyens des itinéraires sur 50 tâches sans pénalité")
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        for i, v in enumerate(mean_costs):
            plt.text(i, v + 3, f"{v:.1f}", ha='center', fontsize=10)
    
    plt.show()


def plot_dcop_results(type_eval):
    """Affichage sous forme d'histogramme des temps d'exécution par type d'algorithme pour dcop"""
    try:
        with open("res_dcop.json", "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Aucune donnée trouvée.")
        return
    
    # Extraction des données
    algos = [entry["algoDcop"] for entry in data]
    times = [entry["time"] for entry in data]
    mean_costs = [entry["moyenne du cout de route"] for entry in data]

    if type_eval == "time":
        # Création de l'histogramme pour le temps
        plt.bar(algos, times, color=['blue', 'green', 'red'])
        plt.xlabel("Type d'algorithme")
        plt.ylabel("Temps (secondes)")
        plt.title("Comparaison des performances des algorithmes sur 50 tâches")
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Affichage des valeurs sur les barres
        for i, v in enumerate(times):
            plt.text(i, v + 3, f"{v:.1f}", ha='center', fontsize=10)

    if type_eval == "cost":
        # Création de l'histogramme pour le coût moyen des itinéraires
        plt.bar(algos, mean_costs, color=['blue', 'green', 'red'])
        plt.xlabel("Type d'algorithme")
        plt.ylabel("coût moyen des itinéraires (en pixels)")
        plt.title("Comparaison des coûts moyens des itinéraires sur 50 tâches")
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        for i, v in enumerate(mean_costs):
            plt.text(i, v + 3, f"{v:.1f}", ha='center', fontsize=10)
    
    plt.show()


if __name__ == "__main__":
    # print("Simulation avec l'algorithme greedy")   
    # main(resolutionType="greedy", isPenalty=True, random_task=False, algo="none")
    # print("Simulation avec l'algorithme PSI")
    # main(resolutionType="PSI", isPenalty=True, random_task=False, algo="none")
    # print("Simulation avec l'algorithme SSI")
    # main(resolutionType="SSI", isPenalty=True, random_task=False, algo="none")
    # print("Simulation avec l'algorithme regret")
    # main(resolutionType="regret", isPenalty=True, random_task=False, algo="none")
    
    # plot_results("time")
    # plot_results("cost")
    # plot_dcop_results("time")
    # plot_dcop_results("cost")
    sys.exit()

