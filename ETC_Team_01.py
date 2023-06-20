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
time_horizon = range(1, 31)  # Time periods from 1 to 30

# Define maximum demand per customer in GWh
max_demand_customers = {
    'Customer_1_Steel_Plant': 1000,
    'Customer_2_Chemical_Plant': 500,
    'Customer_3_Airport': 500,
}

# Define selling price in €/GWh
price_per_unit = {
    'hydrogen': 210000,
    'ammonia': 287004,
    'jetfuel': 315000, 
}

# Define typical capacity per unit area in GW/km^2
capacity_per_unit_area = {
    'photovoltaic': 20,
    'wind': 30,
}

# CO2 point source availabilty in tCO2 /a
m = - 150000 / (2050-2023)
b = 150000 

point_source_availability = {}
for t in time_horizon:
    point_source_availability[t-1] = m*(t-1) + b
    if t > 27:
        point_source_availability[t-1] = 0

# CO2 demand for 1GWh of jetfuel in tons/GWh ! Check again !
CO2_demand_per_unit_jetfuel = 260 

# Define CAPEX & OPEX in €/GW
capex = {
    'photovoltaic': 650 * 10 **6,
    'wind': 1500 * 10 ** 6,
    'PEM_electrolyzer': 700 * 10 **6,
    'alkaline_electrolyzer': 650 * 10 **6,
    'FT_synthesis': 1200 * 10 **6,
    'ammonia_synthesis': 1400 * 10 **6,
    'ammonia_splitting': 1000 * 10 **6, #needs to be investigated
}

opex = {
    'photovoltaic': 0.03 * capex['photovoltaic'],
    'wind': 0.04 * capex['wind'],
    'PEM_electrolyzer': 0.04 * capex['PEM_electrolyzer'],
    'alkaline_electrolyzer': 0.04 * capex['alkaline_electrolyzer'],
    'FT_synthesis': 0.05 * capex['FT_synthesis'],
    'ammonia_synthesis': 0.05 * capex['ammonia_synthesis'],
    'ammonia_splitting': 0.05 * capex['ammonia_splitting'],
}

deprecation_time = {
    'photovoltaic': 30,
    'wind': 30,
    'PEM_electrolyzer': 10,
    'alkaline_electrolyzer': 10,
    'FT_synthesis': 10,
    'ammonia_synthesis': 20,
    'ammonia_splitting': 20,
}

# Define operating hours of photovoltaic and wind in h/year
operating_hours_photovoltaic = 2300
operating_hours_wind = 5000
operating_hours_PEM_electrolyzer = operating_hours_alkaline_electrolyzer = operating_hours_FT_synthesis = operating_hours_ammonia_synthesis = operating_hours_ammonia_splitting = 7500

# Define efficiency of Electrolyzers
efficiency_PEM_electrolyzer = 0.7
efficiency_alkaline_electrolyzer = 0.65
efficiency_FT_synthesis = 0.71*0.75
efficiency_ammonia_synthesis = 0.8
efficiency_ammonia_splitting = 0.8 # needs to be researched

# Transport costs in €/GWh
transport_costs = {
    'hydrogen': 20 * 10**3, 
    'ammonia': 10 * 10**3,
    'jetfuel': 5 * 10**3,
}

# Discount rate
i = 0.1

# Define decision variables
x = {}
y = {}
for c in customers:
    x[c] = model.addVar(name="x_" + c, vtype=gp.GRB.BINARY) # is 1 if customer will be served and 0 if customer won't be served
    for t in time_horizon:
        y[c, t] = model.addVar(name="y_" + c + "_" + str(t), lb=0, vtype=gp.GRB.CONTINUOUS) # describes how much GWh are supplied to customer c in period t

# Decision variables for the constraint that at least 50% of either the chemical plant’s or airport’s demand must be met. At least one of these variables has to be >0.
x1 = model.addVar(name="x1", vtype=gp.GRB.BINARY)
x2 = model.addVar(name="x2", vtype=gp.GRB.BINARY)

