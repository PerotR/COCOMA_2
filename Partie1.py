import math
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon, FancyArrowPatch
import random
import itertools
from copy import deepcopy

# Fonction pour calculer la distance euclidienne entre deux points
def calculate_distance(start, end):
    x1, y1 = start
    x2, y2 = end
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

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
    task_positions = {}

    for task in tasks:
        sx, sy = task['start']
        ex, ey = task['end']
        start_x, start_y = sy + 0.5, n - sx - 1 + 0.5
        end_x, end_y = ey + 0.5, n - ex - 1 + 0.5

        # Gestion des positions multiples pour départ
        if (start_x, start_y) not in task_positions:
            task_positions[(start_x, start_y)] = []
        task_positions[(start_x, start_y)].append(f"M{task['id']}(S)")

        # Gestion des positions multiples pour arrivée
        if (end_x, end_y) not in task_positions:
            task_positions[(end_x, end_y)] = []
        task_positions[(end_x, end_y)].append(f"M{task['id']}(E)")

        # Choisir la couleur en fonction du nombre de tâches
        if len(task_positions[(start_x, start_y)]) > 1:
            start_color = 'orange'
        else:
            start_color = 'blue'

        if len(task_positions[(end_x, end_y)]) > 1:
            end_color = 'orange'
        else:
            end_color = 'red'

        # Départ (point bleu ou orange)
        start_circle = plt.Circle((start_x, start_y), 0.1, color=start_color, label='Start')
        ax.add_patch(start_circle)

        # Arrivée (point rouge ou orange)
        end_circle = plt.Circle((end_x, end_y), 0.1, color=end_color, label='End')
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

    # Afficher les IDs des tâches multiples sur les cases correspondantes
    for (x, y), labels in task_positions.items():
        label_text = "\n".join(labels)
        plt.text(x, y + 0.2, label_text, fontsize=6, color='purple', ha='center', va='center')

    # Ajouter une légende fixe pour les couleurs
    handles = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=10),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', markersize=10)
    ]
    labels = ['Start (Blue)', 'End (Red)', 'multiple tasks (Orange)']

    plt.legend(handles, labels, loc='upper left', bbox_to_anchor=(1,1), borderaxespad=0.)

    # Suppression des étiquettes d'axe
    ax.axes.xaxis.set_ticklabels([])
    ax.axes.yaxis.set_ticklabels([])

    # Sauvegarde ou affichage
    if file_name:
        plt.savefig(file_name, bbox_inches='tight')  # Utilisation de 'bbox_inches' pour bien inclure la légende
    else:
        plt.show()



