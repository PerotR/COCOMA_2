import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon, FancyArrowPatch
import random
import itertools

# Fonction pour calculer la distance euclidienne entre deux points
def calculate_distance(start, end):
    x1, y1 = start
    x2, y2 = end
    return np.sqrt((x1 - x2)**2 + (y1 - y2)**2)

# Fonction pour afficher la grille avec taxis et tâches
def showgrid(n, taxis, tasks, file_name=None):
    plt.figure(figsize=(10, 10))
    plt.grid(True)

    plt.xlim([0, n])
    plt.ylim([0, n])
    plt.xticks(range(n + 1))
    plt.yticks(range(n + 1))
    ax = plt.gca()
    ax.set_aspect('equal', adjustable='box')

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
        poly = Polygon(triangle, closed=True, color='green')
        ax.add_patch(poly)

        plt.text(cx, cy, f"T{taxi['id']}", fontsize=8, color='black', ha='center', va='center')

    # Dessin des tâches (départ et arrivée)
    for task in tasks:
        sx, sy = task['start']
        ex, ey = task['end']
        start_x, start_y = sy + 0.5, n - sx - 1 + 0.5
        end_x, end_y = ey + 0.5, n - ex - 1 + 0.5

        # Départ (point bleu)
        start_circle = plt.Circle((start_x, start_y), 0.1, color='blue', label='Start')
        ax.add_patch(start_circle)
        # Ajouter l'ID de la tâche au point de départ
        plt.text(start_x, start_y + 0.2, f"M{task['id']}", fontsize=8, color='blue', ha='center', va='center')

        # Arrivée (point rouge)
        end_circle = plt.Circle((end_x, end_y), 0.1, color='red', label='End')
        ax.add_patch(end_circle)
        # Flèche en pointillé reliant départ et arrivée
        arrow = FancyArrowPatch(
            (start_x, start_y), (end_x, end_y),
            arrowstyle='->',
            mutation_scale=10,
            linewidth=1,
            linestyle='dashed',
            color='gray',
            alpha=0.5
        )
        ax.add_patch(arrow)

    # Gestion des légendes pour éviter les doublons
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys(), loc='upper right')

    # Suppression des étiquettes d'axe
    ax.axes.xaxis.set_ticklabels([])
    ax.axes.yaxis.set_ticklabels([])
    plt.grid(True)

    # Sauvegarde ou affichage
    if file_name:
        plt.savefig(file_name)
    else:
        plt.show()

# Générer une nouvelle tâche avec départ, arrivée et coût
def generate_task(n, task_id, available_positions):
    # Générer un point de départ et un point d'arrivée distincts
    start_pos = available_positions.pop()
    end_pos = available_positions.pop()
    start = (start_pos // n, start_pos % n)
    end = (end_pos // n, end_pos % n)
    cost = calculate_distance(start, end)
    return {'id': task_id, 'start': start, 'end': end, 'cost': cost, 'assigned': False}

# Fonction pour planifier les tâches et trouver l'ordonnancement optimal
def schedule_tasks(taxis, tasks):
    num_tasks = len(tasks)
    
    # Créer une liste d'index de tâches
    task_indices = list(range(num_tasks))
    
    best_order = None
    best_cost = float('inf')
    
    # Tester toutes les permutations possibles des tâches
    for order in itertools.permutations(task_indices):
        total_cost = 0
        for i in range(len(order) - 1):
            task_i = tasks[order[i]]
            task_j = tasks[order[i + 1]]
            total_cost += calculate_distance(task_i['end'], task_j['start'])  # Coût de déplacement entre tâches
        
        # Ajouter le coût des tâches elles-mêmes
        for i in order:
            total_cost += tasks[i]['cost']
        
        # Si ce coût est meilleur que le précédent, on le garde
        if total_cost < best_cost:
            best_cost = total_cost
            best_order = order

    return best_order, best_cost

# Simulation de l'environnement
def run_simulation(n, num_taxis, m, num_steps):
    taxis = [{'id': i + 1, 'position': (random.randint(0, n-1), random.randint(0, n-1))} for i in range(num_taxis)]
    tasks = []
    task_count = 0  # Compteur de tâches pour générer un ID unique

    available_positions = list(range(n * n))
    random.shuffle(available_positions)  # Mélanger les positions disponibles

    # Positionner les taxis
    for taxi in taxis:
        pos = available_positions.pop()
        taxi['position'] = (pos // n, pos % n)

    # Simulation
    for step in range(num_steps):
        print(f"\nStep {step + 1}:")

        # Générer des tâches
        num_tasks_to_generate = max(m, num_taxis)
        new_tasks = []
        for _ in range(num_tasks_to_generate):
            if len(available_positions) < 2:  # Vérifier qu'il reste suffisamment de positions
                print("Not enough positions available to generate a task.")
                break
            task = generate_task(n, task_count, available_positions)
            new_tasks.append(task)
            task_count += 1  # Incrémenter le compteur de tâches

        tasks.extend(new_tasks)
        for task in new_tasks:
            print(f"New task generated: M{task['id']} Start: {task['start']}, End: {task['end']}, Cost: {task['cost']:.2f}")

        # Planification des tâches
        best_order, best_cost = schedule_tasks(taxis, tasks)
        print(f"Best order of tasks: {best_order}")
        print(f"Best total cost: {best_cost:.2f}")

        # Afficher toutes les tâches
        print("Tasks:")
        for task in tasks:
            status = "Assigned" if task['assigned'] else "Unassigned"
            print(f"  - ID: M{task['id']}, Cost: {task['cost']:.2f}, Status: {status}")

        # Afficher la grille
        showgrid(n, taxis, tasks)