# Decision variables for the CO2 supply, binary
x_point_source = model.addVar(name="x_point_source", vtype=gp.GRB.BINARY)
x_dac = model.addVar(name="x_dac", vtype=gp.GRB.BINARY)

# Decision variable about the splitting of hydrogen from ammonia
x_ammonia_splitting = model.addVar(name="x_ammonia_splitting", vtype=gp.GRB.BINARY)

# Decision variables for the CO2 supply, continous in tons of CO2
point_source_amount = {}
dac_amount = {}
for t in time_horizon:
    point_source_amount[t] = model.addVar(name="point_source_amount", vtype = gp.GRB.CONTINUOUS)
    dac_amount[t] = model.addVar(name="dac_amount", vtype = gp.GRB.CONTINUOUS)

# Decision variables for transport: variable = 0 if product is not transported, and variable = 1 if product is transported
x_transport = {}
x_transport['hydrogen'] = model.addVar(name="x_transport_hydrogen", vtype=gp.GRB.BINARY)
x_transport['ammonia'] = model.addVar(name="x_transport_ammonia", vtype=gp.GRB.BINARY)
x_transport['jetfuel'] = model.addVar(name="x_transport_jetfuel", vtype=gp.GRB.BINARY)

# Decision variable for the initial investment
init_investment_var = model.addVar(name="init_investment", vtype=gp.GRB.CONTINUOUS)

# Decision variables for the electrolyzers, FT synthesis, ammonia synthesis & ammonia splitting
capacity_photovoltaic = model.addVar(name="capacity_photovoltaic", vtype=gp.GRB.CONTINUOUS)
capacity_wind = model.addVar(name="capacity_wind", vtype=gp.GRB.CONTINUOUS)
capacity_PEM_electrolyzer = model.addVar(name="capacity_PEM_electrolyzer", vtype=gp.GRB.CONTINUOUS)
capacity_alkaline_electrolyzer = model.addVar(name="capacity_alkaline_electrolyzer", vtype=gp.GRB.CONTINUOUS)
capacity_FT_synthesis = model.addVar(name="capacity_FT_synthesis", vtype=gp.GRB.CONTINUOUS)
capacity_ammonia_synthesis = model.addVar(name="capacity_ammonia_synthesis", vtype=gp.GRB.CONTINUOUS)
capacity_ammonia_splitting = model.addVar(name="capacity_ammonia_splitting", vtype=gp.GRB.CONTINUOUS)

# Update Model
model.update()

# Define transported amounts in GWh
transported_ammonia = [y['Customer_2_Chemical_Plant', t] * x_transport['ammonia'] + y['Customer_1_Steel_Plant', t] * x_ammonia_splitting / efficiency_ammonia_splitting for t in time_horizon ] 
transported_jetfuel = [y['Customer_3_Airport', t] * x_transport['jetfuel'] for t in time_horizon]
transported_hydrogen = [y['Customer_1_Steel_Plant', t] * x_transport['hydrogen'] + y['Customer_2_Chemical_Plant', t] * (1- x_transport['ammonia']) / efficiency_ammonia_synthesis + y['Customer_3_Airport', t] * (1- x_transport['jetfuel']) / efficiency_FT_synthesis  for t in time_horizon]

# Define cash inflow per period for each customer
cash_inflow_customer_1 = [price_per_unit['hydrogen'] * y['Customer_1_Steel_Plant', t] for t in time_horizon]
cash_inflow_customer_2 = [price_per_unit['ammonia'] * y['Customer_2_Chemical_Plant', t] for t in time_horizon]
cash_inflow_customer_3 = [price_per_unit['jetfuel'] * y['Customer_3_Airport', t] / 0.71 for t in time_horizon] # in the task it says, that only 71% of the product is jet fuel, but the other 29% can be sold for the same price

# Define costs for CO2 supply in € ( €/tons * tons * decision variable)
point_source_costs = [70 * point_source_amount[t] * x_point_source for t in time_horizon]
dac_costs = [300 * dac_amount[t] * x_dac for t in time_horizon]

