import pygame
import random
import math
import itertools
import sys
from copy import deepcopy

# --- Paramètres de la simulation ---
WIDTH, HEIGHT = 800, 600         # Taille de l'environnement (pixels)
NUM_TAXIS = 5                    # Nombre de taxis
TASK_INTERVAL = 2000             # Intervalle de génération d'une nouvelle tâche en millisecondes
TAXI_SPEED = 100                 # Vitesse du taxi (pixels par seconde)
NUM_TASKS_SPAWN = 5              # Nombre de tâches à générer à chaque intervalle
RED = (255, 0, 0)
GREEN = (0, 255, 0)
ORANGE = (255, 165, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)

# --- Classes de base ---

class Task:
    """Représente une tâche (trajet) avec un point de départ et une destination."""
    def __init__(self, start, destination, id=None):
        self.id = id
        self.start = start          # (x, y)
        self.destination = destination

class Taxi:
    """Un taxi qui se déplace dans l'environnement et exécute des tâches."""
    def __init__(self, id, position):
        self.id = id
        self.position = position    # Position actuelle (x, y)
        self.tasks = []             # Liste des tâches attribuées (dans l'ordre optimal)
        self.route = []             # Liste des points (waypoints) à suivre, calculée par plan_route()
        self.target_index = 0       # Indice du waypoint courant dans self.route
        self.current_route_cost = 0 # Coût total du chemin planifié
        self.isWorking = False      # ici on recupere pour l'affichage si le taxi est entre le depart et la destination d'une tache ou si il va vers le depart d'une tache

    def plan_route(self):
        """
        Recalcule l'ordonnancement optimal des tâches en testant toutes les permutations.
        Le coût d'un ordre est défini par : 
           distance(position initiale, tâche.start) + distance(tâche.start, tâche.destination)
           + distances entre la destination d'une tâche et le début de la suivante.
        """
        if not self.tasks:
            self.route = []
            self.current_route_cost = 0
            self.target_index = 0
            return

        best_order = None
        best_cost = float('inf')
        # Tester toutes les permutations possibles des tâches
        for perm in itertools.permutations(self.tasks):
            cost = 0
            pos = self.position
            for task in perm:
                cost += math.dist(pos, task.start)
                cost += math.dist(task.start, task.destination)
                pos = task.destination
            if cost < best_cost:
                best_cost = cost
                best_order = perm

        # Mettre à jour la liste des tâches selon l'ordre optimal trouvé
        self.tasks = list(best_order)
        self.current_route_cost = best_cost

        # Construire la liste des waypoints : pour chaque tâche, on passe par le départ puis la destination
        self.route = []
        for task in self.tasks:
            self.route.append(task.start)
            self.route.append(task.destination)
        self.target_index = 0

    def add_task(self, task):
        """Ajoute une tâche à la liste et recalcule le planning."""
        self.tasks.append(task)
        self.plan_route()

    def update(self, dt):
        """
        Fait avancer le taxi le long de son itinéraire.
        dt : temps écoulé depuis la dernière mise à jour (en secondes)
        """
        if self.target_index >= len(self.route):
            return  # Plus rien à faire

        target = self.route[self.target_index]
        dx = target[0] - self.position[0]
        dy = target[1] - self.position[1]
        distance = math.hypot(dx, dy)
        
        # Si le taxi est très proche du waypoint, on considère qu'il l'a atteint
        if distance < 1:
            self.position = target
            self.target_index += 1
        else:
            move_distance = TAXI_SPEED * dt
            if move_distance >= distance:
                self.position = target
                self.target_index += 1
            else:
                ratio = move_distance / distance
                self.position = (self.position[0] + dx * ratio, self.position[1] + dy * ratio)
        
        # On définit ici isWorking pour l'affichage
        if self.target_index < len(self.route):
            self.isWorking = (self.target_index % 2 == 1)
        else:
            self.isWorking = False

        # Si le taxi vient de terminer une tâche (c'est-à-dire atteindre une destination)
        # Comme le chemin est [start, destination, start, destination, ...], dès qu'on a atteint
        # le second point (indice impair) d'une tâche, on considère cette tâche comme terminée.
        if self.target_index >= 1 and self.target_index % 2 == 0:
            # Retirer la première tâche accomplie et recalculer l'itinéraire avec les tâches restantes
            if self.tasks:
                self.tasks.pop(0)
                self.plan_route()

