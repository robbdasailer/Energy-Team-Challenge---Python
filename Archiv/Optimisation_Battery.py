import gurobipy as gp

# Overall units:
# energy: GWh
# capacity: GW
# area: km^2
# money: €

# Create a Gurobi model
model = gp.Model()

cap_PV = 1
t_vl=6.3
t_x=12 #noch korrekten Wert aus Sonnenprofil einfügen!!

# Define 
capex = {
    'PV': 650 * 10 ** 6,     # €/GW
    'EL': 700 * 10 ** 6,     # €/GW
    'Bat': 10 * 10 ** 6,   # €/GWh
}

opex = {
    'PV': 0.03 * capex['PV'],     # korrekte opex einfügen !!
    'EL': 0.04 * capex['EL'],     # korrekte opex einfügen !!
    'Bat': 0.01 * capex['Bat']   # €/GWh
}

i=0.1 #Zins
a=30 #Jahre
RBF=(((1+i)**a)-1)/(((1+i)**a)*i)

cap_bat = model.addVar(name="cap_bat", vtype=gp.GRB.CONTINUOUS) 
cap_EL = model.addVar(name="cap_EL", vtype=gp.GRB.CONTINUOUS)
x_bat = model.addVar(name="x_bat", vtype=gp.GRB.BINARY)


# Update Model
model.update()

#costs = cap_PV * capex['PV'] + cap_bat * capex['Bat'] + cap_EL * capex['EL']
NPV = (cap_PV * capex['PV'] + cap_bat * capex['Bat'] + cap_EL * capex['EL'])+RBF*(cap_PV * opex['PV'] + cap_bat * opex['Bat'] + cap_EL * opex['EL'])

model.setObjective(NPV, sense=gp.GRB.MINIMIZE)

#neu Fabian
model.addConstr(cap_EL == cap_PV * (t_vl/24)*x_bat+cap_PV*(1-x_bat), name="constr1")

model.addConstr(cap_bat >= (cap_PV * 6.3 - cap_EL * t_x) * x_bat, name="constr2")



# Solve the model
model.optimize()

# Print the solution
if model.status == gp.GRB.OPTIMAL:
    print("Optimal solution found.")
    print("x_bat =", x_bat.x)
    print("cap_bat =", cap_bat.x)
    print("cap_EL =", cap_EL.x)
    print("Total cost =", model.objVal)
else:
    print("No solution found.")