# Define cash outflow per period
cash_outflow_photovoltaic = opex['photovoltaic'] * capacity_photovoltaic
cash_outflow_wind = opex['wind'] * capacity_wind
cash_outflow_PEM_electrolyzer = opex['PEM_electrolyzer'] * capacity_PEM_electrolyzer
cash_outflow_alkaline_electrolyzer = opex['alkaline_electrolyzer'] * capacity_alkaline_electrolyzer
cash_outflow_FT_synthesis = [opex['FT_synthesis'] * capacity_FT_synthesis + point_source_costs[t-1] + dac_costs[t-1] for t in time_horizon]
cash_outflow_ammonia_synthesis = opex['ammonia_synthesis'] * capacity_ammonia_synthesis
cash_outflow_ammonia_splitting = opex['ammonia_splitting'] * capacity_ammonia_splitting
cash_outflow_transport = [transported_hydrogen[t-1] * transport_costs["hydrogen"] + transported_ammonia[t-1] * transport_costs["ammonia"] + transported_jetfuel[t-1] * transport_costs["jetfuel"] for t in time_horizon]
cash_outflow_deprecation = {}

for t in time_horizon:
    cash_outflow_deprecation[t - 1] = 0
    for key, value in deprecation_time.items():
        if t >= value and t % value == 0:
            cash_outflow_deprecation[t - 1]+=(capex[key])


# Initial investment
init_investment_expr =   (capex['photovoltaic'] * capacity_photovoltaic 
                    + capex['wind'] * capacity_wind
                    + capex['PEM_electrolyzer'] * capacity_PEM_electrolyzer
                    + capex['alkaline_electrolyzer'] * capacity_alkaline_electrolyzer
                    + capex['FT_synthesis'] * capacity_FT_synthesis
                    + capex['ammonia_synthesis'] * capacity_ammonia_synthesis
                    + capex['ammonia_splitting'] * capacity_ammonia_splitting
)

# Set the objective function to maximize dynamically calculated NPV
objective = - init_investment_var + gp.quicksum(
    ( cash_inflow_customer_1[t - 1] 
    + cash_inflow_customer_2[t - 1] 
    + cash_inflow_customer_3[t - 1] 
    - cash_outflow_photovoltaic
    - cash_outflow_wind
    - cash_outflow_PEM_electrolyzer
    - cash_outflow_alkaline_electrolyzer
    - cash_outflow_FT_synthesis[t - 1]
    - cash_outflow_ammonia_synthesis
    - cash_outflow_ammonia_splitting
    - cash_outflow_transport[t - 1]
    - cash_outflow_deprecation[t - 1]
    ) 
    / ((1 + i) ** t)
    for t in time_horizon
)

model.setObjective(objective, sense=gp.GRB.MAXIMIZE)

model.addConstr(init_investment_var == init_investment_expr, name="init_investment_eq")

# Add constraint for customer's supply
for c in customers:
    for t in time_horizon:
        model.addConstr(y[c, t] <= x[c] * max_demand_customers[c], name=f"max_supply_constr_{c}_{t}")
        model.addConstr(y[c, t] >= x[c])

# Add constraint for area limitation
model.addConstr(capacity_photovoltaic / capacity_per_unit_area['photovoltaic']
                + capacity_wind / capacity_per_unit_area['wind'] <= 9)

# Linking constraint between produced energy and required energy
model.addConstr(capacity_photovoltaic * operating_hours_photovoltaic 
                    + capacity_wind * operating_hours_wind
                    >= capacity_PEM_electrolyzer * operating_hours_PEM_electrolyzer #* 0.9 why did I add this?
                    + capacity_alkaline_electrolyzer * operating_hours_alkaline_electrolyzer)# * 0.8) why?

# At least 80% of the steel plant’s maximum demand must be met
for t in time_horizon:
    model.addConstr(y['Customer_1_Steel_Plant', t] >= 0.8 * max_demand_customers['Customer_1_Steel_Plant'])

# At least 50% of either the chemical plant’s or airport’s demand must be met
for t in time_horizon:
    model.addConstr(y['Customer_2_Chemical_Plant', t] >= 0.5 * max_demand_customers['Customer_2_Chemical_Plant'] * x1)
    model.addConstr(y['Customer_3_Airport', t] >= 0.5 * max_demand_customers['Customer_3_Airport'] * x2)
    model.addConstr(x1 + x2 >= 1)

