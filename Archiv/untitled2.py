from gurobipy import * 

factories, reduced_pollutants_by_factory, limit = multidict({
    'factORy_1': [5, 30],
    'factORy_2': [2, 30],
    'factORy_3': [1, 30],
})

wastes, reduced_pollutants_by_type = multidict({
    "Giftmuell": [6],
    "giftiges Wasser": [7],
    "Giftgas": [7],
})

dangerous_wastes = ["Giftgas"]

produced_waste = {(f, w): 0 for f in factories for w in wastes}
produced_waste[('factORy_1', 'Giftmuell')] = 8
produced_waste[('factORy_1', 'giftiges Wasser')] = 6
produced_waste[('factORy_1', 'Giftgas')] = 4
produced_waste[('factORy_2', 'Giftmuell')] = 10
produced_waste[('factORy_2', 'giftiges Wasser')] = 4
produced_waste[('factORy_2', 'Giftgas')] = 14
produced_waste[('factORy_3', 'Giftmuell')] = 2
produced_waste[('factORy_3', 'giftiges Wasser')] = 16
produced_waste[('factORy_3', 'Giftgas')] = 12

costs = {(f, w): 0 for f in factories for w in wastes}
costs[('factORy_1', 'Giftmuell')] = 3
costs[('factORy_1', 'giftiges Wasser')] = 5
costs[('factORy_1', 'Giftgas')] = 15
costs[('factORy_2', 'Giftmuell')] = 3
costs[('factORy_2', 'giftiges Wasser')] = 4
costs[('factORy_2', 'Giftgas')] = 11
costs[('factORy_3', 'Giftmuell')] = 3
costs[('factORy_3', 'giftiges Wasser')] = 13
costs[('factORy_3', 'Giftgas')] = 10

pollutants = {(f, w): 0 for f in factories for w in wastes}
pollutants[('factORy_1', 'Giftmuell')] = 0.3
pollutants[('factORy_1', 'giftiges Wasser')] = 0.3
pollutants[('factORy_1', 'Giftgas')] = 0.3
pollutants[('factORy_2', 'Giftmuell')] = 0.3
pollutants[('factORy_2', 'giftiges Wasser')] = 0.3
pollutants[('factORy_2', 'Giftgas')] = 0.3
pollutants[('factORy_3', 'Giftmuell')] = 0.3
pollutants[('factORy_3', 'giftiges Wasser')] = 0.3
pollutants[('factORy_3', 'Giftgas')] = 0.3

min_dangerous_waste = 0.3

    # create model
model = Model("orb")

model.modelSense = GRB.MINIMIZE

# create vars
x = {}
for f in factories:
    for w in wastes:
        x[f, w] = model.addVar(name="x_" + f + "_" + w, obj=costs[f,w],ub=produced_waste[f,w])

# update vars
model.update()


# Zweite Nebenbedingung: Pro Abfall w sollen mindestens reduced_pollutants_by_type[w] und 
#                        pro Factory f sollen mindestens reduced_pollutants_by_factory viele Schadstoffe reduziert werden
# Bedeutung: 
# Ungleichung:
for w in wastes:
    model.addConstr(quicksum(x[f, w] * pollutants[f,w] for f in factories) >= reduced_pollutants_by_type[w] )

for f in factories:
    model.addConstr(quicksum(x[f, w] * pollutants[f,w] for w in wastes) >= reduced_pollutants_by_factory[f] )

# Dritte Nebenbedingung: Von allen aufbereiteten Abfaellen sollen mindestens min_dangerous_waste viel Prozent aus den besonders gefaehrlichen Abfaellen bestehen
# Bedeutung: ...
# Ungleichung: 
model.addConstr( quicksum(x[f,y] * pollutants[f,y] for f in factories for y in dangerous_wastes) >= min_dangerous_waste * quicksum(x[f,w] * pollutants[f,w] for f in factories for w in wastes))
    
# Vierte Nebenbedingung: Jede Fabrik hat ein Limit, was sie an Tonnen pro Monat aufbereiten kann
# Bedeutung: ...
# Ungleichung: 
for f in factories:      
    model.addConstr(quicksum(x[f,w] for w in wastes) <= limit[f])

# Fuenfte Nebenbedingung: Es sollte  nur so viel aufbereitet werden, wie auch Abfall vorhanden ist
# Bedeutung: ...
# Ungleichung: 
for f in factories:
    for w in wastes:
        model.addConstr(x[f,w]<=produced_waste[f,w])

# optimize
model.optimize()

# Ausgabe der Loesung.
if model.status == GRB.OPTIMAL:
    print('\nOptimaler Zielfunktionswert: %g\n' % model.ObjVal)
    for f in factories:
        for w in wastes:
            print("Fabrik " + f + " bereitet Abfall " + w + " mit " + str(x[f, w].x) + " Tonnen auf")
else:
    print('Keine Optimalloesung gefunden. Status: %i' % (model.status))

