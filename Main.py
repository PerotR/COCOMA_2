import random
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon, Rectangle, Circle
import Partie1 as p1

def main():
    # Paramètres de la simulation
    n = 10  # Taille de l'environnement (n x n)
    num_taxis = 3  # Nombre de taxis
    task_frequency = 1  # Fréquence d'arrivée des tâches (toutes les 5 étapes)
    num_steps = 2 # Nombre de pas de temps

    # Exécution de la simulation
    p1.run_simulation(n, num_taxis, task_frequency, num_steps)

if __name__ == "__main__":
    main()