class Simulation:
    """Gère l'environnement, la génération de tâches et l'allocation aux taxis."""
    def __init__(self, width, height, num_taxis, task_interval, num_tasks_spawn):
        self.width = width
        self.height = height
        self.taxis = []
        self.num_tasks_spawn = num_tasks_spawn
        for i in range(num_taxis):
            pos = (random.randint(0, width), random.randint(0, height))
            self.taxis.append(Taxi(i, pos))
        self.task_interval = task_interval
        self.last_task_time = 0  # Temps (en ms) de la dernière génération de tâche
        self.task_counter = 0    # Compteur pour assigner des ID uniques aux tâches


    def generate_task(self):
        """Génère une nouvelle tâche avec un départ et une destination aléatoires dans l'environnement."""
        start = (random.randint(0, self.width), random.randint(0, self.height))
        destination = (random.randint(0, self.width), random.randint(0, self.height))
        task = Task(start, destination, self.task_counter)
        self.task_counter += 1
        return task

    def allocate_task(self, task):
        """
        Alloue la tâche au taxi pour lequel l'ajout de cette tâche entraînerait le moindre coût additionnel.
        Pour chaque taxi, on compare :
           coût actuel  vs. coût optimal avec la nouvelle tâche (en testant toutes les permutations).
        """
        best_taxi = None
        best_additional_cost = float('inf')

        for taxi in self.taxis:
            # Coût actuel : si le taxi n'a pas de tâche, le coût est nul
            current_cost = taxi.current_route_cost if taxi.tasks else 0

            # Calculer le coût optimal si on ajoute la nouvelle tâche
            tasks_candidate = taxi.tasks + [task]
            best_candidate_cost = float('inf')
            for perm in itertools.permutations(tasks_candidate):
                cost = 0
                pos = taxi.position
                for tas in perm:
                    cost += math.dist(pos, tas.start)
                    cost += math.dist(tas.start, tas.destination)
                    pos = tas.destination
                if cost < best_candidate_cost:
                    best_candidate_cost = cost

            additional_cost = best_candidate_cost - current_cost
            if additional_cost < best_additional_cost:
                best_additional_cost = additional_cost
                best_taxi = taxi

        if best_taxi is not None:
            best_taxi.add_task(task)

    def greedy_task_assignment(self, taxis, task):
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
        
        # Pour chaque tâche à affecter, on choisit le taxi avec le moindre coût estimé.
        
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
            
            print(f"Taxi {taxi.id} : coût estimé = {cost:.2f} pour la tâche {getattr(task, 'id', 'inconnue')}")
            
            if cost < best_estimated_cost:
                best_estimated_cost = cost
                best_taxi = taxi
        
        print(f"=> Affectation de la tâche {getattr(task, 'id', 'inconnue')} au taxi {best_taxi.id} (coût estimé = {best_estimated_cost:.2f})\n")
        
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


    def update(self, current_time, dt):
        """
        Met à jour la simulation :
         - Génère une nouvelle tâche tous les task_interval millisecondes et l'alloue.
         - Met à jour la position de chaque taxi.
        """
        if current_time - self.last_task_time > self.task_interval:
            new_task = self.generate_task()
            # self.allocate_task(new_task)
            self.greedy_task_assignment(self.taxis, new_task)
            self.last_task_time = current_time

        for taxi in self.taxis:
            taxi.update(dt)

    def draw(self, screen):
        """Affiche l'environnement, les trajets planifiés et les taxis."""
        screen.fill((255, 255, 255))  # fond blanc

        # Pour chaque taxi, dessiner son itinéraire et sa position
        for taxi in self.taxis:
            # Tracer la route planifiée : depuis la position actuelle jusqu'aux waypoints restants
            if taxi.route and taxi.target_index < len(taxi.route):
                points = [taxi.position] + taxi.route[taxi.target_index:]
                if len(points) >= 2:
                    line_color = BLACK if not taxi.isWorking else ORANGE
                    pygame.draw.lines(screen, line_color, False, points, 2)

                # Afficher les waypoints : en vert pour un départ, en bleu pour une destination
                for i, point in enumerate(taxi.route[taxi.target_index:], start=taxi.target_index):
                    color = GREEN if i % 2 == 0 else BLUE
                    pygame.draw.circle(screen, color, (int(point[0]), int(point[1])), 5)

            # Dessiner le taxi (cercle rouge) et son identifiant
            pygame.draw.circle(screen, RED, (int(taxi.position[0]), int(taxi.position[1])), 8)
            font = pygame.font.SysFont(None, 24)
            text = font.render(str(taxi.id), True, (0, 0, 0))
            screen.blit(text, (taxi.position[0] - 10, taxi.position[1] - 20))

def main():
    step = 0
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Simulation Allocation en ligne de tâches (Partie 1)")
    clock = pygame.time.Clock()

    sim = Simulation(WIDTH, HEIGHT, NUM_TAXIS, TASK_INTERVAL, NUM_TASKS_SPAWN)
    running = True

    while running:
        dt = clock.tick(60) / 1000.0  # dt en secondes (60 FPS)
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        sim.update(current_time, dt)
        sim.draw(screen)
        step+=1
        # if(step % 60 == 0):
        #     print(f"Step {step}")
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
