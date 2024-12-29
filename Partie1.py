import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon, Rectangle, Circle
import random

# Fonction pour générer les tâches
def generate_task(n, task_count, taxis, tasks, available_positions):
    while True:
        if not available_positions:
            # Si toutes les positions sont utilisées, on les regénère et les mélange
            available_positions = list(range(n * n))
            random.shuffle(available_positions)  # Mélanger les positions disponibles
        pos = available_positions.pop()
        x, y = divmod(pos, n)  # Convertir le numéro linéaire en coordonnées x, y
        # Vérifier si la case est déjà occupée par un taxi ou une autre tâche
        if not any(taxi['position'] == (x, y) for taxi in taxis) and not any(task['position'] == (x, y) for task in tasks):
            return {'id': task_count + 1, 'position': (x, y)}

# Fonction pour calculer la distance euclidienne entre deux points
def calculate_distance(taxi_pos, task_pos):
    tx, ty = taxi_pos
    tx_dest, ty_dest = task_pos
    return np.sqrt((tx - tx_dest)**2 + (ty - ty_dest)**2)

# Planification des tâches : assigner les tâches aux taxis en minimisant les déplacements
def plan_trips(taxis, tasks):
    allocations = {}
    for task in tasks:
        best_taxi = None
        min_distance = float('inf')
        for taxi in taxis:
            dist = calculate_distance(taxi['position'], task['position'])
            if dist < min_distance:
                min_distance = dist
                best_taxi = taxi
        if best_taxi:
            # Assigner la tâche au meilleur taxi
            allocations[task['id']] = best_taxi['id']
            best_taxi['position'] = task['position']  # Déplacer le taxi à la position de la tâche
    return allocations

# Fonction pour afficher la grille avec les taxis et les tâches
def showgrid(n, taxis, tasks, allocations=None, file_name=None):
    plt.figure(figsize=(10, 10))
    plt.grid()

    plt.xlim([0, n])
    plt.ylim([0, n])
    plt.xticks(range(n + 1))
    plt.yticks(range(n + 1))
    ax = plt.gca()
    ax.set_aspect('equal', adjustable='box')

    patches_by_cell = {}  # Nouveau dictionnaire pour stocker les patchs par case

    def clear_cell(ax, patches_by_cell, cell_position):
        """Efface tous les patchs d'une case spécifique."""
        if cell_position in patches_by_cell:
            for patch in patches_by_cell[cell_position]:
                patch.remove()  # Supprimer le patch de l'axe
            del patches_by_cell[cell_position]  # Supprimer l'entrée du dictionnaire
            plt.draw()  # Redessiner la figure pour refléter les changements

    # Dessin des taxis (sous forme de triangles)
    for taxi in taxis:
        x, y = taxi['position']
        cx, cy = y + 0.5, n - x - 1 + 0.5
        size = 0.5  # Taille relative du triangle
        triangle = [
            (cx, cy + size / 2),  # Sommet supérieur
            (cx - size / 2, cy - size / 2),  # Coin inférieur gauche
            (cx + size / 2, cy - size / 2)   # Coin inférieur droit
        ]
        poly = Polygon(triangle, closed=True, color='orange')
        ax.add_patch(poly)

        # Stocker dans le dictionnaire
        cell_key = (x, y)
        patches_by_cell.setdefault(cell_key, []).append(poly)

        plt.text(cx, cy, f"T{taxi['id']}", fontsize=8, color='black', ha='center', va='center')

    # Dessin des tâches (sous forme de carrés verts)
    for task in tasks:
        x, y = task['position']
        cx, cy = y + 0.5, n - x - 1 + 0.5  # Centrer la tâche sur la case
        size = 0.5  # Taille relative du carré
        square = Rectangle((cx - size / 2, cy - size / 2), size, size, color='green')
        ax.add_patch(square)

        # Stocker dans le dictionnaire
        cell_key = (x, y)
        patches_by_cell.setdefault(cell_key, []).append(square)

        # Vérifier si un taxi est aussi sur la même case
        task_and_taxi = [taxi for taxi in taxis if taxi['position'] == task['position']]
        
        if task_and_taxi:
            # Effacer tous les patchs de cette case
            clear_cell(ax, patches_by_cell, cell_key)

            # Ajouter un cercle bleu et le texte combiné ID taxi + ID tâche
            circle = Circle((cx, cy), 0.25, color='blue')
            ax.add_patch(circle)

            # Ajouter le cercle au dictionnaire
            patches_by_cell.setdefault(cell_key, []).append(circle)

            # Texte combiné : Taxi ID et Tâche ID
            combined_text = f"T{task_and_taxi[0]['id']}M{task['id']}"
            plt.text(cx, cy, combined_text, fontsize=8, color='white', ha='center', va='center')
        else:
            # Si pas de taxi, afficher normalement la tâche
            plt.text(cx, cy, f"M{task['id']}", fontsize=8, color='black', ha='center', va='center')

    # Suppression des étiquettes d'axe
    ax.axes.xaxis.set_ticklabels([])
    ax.axes.yaxis.set_ticklabels([])
    plt.grid(True)

    # Sauvegarde ou affichage
    if file_name:
        plt.savefig(file_name)
    else:
        plt.show()


# Simulation de l'environnement
def run_simulation(n, num_taxis, task_frequency, num_steps):
    # Initialiser les taxis et les tâches
    taxis = [{'id': i + 1, 'position': (random.randint(0, n-1), random.randint(0, n-1))} for i in range(num_taxis)]
    tasks = []
    task_count = 0  # Compteur de tâches pour générer un ID unique
    allocations = {}

    # Créer une liste de toutes les positions disponibles sur la grille
    available_positions = list(range(n * n))
    random.shuffle(available_positions)  # Mélanger les positions disponibles

    # Positionner les taxis de manière à éviter les chevauchements
    for taxi in taxis:
        pos = available_positions.pop()
        taxi['position'] = (pos // n, pos % n)

    # Simulation de l'environnement pendant `num_steps` pas de temps
    for step in range(num_steps):
        print(f"Step {step + 1}:")

        # Générer une nouvelle tâche tous les `task_frequency` pas de temps
        if step % task_frequency == 0:
            task = generate_task(n, task_count, taxis, tasks, available_positions)
            tasks.append(task)
            task_count += 1  # Incrémenter le compteur de tâches
            print(f"New task generated: M{task['id']} at position {task['position']}")

        # Afficher la grille à l'étape initiale (step = 0) avec taxis et tâches
        if step == 0:
            showgrid(n, taxis, tasks)

        # Planifier les trajets à partir de l'étape 2
        if step == 1:
            allocations = plan_trips(taxis, tasks)
            showgrid(n, taxis, tasks, allocations)
        elif step >= 2:
            allocations = plan_trips(taxis, tasks)
            showgrid(n, taxis, tasks, allocations)

# Paramètres de la simulation
n = 10  # Taille de l'environnement (n x n)
num_taxis = 3  # Nombre de taxis
task_frequency = 5  # Fréquence d'arrivée des tâches (toutes les 5 étapes)
num_steps = 2  # Nombre de pas de temps

# Exécution de la simulation
run_simulation(n, num_taxis, task_frequency, num_steps)
