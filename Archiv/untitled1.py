import gurobipy as gp
from gurobipy import GRB

def calculate_npv(cashflows, discount_rate):
    npv = 0
    for i, cashflow in enumerate(cashflows):
        npv += cashflow / (1 + discount_rate) ** i
    return npv

def maximize_npv(cashflows, discount_rate):
    model = gp.Model("NPV Maximization")
    
    # Decision variables
    demand_steel_plant = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name="demand_steel_plant")
    demand_chemical_plant = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name="demand_chemical_plant")
    demand_chemical_airport = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name="demand_chemical_airport")
    
    # Objective function
    npv = calculate_npv(cashflows, discount_rate)
    objective = npv
    model.setObjective(objective, GRB.MAXIMIZE)
    
    # Constraints
    investment_photovoltaic = model.addConstr(demand_steel_plant + demand_chemical_plant + demand_chemical_airport <= 1000, "investment_photovoltaic")
    investment_wind = model.addConstr(demand_steel_plant + demand_chemical_plant + demand_chemical_airport <= 800, "investment_wind")
    
    demand_chemical_plant_constraint = model.addConstr(demand_chemical_plant <= 500, "demand_chemical_plant_constraint")
    demand_chemical_plant_constraint = model.addConstr(demand_chemical_plant >= 0, "demand_chemical_plant_constraint")
    
    demand_chemical_airport_constraint = model.addConstr(demand_chemical_airport <= 500, "demand_chemical_airport_constraint")
    demand_chemical_airport_constraint = model.addConstr(demand_chemical_airport >= 0, "demand_chemical_airport_constraint")
    
    # Solve the optimization problem
    model.optimize()
    
    if model.status == GRB.OPTIMAL:
        # Retrieve the optimal solution
        demand_steel_plant_value = demand_steel_plant.x
        demand_chemical_plant_value = demand_chemical_plant.x
        demand_chemical_airport_value = demand_chemical_airport.x
        
        return demand_steel_plant_value, demand_chemical_plant_value, demand_chemical_airport_value
    else:
        return None, None, None

# Assumptions
discount_rate = 0.1  # Discount rate (10%)

# Cashflows
cashflows = [-1000, 500, 400, 300, 250]  # Cashflows for each period

# Calculate the optimal demand to maximize NPV
demand_steel_plant_opt, demand_chemical_plant_opt, demand_chemical_airport_opt = maximize_npv(cashflows, discount_rate)

if demand_steel_plant_opt is not None and demand_chemical_plant_opt is not None and demand_chemical_airport_opt is not None:
    print("Optimal Demand for Steel Plant:", demand_steel_plant_opt)
    print("Optimal Demand for Chemical Plant:", demand_chemical_plant_opt)
    print("Optimal Demand for Chemical Airport:", demand_chemical_airport_opt)
else:
    print("Failed")
