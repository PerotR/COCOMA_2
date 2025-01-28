import Partie1 as P1

def PSI (Taxis, Tasks):

    bids={}
    for task in Tasks:
        tmp=[]
        for taxi in Taxis:
            cout=[]
            cout.append(P1.calculate_distance(taxi['position'],task['start']))
            
            cout_min = min(cout)
            tmp+=[(taxi['id'],cout_min)]
        sorted_tmp = sorted(tmp, key=lambda tup: tup[1])
        bids[task['id']]=sorted_tmp

    return bids



taxis = [{'id': 1, 'position': (0,0), 'tasks' : []},
            {'id': 2, 'position': (1,1), 'tasks' : []},
            {'id': 3, 'position': (2,2), 'tasks' : []}]

tasks = [{'id': 1, 'start': (1,1), 'end': (2,2), 'cost': 1},
            {'id': 2, 'start': (0,0), 'end': (2,2), 'cost': 2},
            {'id': 3, 'start': (0,0), 'end': (1,1), 'cost': 3}]

bids=PSI(taxis,tasks)
print(bids)

