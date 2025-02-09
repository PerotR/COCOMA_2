import math
import itertools
import config

class Taxi:
    """Un taxi qui se déplace dans l'environnement et exécute des tâches."""
    def __init__(self, id, position):
        self.id = id                 # Identifiant unique du taxi
        self.position = position     # Position actuelle (x, y)
        self.tasks = []              # Liste des tâches attribuées (dans l'ordre optimal), self.tasks = [task1, task2, ...]
        self.route = []              # Liste des points (waypoints) à suivre, calculée par plan_route(), self.route = [start, destination, start, destination, ...]
        self.target_index = 0        # Indice du waypoint courant dans self.route
        self.current_route_cost = 0  # Coût total du chemin planifié
        self.isWorking = False       # ici on recupere pour l'affichage si le taxi est entre le depart et la destination d'une tache ou si il va vers le depart d'une tache
        self.allow_reordering = True # On permet de réordonner les tâches par défaut avec plan_route()

        
        

    def calculate_total_route_cost(self): 
        """On calcule le coût total du chemin planifié, 
        je l'ai utilisé pour la fonction greedy_task_assignment, 
        pour avoir accès au coût total de chaque taxi sans faire plan_route"""
        self.current_route_cost = 0
        pos = self.position
        for task in self.tasks:
            self.current_route_cost += math.dist(pos, task.start) + math.dist(task.start, task.destination)
            pos = task.destination


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

    def build_route_from_current_tasks(self):
        """Construit la route selon l'ordre actuel des tâches (sans permutations)."""

        self.route = []
        current_pos = self.position
        self.current_route_cost = 0
        
        for task in self.tasks:
            self.route.append(task.start)
            self.route.append(task.destination)
            self.current_route_cost += math.dist(current_pos, task.start) + math.dist(task.start, task.destination)
            current_pos = task.destination
        
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
            move_distance = config.TAXI_SPEED * dt
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
                if self.allow_reordering:
                    self.plan_route()
                else:
                    self.build_route_from_current_tasks()
                    

    
    def __repr__(self):
        return f"Taxi(id={self.id}, position={self.position}, tasks={self.tasks})"