# The capacity of the electrolyzers must meet demands in GWh
for t in time_horizon:
    model.addConstr(capacity_PEM_electrolyzer * operating_hours_PEM_electrolyzer * efficiency_PEM_electrolyzer 
                    + capacity_alkaline_electrolyzer * operating_hours_alkaline_electrolyzer * efficiency_alkaline_electrolyzer 
                    >= y['Customer_1_Steel_Plant', t]
                    + y['Customer_2_Chemical_Plant', t] / efficiency_ammonia_synthesis
                    + y['Customer_3_Airport', t] / efficiency_FT_synthesis
                    )
    x_ammonia_splitting
# The capacity of the FT synthesis must meet demand of chemical plant
for t in time_horizon:
    model.addConstr(capacity_ammonia_synthesis * operating_hours_ammonia_synthesis >= y['Customer_2_Chemical_Plant', t])

# The CO2 demand of the FT synthesis must not exceed the DAC availability
for t in time_horizon:
    model.addConstr(transported_jetfuel[t-1] * CO2_demand_per_unit_jetfuel  <= point_source_availability[t-1] * x_point_source + gp.GRB.INFINITY * x_dac)

# Couple the CO2 captured from the air to the transported jet fuel
for t in time_horizon:
    model.addConstr(point_source_amount[t] * x_point_source + dac_amount[t] * x_dac == transported_jetfuel[t-1] * CO2_demand_per_unit_jetfuel)

# When dac_amount = [0, 0, 0, ..] x_dac should be zero, too
for t in time_horizon:
    model.addConstr(x_dac <= dac_amount[t])
    model.addConstr(x_point_source <= point_source_amount[t])

# The capacity of the ammonia synthesis must meet demand of airport
for t in time_horizon:
    model.addConstr(capacity_FT_synthesis * operating_hours_FT_synthesis >= y['Customer_3_Airport', t])

# If ammonia is transported, then the cusomer will be supplied. Same for jet fuel
model.addConstr(x_transport['ammonia'] <= x['Customer_2_Chemical_Plant'])
model.addConstr(x_transport['jetfuel'] <= x['Customer_3_Airport'])

# If no hydrogen is transported, the customer is not being served. But also if hydrogen is transported, that doesn't mean the steel plant is supplied
# model.addConstr(x_transport['hydrogen'] >= x['Customer_1_Steel_Plant'])
for t in time_horizon:
    model.addConstr(transported_hydrogen[t-1] <= x_transport['hydrogen'] * gp.GRB.INFINITY)

# Hydrogen can only either be transported or split in Rotterdam. If the steel plant is supplied, hydrogen needs to be either split or transported
model.addConstr(x_ammonia_splitting + x_transport['hydrogen'] <= 1)
model.addConstr(x_ammonia_splitting + x_transport['hydrogen'] >= x['Customer_1_Steel_Plant'])

# If ammonia is produced in morocco, then no further hydrogen needs to be transported to meet demand of customer 2. If there is no ammonia transported, additional 
# hydrogen has to be transported. In that case, the demand of customers 1 and 3 have to be substracted from the hydrogen amount, to 
# for t in time_horizon:
#     model.addConstr(transported_ammonia[t-1] + transported_hydrogen[t-1] *(1-x_transport['ammonia']) - y['Customer_1_Steel_Plant'] * x_transport['hydrogen'] - y['Customer_2_Chemical_Plant'] * x_transport['jetfuel'] >= y['Customer_2_Chemical_Plant', t])

# Initial investment must be lower than 2bn
model.addConstr(init_investment_var <= 2*10**9)

# Solve the model
model.optimize()

print('cash_outflow_photovoltaic:', cash_outflow_photovoltaic.getValue())


# Print the final NPV
print(f"The maximized NPV is {model.ObjVal}")

# Print which customers were chosen
for c in customers:
    if x[c].x == 1:  # Checking if the project is selected
        print(f"{c} is selected")
    else:
        print(f"{c} is not selected")