def generate_task(n, task_id, available_positions, used_tasks):

    isGenerated = True

    print(f"available_positions: {available_positions}")
    print(f"used_tasks: {used_tasks}")

    # Créer une liste temporaire des positions valides de taille (((n*n)-num_taxis)*((n*n)-num_taxis-1))
    valid_tasks = [ 
        (start_pos_tmp, end_pos_tmp)
        for start_pos_tmp in available_positions
        for end_pos_tmp in available_positions
        if start_pos_tmp != end_pos_tmp and (start_pos_tmp, end_pos_tmp) not in used_tasks
    ]

    # print(f"valid_tasks: {valid_tasks}, len(valid_tasks): {len(valid_tasks)}") #attention tableau de taille ((n-num_taxis)*(n-num_taxis-1))
    print(f"len(valid_tasks): {len(valid_tasks)}")

    # verif si on peut generer une tache
    if len(valid_tasks) == 0:
        isGenerated = False
        return isGenerated, None

    start_pos, end_pos = random.choice(valid_tasks)

    start = (start_pos // n, start_pos % n)
    end = (end_pos // n, end_pos % n)

    used_tasks.append((start_pos, end_pos))

    print(f"start_pos: {start_pos}, end_pos: {end_pos}")
    print(f"start: {start}, end: {end}")

    cost = calculate_distance(start, end)
    print(f"cost: {cost:.2f}")

    return isGenerated, {'id': task_id, 'start': start, 'end': end, 'cost': cost, 'assigned': -1}

    


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

def greedy_task_assignment(n, taxis, tasks):

    all_permutations = [list(p) for p in itertools.permutations(tasks)]
    best_permutation_cost = float('inf')
    best_permutation = None

    showgrid(n, taxis, tasks)
    
    initial_taxis = deepcopy(taxis) # sauvegarde des taxis initiaux

    # all_permutations = [[{'id': 0, 'start': (1, 1), 'end': (3, 3), 'cost': 4.24, 'assigned': -1}, {'id': 4, 'start': (0, 3), 'end': (4, 2), 'cost': 7.21, 'assigned': -1}, {'id': 2, 'start': (4, 0), 'end': (2, 1), 'cost': 2.83, 'assigned': -1}, {'id': 1, 'start': (3, 3), 'end': (0, 4), 'cost': 3.61, 'assigned': -1}, {'id': 3, 'start': (2, 1), 'end': (1, 4), 'cost': 3.61, 'assigned': -1}]]

    for permutation in all_permutations:

        print("************************************DEBUT PERMUTATION************************************\n")
        
        tasks = deepcopy(permutation)
        taxis = deepcopy(initial_taxis)
        total_cost_permutation = 0.0

        for task in tasks:
            if task['assigned'] != -1:
                continue
            
            best_taxi = None
            best_cost = float('inf')

            for taxi in taxis:
                total_cost = 0.0
                list_task_cost = 0.0
                dist_cost = calculate_distance(taxi['position'], task['start'])
                task_cost = task['cost']
                for t in taxi['tasks']:
                    list_task_cost += tasks[t]['cost'] + calculate_distance(tasks[t]['end'], task['start']) 
                total_cost = dist_cost + task_cost + list_task_cost

                print(f"dist_cost: {dist_cost:.2f}, task_cost: {task_cost:.2f}, list_task_cost: {list_task_cost:.2f}, total_cost: {total_cost:.2f} pour taxi: {taxi['id']} et task: {task['id']}")

                if total_cost < best_cost:
                    best_cost = total_cost
                    best_taxi = taxi
                
            task['assigned'] = best_taxi['id']
            best_taxi['tasks'].append(task['id'])

            print(f"le taxi {best_taxi['id']} a pris la tache {task['id']}")
            print(f"best_cost: {best_cost:.2f}")

            # showgrid(n, taxis, tasks)

            best_taxi['position'] = task['end']

            # ici on veut prendre le plus elevé des best_cost, ce n'est pas un cumul. On prend la valeur la plus elevée de la liste de tache d'un taxi qui sera le plus rapide à effectuer cet ensemble de taches
            if total_cost_permutation < best_cost:
                total_cost_permutation = best_cost
                

            print(f"total_cost_permutation: {total_cost_permutation:.2f}")

            print("ensemble de taxis: ", taxis)

        if total_cost_permutation < best_permutation_cost:
            best_permutation_cost = total_cost_permutation
            best_permutation = tasks
            print(f"best_permutation_cost: {best_permutation_cost:.2f}")
            print(f"best_permutation: {best_permutation}")

        print("************************************FIN PERMUTATION************************************\n")

    print(f"best_permutation: {best_permutation}")
    print(f"best_permutation_cost: {best_permutation_cost:.2f}")

    # showgrid(n, taxis, tasks)

    return best_permutation_cost
                    


# Simulation de l'environnement
def run_simulation(n, num_taxis, max_task_gen, num_steps):

    #vérification
    if max_task_gen < num_taxis:
        print("Error: max_task_gen must be greater than or equal to num_taxis.")
        return

    isGenerated = True # Indicateur si la tache a ete generee
    end = False # Indicateur de fin de simulation pour arreter les step si plus de taches a generer
    taxis = [{'id': i + 1, 'position': (0,0), 'tasks' : []} for i in range(num_taxis)]
    # print(f"taxis: {taxis}")

    tasks = []
    task_count = 0  # Compteur de tâches pour générer un ID unique

    used_tasks = []  # Liste des positions utilisées pour les tâches
    available_positions = list(range(n * n))
    random.shuffle(available_positions)  # Mélanger les positions disponibles pour le positionnement aléatoire

    print(f"available_positions: {available_positions}")

    # Positionner les taxis
    for taxi in taxis:
        pos = available_positions.pop() # on prend la derniere position de la liste melangée pour placer les taxis
        taxi['position'] = (pos // n, pos % n)

    print(f"taxis: {taxis}")

    # Simulation
    for step in range(num_steps):
        print(f"\nStep {step + 1}:")

        # Générer des tâches
        num_tasks_to_generate = random.randint(num_taxis, max_task_gen)
        print(f"Generating {num_tasks_to_generate} new tasks...")
        new_tasks = []
        for _ in range(num_tasks_to_generate):
            isGenerated, task = generate_task(n, task_count, available_positions, used_tasks)
            if not isGenerated:
                print("No more tasks can be generated.")
                end = True
                break
            new_tasks.append(task)
            task_count += 1  # Incrémenter le compteur de tâches

        tasks.extend(new_tasks)
        # print(f"tasks: {tasks}")
        for task in new_tasks:
            print(f"New task generated: M{task['id']} Start: {task['start']}, End: {task['end']}, Cost: {task['cost']:.2f}")

        # Afficher toutes les tâches
        print("Tasks:")
        for task in tasks:
            print(f"  - ID: M{task['id']}, Cost: {task['cost']:.2f}, Status: {task['assigned']}")
        
        best_cost = greedy_task_assignment(n, taxis, tasks)

        print(f"Best total cost: {best_cost:.2f}")
        print("taxis: ", taxis)

        # Afficher la grille
        showgrid(n, taxis, tasks)

        if end:
            return # arreter la simulation si plus de taches a generer

        

# run_simulation(5, 3, 3, 2)

taxis_test = [{'id': 1, 'position': (1, 0), 'tasks': []}, {'id': 2, 'position': (4, 4), 'tasks': []}, {'id': 3, 'position': (0, 2), 'tasks': []}]

tasks_test = [
    {'id': 0, 'start': (1, 1), 'end': (3, 3), 'cost': 4.24, 'assigned': -1},
    {'id': 1, 'start': (3, 3), 'end': (0, 4), 'cost': 3.61, 'assigned': -1},
    {'id': 2, 'start': (4, 0), 'end': (2, 1), 'cost': 2.83, 'assigned': -1},
    {'id': 3, 'start': (2, 1), 'end': (1, 4), 'cost': 3.61, 'assigned': -1},
    {'id': 4, 'start': (0, 3), 'end': (4, 2), 'cost': 7.21, 'assigned': -1}
]

#best_cost = greedy_task_assignment(5, taxis_test, tasks_test)


#-----------------------------------TESTS-----------------------------------#

# start = math.dist((479, 44), (226, 126))
# res1 = calculate_distance((226, 126), (474, 76))
# res = start + res1
# print(f"res: {res:.2f}")

# dist = calculate_distance((114, 332), (473, 439))
# res2 = calculate_distance((473, 439),(233, 431))
# ressss = dist + res2
# print(f"ressss: {ressss:.2f}")
