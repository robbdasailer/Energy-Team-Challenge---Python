import gurobipy as gp

# Overall units:
    # energy: GWh
    # capacity: GW
    # area: km^2
    # money: €

# Create a Gurobi model
model = gp.Model()

# Define projects
customers = ['Customer_1_Steel_Plant', 'Customer_2_Chemical_Plant', 'Customer_3_Airport']

# Define time horizon
time_horizon = range(1, 11)  # Time periods from 1 to 10
for i in time_horizon:
    print(i)

# Define maximum demand per customer in GWh
max_demand_customers = {
    'Customer_1_Steel_Plant': 1000,
    'Customer_2_Chemical_Plant': 500,
    'Customer_3_Airport': 500,
}

# Define selling price in €/GWh
price_per_unit_hydrogen = 210000
price_per_unit_ammonia = 287004
price_per_unit_jetfuel = 315000

# Define typical capacity per unit area in GW/km^2
capacity_per_unit_area_photovoltaic = 20 # = 2 MW/ha
capacity_per_unit_area_wind = 30 # = 3 MW/ha

# Define CAPEX & OPEX in €/GW
capex_photovoltaic = 650 * 10 **6 # = 650 €/kW
capex_wind = 1500 * 10 **6 # = 1500 €/kW
opex_photovoltaic = 0.03 * capex_photovoltaic 
opex_wind = 0.04 * capex_wind 

# Define operating hours of photovoltaic and wind in h/year
operating_hours_photovoltaic = 3000
operating_hours_wind = 4500

# Discount rate
i = 0.1

# Define decision variables
x = {}
y = {}
for c in customers:
    x[c] = model.addVar(name="x_" + c, vtype=gp.GRB.BINARY) # is 1 if customer will be served and 0 if customer won't be served
    for t in time_horizon:
        y[c, t] = model.addVar(name="y_" + c + "_" + str(t), lb=0, vtype=gp.GRB.CONTINUOUS) # describes how much GWh are supplied to customer c in period t

capacity_photovoltaic = model.addVar(name="capacity_photovoltaic", vtype=gp.GRB.CONTINUOUS)
capacity_wind = model.addVar(name="capacity_wind", vtype=gp.GRB.CONTINUOUS)

# Decision variables for the constraint that at least 50% of either the chemical plant’s or airport’s demand must be met
y1 = model.addVar(name="y1", vtype=gp.GRB.BINARY)
y2 = model.addVar(name="y2", vtype=gp.GRB.BINARY)

# Update Model
model.update()

# Define cash inflow per period for each customer
cash_inflow_customer_1 = [price_per_unit_hydrogen * y['Customer_1_Steel_Plant', t] for t in time_horizon]
cash_inflow_customer_2 = [price_per_unit_ammonia * y['Customer_2_Chemical_Plant', t] for t in time_horizon]
cash_inflow_customer_3 = [price_per_unit_jetfuel * y['Customer_3_Airport', t] for t in time_horizon]

# Define cash outflow per period
cash_outflow_photovoltaic = opex_photovoltaic * capacity_photovoltaic
cash_outflow_wind = opex_wind * capacity_wind

# Initial investment
init_investment = capex_photovoltaic * capacity_photovoltaic + capex_wind * capacity_wind

# Set the objective function to maximize dynamically calculated NPV
objective = - init_investment + gp.quicksum(
    ( cash_inflow_customer_1[t - 1] 
    + cash_inflow_customer_2[t - 1] 
    + cash_inflow_customer_3[t - 1] 
    - cash_outflow_photovoltaic
    - cash_outflow_wind) 
    / ((1 + i) ** t)
    for t in time_horizon
)

model.setObjective(objective, sense=gp.GRB.MAXIMIZE)

# Add constraint for customer's supply
for c in customers:
    for t in time_horizon:
        model.addConstr(y[c, t] <= x[c] * max_demand_customers[c], name=f"max_supply_constr_{c}_{t}")

# Add constraint for area limitation
model.addConstr(capacity_photovoltaic * capacity_per_unit_area_photovoltaic 
                + capacity_wind * capacity_per_unit_area_wind <= 9)

# Linking constraint
for t in time_horizon:
    model.addConstr(capacity_photovoltaic * operating_hours_photovoltaic 
                    + capacity_wind * operating_hours_wind
                    >= gp.quicksum(y[c, t] for c in customers))

# At least 80% of the steel plant’s maximum demand must be met
for t in time_horizon:
    model.addConstr(y['Customer_1_Steel_Plant', t] >= 0.8 * max_demand_customers['Customer_1_Steel_Plant'])

# At least 50% of either the chemical plant’s or airport’s demand must be met
for t in time_horizon:
    model.addConstr(y['Customer_2_Chemical_Plant', t] >= 0.5 * max_demand_customers['Customer_2_Chemical_Plant'] * y1)
    model.addConstr(y['Customer_3_Airport', t] >= 0.5 * max_demand_customers['Customer_3_Airport'] * y2)
    model.addConstr(y1 + y2 >= 1)


# Solve the model
model.optimize()

# Print the final NPV
print(f"The maximized NPV is {model.ObjVal}")

# Print which customers were chosen
for c in customers:
    if x[c].x == 1:  # Checking if the project is selected
        print(f"{c} is selected")
    else:
        print(f"{c} is not selected")

# Print the capacity of photovoltaic and wind
print(f"capacity of photovoltaic used: {capacity_photovoltaic.x} GW, i.e. a yearly production of {capacity_photovoltaic.x * operating_hours_photovoltaic} GWh")
print(f"capacity of wind power used: {capacity_wind.x} GW, i.e. a yearly production of {capacity_wind.x * operating_hours_wind} GWh")

# Print the supply for each customer
for c in customers:
    supply_values = [y[c, t].x for t in time_horizon]
    print(f"Supply to {c}: {supply_values} GWh")