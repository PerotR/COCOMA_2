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

class Simulation:
    """Gère l'environnement, la génération de tâches et l'allocation aux taxis."""
    def __init__(self, width, height, num_taxis, task_interval, num_tasks_spawn):
        self.width = width
        self.height = height
        self.taxis = []
        self.num_tasks_spawn = num_tasks_spawn
        self.paused = False
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

    def greedy_task_assignment(n, taxis, tasks):
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
                list_estimated_cost.append(taxi.total_route_cost)

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
                self.greedy_task_assignment(self.taxis, new_tasks)

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

def main():
    # step = 0
    pygame.init()
    screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
    pygame.display.set_caption("Simulation Allocation en ligne de tâches (Partie 1)")
    clock = pygame.time.Clock()

    sim = Simulation(config.WIDTH, config.HEIGHT, config.NUM_TAXIS, config.TASK_INTERVAL, config.NUM_TASKS_SPAWN)
    print(sim)
    running = True

    while running:
        dt = clock.tick(config.FPS) / 1000.0  # dt en secondes (60 FPS)
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                sim.toggle_pause()

        sim.update(current_time, dt)
        sim.draw(screen)
        # step+=1
        # if(step % 60 == 0):
        #     print(f"Step {step}")
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