# Print the capacity of photovoltaic and wind
print(f"capacity of photovoltaic used: {round(capacity_photovoltaic.x, 2)} GW, i.e. a yearly energy demand of {round(capacity_photovoltaic.x * operating_hours_photovoltaic, 2)} GWh")
print(f"capacity of wind power used: {capacity_wind.x} GW, i.e. a yearly energy demand of {round(capacity_wind.x * operating_hours_wind, 2)} GWh")
print(f"capacity of PEM electrolyzer: {round(capacity_PEM_electrolyzer.x, 2)} GW, i.e. a yearly energy demand of {round(capacity_PEM_electrolyzer.x, 2) * operating_hours_PEM_electrolyzer} GWh")
print(f"capacity of alkaline electrolyzer: {round(capacity_alkaline_electrolyzer.x, 2)} GW, i.e. a yearly energy demand of {round(capacity_alkaline_electrolyzer.x, 2) * operating_hours_alkaline_electrolyzer} GWh")

# Print the supply for each customer
for c in customers:
    supply_values = [y[c, t].x for t in time_horizon]
    print(f"Supply to {c}: {supply_values} GWh")

# Print all variables related to transport
print("x_ammonia_splitting: ", x_ammonia_splitting.x)
print("x_transport_ammonia: ", x_transport['ammonia'].x)
print("x_transport_hydrogen: ", x_transport['hydrogen'].x)
transported_ammonia_values = [round(expr.getValue(),2) for expr in transported_ammonia]
transported_jetfuel_values = [round(expr.getValue(),2) for expr in transported_jetfuel]
transported_hydrogen_values = [round(expr.getValue(),2) for expr in transported_hydrogen]

print("transported_ammonia:", transported_ammonia_values)
print("transported_jetfuel:", transported_jetfuel_values)
print("transported_hydrogen:", transported_hydrogen_values)

# Print all variables related to the CO2 source
print("x_dac:", x_dac.x)
print("x_point_source:", x_point_source.x) 
print("point_source_availability:", [point_source_availability[t-1] for t in time_horizon]) 
print("point_source_amount:", [point_source_amount[t].x for t in time_horizon])
print("dac_amount:", [dac_amount[t].x for t in time_horizon])

print("init_investment:", init_investment_var.x)
LCOH = {
    'PEM_electrolyzer': (capex['PEM_electrolyzer'] * capacity_PEM_electrolyzer.x + gp.quicksum((cash_outflow_PEM_electrolyzer.getValue()) / ((1 + i) ** t) for t in time_horizon))
    / (capacity_PEM_electrolyzer.x * operating_hours_PEM_electrolyzer * efficiency_PEM_electrolyzer * (max(time_horizon)-1)),
    # 'alkaline_electrolyzer': (capex['alkaline_electrolyzer'] * capacity_alkaline_electrolyzer.x + gp.quicksum((cash_outflow_alkaline_electrolyzer) / ((1 + i) ** t)    for t in time_horizon))
    # /(capacity_alkaline_electrolyzer.x*operating_hours_alkaline_electrolyzer*efficiency_alkaline_electrolyzer),
}
print("LCOH PEM", LCOH['PEM_electrolyzer'])
# print("LCOH alkaline", LCOH['alkaline_electrolyzer'])

# print("transported_jetfuel[t-1] * CO2_demand_per_unit_jetfuel", [transported_jetfuel[t-1] * CO2_demand_per_unit_jetfuel for t in time_horizon])
# print("dac_costs:", [300 * dac_amount[t].x * x_dac for t in time_horizon])
# print("cash_inflow_customer_1: ", [model.getVarByName(f'y_Customer_1_Steel_Plant_{i}').x * price_per_unit['hydrogen'] for i in range(1, 11)])
# print("transported_ammonia: ", transported_ammonia)
# print("transported_hydrogen", transported_hydrogen)

# Print all vars
# all_vars = model.getVars()
# values = model.getAttr("X", all_vars)
# names = model.getAttr("VarName", all_vars)

# # for name, val in zip(names, values):
# #     print(f"{name} = {val}")