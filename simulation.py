# simulation.py
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
    def __init__(self, width, height, num_taxis, task_interval, num_tasks_spawn, resolutionType):
        self.width = width
        self.height = height
        self.taxis = []
        self.num_tasks_spawn = num_tasks_spawn
        self.paused = False
        self.resolutionType = resolutionType
        for i in range(num_taxis):
            pos = (random.randint(0, width), random.randint(0, height))
            self.taxis.append(Taxi(i, pos))
        self.task_interval = task_interval
        self.last_task_time = -10000  # Temps (en ms) de la dernière génération de tâche
        self.task_counter = 0    # Compteur pour assigner des ID uniques aux tâches



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

    def greedy_task_assignment(self, taxis, tasks):
        """
        Affecte chacune des tâches de la liste tasks au taxi le plus proche
        (en tenant compte du temps qu'il met à finir ses tâches déjà assignées).
        
        Pour un taxi donné, le coût estimé est calculé en FIFO :
        - Si le taxi est inactif (aucune tâche en attente), le coût est 
            distance(position du taxi, tâche.start) + distance(tâche.start, tâche.destination)
        - Sinon, le coût est égal à la somme des distances le long de la file d'attente 
            (en partant de la position actuelle du taxi) + 
            distance(dernier point atteint, tâche.start) + distance(tâche.start, tâche.destination)
        
        La fonction affiche l'état initial et final via showgrid (à définir ailleurs).
        """
        

        all_permutation = [list(task) for task in itertools.permutations(tasks)]

        taxi_tmp = deepcopy(taxis)

        i = 0
        # for permutation in all_permutation:
        #     i+=1
        #     print(f"Permutation : {i}")
        #     for t in permutation:
        #         print(f"Tâche {getattr(t, 'id', 'inconnue')} : départ = {t.start}, destination = {t.destination}")

        best_Permutation = None
        for permutation in all_permutation:
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
                    # en suivant l'ordre FIFO des tâches déjà en file.
                    cost = 0.0
                    current_pos = taxi.position
                    
                    # Parcourt des tâches déjà affectées (exécutées dans l'ordre d'arrivée)
                    for t in taxi.tasks:
                        cost += math.dist(current_pos, t.start) + math.dist(t.start, t.destination)
                        current_pos = t.destination
                    
                    # Coût pour la nouvelle tâche
                    cost += math.dist(current_pos, task.start) + math.dist(task.start, task.destination)
                    
                    # print(f"Taxi {taxi.id} : coût estimé = {cost:.2f} pour la tâche {getattr(task, 'id', 'inconnue')}")
                    
                    if cost < best_estimated_cost:
                        best_estimated_cost = cost
                        best_taxi = taxi

                best_taxi.tasks.append(task)

            for taxi in taxi_tmp: # On calcule le coût de la permutation
                # print(f"position du taxi : {taxi.position} et taches du taxi {taxi.id} : ")
                # for t in taxi.tasks:
                #     print(f"Tâche {getattr(t, 'id', 'inconnue')} : départ = {t.start}, destination = {t.destination}")
                taxi.calculate_total_route_cost()
                list_estimated_cost.append(taxi.current_route_cost)

            longest_route = max(list_estimated_cost) # On récupère le coût le plus long entre les taxis pour avoir le coût de la permutation

            # print(f"Coût de la permutation : {longest_route}")

            if longest_route < best_allocation_cost: # On compare le coût de la permutation avec le meilleur coût trouvé
                best_allocation_cost = longest_route
                best_Permutation = permutation

        # print("MEILLEURE PERMUTATION")
        # print(f"Meilleur coût : {best_allocation_cost}")
        # for t in permutation:
        #     print(f"Tâche {getattr(t, 'id', 'inconnue')} : départ = {t.start}, destination = {t.destination}")

        for task in best_Permutation:
            best_taxi = None
            best_estimated_cost = float('inf')

            for taxi in taxis:
                # Calcul du coût de réalisation si l'on affecte cette tâche au taxi,
                # en suivant l'ordre FIFO des tâches déjà en file.
                cost = 0.0
                current_pos = taxi.position
                
                # Parcourt des tâches déjà affectées (exécutées dans l'ordre d'arrivée)
                for t in taxi.tasks:
                    cost += math.dist(current_pos, t.start) + math.dist(t.start, t.destination)
                    current_pos = t.destination
                
                # Coût pour la nouvelle tâche
                cost += math.dist(current_pos, task.start) + math.dist(task.start, task.destination)
                
                # print(f"Taxi {taxi.id} : coût estimé = {cost:.2f} pour la tâche {getattr(task, 'id', 'inconnue')}")
                
                if cost < best_estimated_cost:
                    best_estimated_cost = cost
                    best_taxi = taxi


            # print(f"=> Affectation de la tâche {getattr(task, 'id', 'inconnue')} au taxi {best_taxi.id} (coût estimé = {best_estimated_cost:.2f})\n")
            
            # Affectation de la tâche au taxi choisi (ajout en fin de file d'attente)
            best_taxi.tasks.append(task)
            
            # Mise à jour de l'itinéraire du taxi en mode FIFO :
            # Si le taxi n'avait pas d'itinéraire (pas de tâches en attente), on le crée.
            # Sinon, on ajoute simplement les deux points (start et destination) à la suite.
            if not best_taxi.route:
                best_taxi.route = [task.start, task.destination]
                best_taxi.target_index = 0
            else:
                best_taxi.route.extend([task.start, task.destination])
            
            # On peut aussi mettre à jour le coût total estimé de la file (pour information)
            current_pos = best_taxi.position
            route_cost = 0.0
            for t in best_taxi.tasks:
                route_cost += math.dist(current_pos, t.start) + math.dist(t.start, t.destination)
                current_pos = t.destination
            best_taxi.current_route_cost = route_cost

        # for taxi in taxis:
        #     print(f"taches du taxi {taxi.id} : ")
        #     for t in taxi.tasks:
        #         print(f"Tâche {getattr(t, 'id', 'inconnue')} : départ = {t.start}, destination = {t.destination}")
        #     print(f"Coût total estimé : {taxi.current_route_cost:.2f}\n")


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
                f.write(f"      function: {math.dist(tasks[0].start, tasks[0].destination)+(math.dist(taxis[i].position,tasks[0].start)if not taxis[i].isWorking else math.dist(taxis[i].tasks[taxis[i].target_index//2].destination,tasks[0].start))} if Tache_{tasks[0].id} =='T{taxis[i].id}'")
                for j in range(1,len(tasks)-1):
                    f.write(f" else {math.dist(tasks[j].start, tasks[j].destination)+(math.dist(taxis[i].position,tasks[j].start)if not taxis[i].isWorking else math.dist(taxis[i].tasks[taxis[i].target_index//2].destination,tasks[j].start))} if Tache_{tasks[j].id} =='T{taxis[i].id}'")
                if len(tasks)>1:
                    f.write(f" else {math.dist(tasks[-1].start, tasks[-1].destination)+(math.dist(taxis[i].position,tasks[-1].start)if not taxis[i].isWorking else math.dist(taxis[i].tasks[taxis[i].target_index//2].destination,tasks[-1].start))}")
                f.write("\n")
            
            f.write("\n")
            f.write(f"agents: \n")
            for i in range(len(tasks)):
                f.write(f"   Tache_{tasks[i].id}: \n")
                f.write("      capacity: 1 \n")

    def solve_dcop(self, yaml_file):
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

    def PSI_task_assignment(self, taxis, tasks):
        return

    def insertion_heuristic(self, taxi, task):
        """simule l'insertion d'une tâche dans la liste des tâches d'un taxi"""

        taxi.calculate_total_route_cost()
        current_route_cost = taxi.current_route_cost


        if not taxi.tasks:
            return math.dist(taxi.position, task.start) + math.dist(task.start, task.destination), 0
        

        best_cost_with_insertion = float('inf')
        best_index = 0

        for pos in range(len(taxi.tasks) + 1):
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

        print(f"tache {task.id} insérée au taxi {taxi.id} à la position {best_index} avec un coût de {gap_cost:.2f}")

        
        return gap_cost, best_index



    def SSI_task_assignment(self, taxis, tasks):
        """Enchères sequentielles, où les offres sont réalisées itérativement sur les items"""
        bid = 0
        index = 0

        for task in tasks:
            best_taxi = None
            best_bid = float('inf')
            for taxi in taxis:
                bid, index = self.insertion_heuristic(taxi, task)
                # print(f"Taxi {taxi.id} : coût marginal pour la tâche {task.id} = {bid:.2f}")
                if bid < best_bid:
                    best_bid = bid
                    best_taxi = taxi 
                    best_index = index         
            
            if best_taxi:
                best_taxi.tasks.insert(best_index, task)
                best_taxi.allow_reordering = False
                best_taxi.build_route_from_current_tasks()
                # print(f"=> Tâche {task.id} attribuée au taxi {best_taxi.id} (coût marginal = {best_bid:.2f})\n")


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

        print("Tâches triées par regret décroissant :")
        for tr in task_regrets:
            print(f"Tâche {tr[0].id} : regret = {tr[1]:.2f}")

        return [tr[0] for tr in task_regrets] # On retourne seulement les tâches dans l'ordre décroissant des regrets

    def regret_task_assignment(self, taxis, tasks):

        ordered_tasks = self.calculate_regret(taxis, tasks)

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

                    
                print(f"=> Tâche {task.id} attribuée au taxi {best_taxi.id} (coût marginal = {best_bid:.2f})\n")

    def __repr__(self):
        return f"Simulation(width={self.width}, height={self.height}, num_taxis={len(self.taxis)}, task_interval={self.task_interval}, num_tasks_spawn={self.num_tasks_spawn})"

            


    def update(self, current_time, dt):
        """
        Met à jour la simulation :
         - Génère une nouvelle tâche tous les task_interval millisecondes et l'alloue.
         - Met à jour la position de chaque taxi.
        """
        if not self.paused:
            if current_time - self.last_task_time > self.task_interval:
                new_tasks = self.generate_task()
                match self.resolutionType:
                    case "greedy":
                        self.greedy_task_assignment(self.taxis, new_tasks)
                    case "dcop":
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

                #Pour python 3.8
                # if self.resolutionType== "greedy":
                #     self.greedy_task_assignment(self.taxis, new_tasks)
                # elif self.resolutionType=="dcop":
                #     self.generate_dcop(self.taxis, new_tasks, "dcop.yaml")
                #     self.toggle_pause()
                #     allocation=self.solve_dcop("dcop.yaml")
                #     print(allocation['assignment'])
                #     self.attribution_dcop(new_tasks, self.taxis, allocation['assignment'])
                #     self.toggle_pause()
                
                self.last_task_time = current_time

            for taxi in self.taxis:
                taxi.update(dt)

    def draw(self, screen):
        """Affiche l'environnement, les trajets planifiés et les taxis."""
        screen.fill(config.WHITE)  # fond blanc

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
                    # if i % 2 == 0:
                    #     task_index = i // 2
                    #     if task_index < len(taxi.tasks):
                    #         task = taxi.tasks[task_index]
                    #         font = pygame.font.SysFont(None, 20)
                    #         text = font.render(f"Task {task.id}", True, config.BLACK)                            
                    #         screen.blit(text, (task.start[0] - 10, task.start[1] - 20))

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

def main(resolutionType):
    # step = 0
    pygame.init()
    screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
    pygame.display.set_caption("Simulation Allocation en ligne de tâches (Partie 1)")
    clock = pygame.time.Clock()

    sim = Simulation(config.WIDTH, config.HEIGHT, config.NUM_TAXIS, config.TASK_INTERVAL, config.NUM_TASKS_SPAWN, resolutionType)
    print(sim)
    running = True

    while running:
        dt = clock.tick(config.FPS) / 1000.0  # dt en secondes (60 FPS)
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    sim.toggle_pause()
                elif event.key == pygame.K_ESCAPE:  # Raccourci clavier pour arrêter
                    running = False

        sim.update(current_time, dt)
        sim.draw(screen)
        # step+=1
        # if(step % 60 == 0):
        #     print(f"Step {step}")
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main(resolutionType="regret")
