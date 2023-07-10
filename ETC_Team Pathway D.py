import gurobipy as gp
import csv

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
    'photovoltaic': 0.2,
    'wind': 0.3,
}

# Define battery capacity in GWh
# capacity_battery = 3.5 #3.74

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
    'battery': 500 * 10**6 #€/GWh
}

opex = {
    'photovoltaic': 0.03 * capex['photovoltaic'],
    'wind': 0.04 * capex['wind'],
    'PEM_electrolyzer': 0.04 * capex['PEM_electrolyzer'],
    'alkaline_electrolyzer': 0.04 * capex['alkaline_electrolyzer'],
    'FT_synthesis': 0.05 * capex['FT_synthesis'],
    'ammonia_synthesis': 0.05 * capex['ammonia_synthesis'],
    'ammonia_splitting': 0.05 * capex['ammonia_splitting'],
    'battery': 0 * capex['battery']
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
operating_hours_PEM_electrolyzer = operating_hours_alkaline_electrolyzer = 24*365 * 0.9
operating_hours_FT_synthesis = operating_hours_ammonia_synthesis = operating_hours_ammonia_splitting = 24*365 * 0.9

# Define efficiency of Electrolyzers
efficiency_PEM_electrolyzer = 0.7
efficiency_alkaline_electrolyzer = 0.65
efficiency_FT_synthesis = 0.75
efficiency_ammonia_synthesis = 0.8
efficiency_ammonia_splitting = 0.8 # needs to be researched
# efficiency_battery = 0.95

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

# Decision variables for the battery capacity constraint
x1 = model.addVar(name="x1", vtype=gp.GRB.BINARY)
x2 = model.addVar(name="x2", vtype=gp.GRB.BINARY)

# Decision variables for the CO2 supply, binary
x_point_source = {}
x_dac = {}
for t in time_horizon:
    x_point_source[t-1] = model.addVar(name="x_point_source", vtype=gp.GRB.BINARY)
    x_dac[t-1] = model.addVar(name="x_dac", vtype=gp.GRB.BINARY)

# Decision variable about the splitting of hydrogen from ammonia
x_ammonia_splitting = model.addVar(name="x_ammonia_splitting", vtype=gp.GRB.BINARY)

# Decision variables for the CO2 supply, continous in tons of CO2
point_source_amount = {}
dac_amount = {}
for t in time_horizon:
    point_source_amount[t-1] = model.addVar(name="point_source_amount", vtype = gp.GRB.CONTINUOUS)
    dac_amount[t-1] = model.addVar(name="dac_amount", vtype = gp.GRB.CONTINUOUS)

# Decision variables for transport: variable = 0 if product is not transported, and variable = 1 if product is transported
x_transport = {}
x_transport['hydrogen'] = 0 #model.addVar(name="x_transport_hydrogen", vtype=gp.GRB.BINARY)
x_transport['ammonia'] = 1 #model.addVar(name="x_transport_ammonia", vtype=gp.GRB.BINARY)
x_transport['jetfuel'] = 1 #model.addVar(name="x_transport_jetfuel", vtype=gp.GRB.BINARY)

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
capacity_battery = model.addVar(name="capacity_battery", vtype=gp.GRB.CONTINUOUS)

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
point_source_costs = [70 * point_source_amount[t-1] * x_point_source[t-1] for t in time_horizon]
dac_costs = [300 * dac_amount[t-1] * x_dac[t-1] for t in time_horizon]

# Define cash outflow per period
cash_outflow_photovoltaic = opex['photovoltaic'] * capacity_photovoltaic
cash_outflow_wind = opex['wind'] * capacity_wind
cash_outflow_PEM_electrolyzer = opex['PEM_electrolyzer'] * capacity_PEM_electrolyzer
cash_outflow_alkaline_electrolyzer = opex['alkaline_electrolyzer'] * capacity_alkaline_electrolyzer
cash_outflow_FT_synthesis = opex['FT_synthesis'] * capacity_FT_synthesis
cash_outflow_ammonia_synthesis = opex['ammonia_synthesis'] * capacity_ammonia_synthesis
cash_outflow_ammonia_splitting = opex['ammonia_splitting'] * capacity_ammonia_splitting
cash_outflow_transport = [transported_hydrogen[t-1] * transport_costs["hydrogen"] + transported_ammonia[t-1] * transport_costs["ammonia"] + transported_jetfuel[t-1] * transport_costs["jetfuel"] for t in time_horizon]
cash_outflow_co2 = [point_source_costs[t-1] + dac_costs[t-1] for t in time_horizon]
cash_outflow_battery = opex['battery'] * capacity_battery 

# Initial investment
init_investment_expr =   (capex['photovoltaic'] * capacity_photovoltaic 
                    + capex['wind'] * capacity_wind
                    + capex['PEM_electrolyzer'] * capacity_PEM_electrolyzer
                    + capex['alkaline_electrolyzer'] * capacity_alkaline_electrolyzer
                    + capex['FT_synthesis'] * capacity_FT_synthesis
                    + capex['ammonia_synthesis'] * capacity_ammonia_synthesis
                    + capex['ammonia_splitting'] * capacity_ammonia_splitting
                    + capex['battery'] * capacity_battery
                    # + capex['battery'] * capacity_photovoltaic * 3.15
)

# Set the objective function to maximize dynamically calculated NPV
objective = - 0.5 * init_investment_var - 0.5 * init_investment_var / (1+i) + gp.quicksum(
    ( cash_inflow_customer_1[t - 1] 
    + cash_inflow_customer_2[t - 1] 
    + cash_inflow_customer_3[t - 1] 
    - cash_outflow_photovoltaic
    - cash_outflow_wind
    - cash_outflow_PEM_electrolyzer
    - cash_outflow_alkaline_electrolyzer
    - cash_outflow_FT_synthesis
    - cash_outflow_ammonia_synthesis
    - cash_outflow_ammonia_splitting
    - cash_outflow_transport[t - 1]
    - cash_outflow_co2[t-1]
    - cash_outflow_battery
    ) 
    / ((1 + i) ** (t+1))
    for t in time_horizon
)

model.setObjective(objective, sense=gp.GRB.MAXIMIZE)

# Define Big M 
M = 10**6

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
    model.addConstr(y['Customer_2_Chemical_Plant', t] >= 0.5 * max_demand_customers['Customer_2_Chemical_Plant'] * x['Customer_2_Chemical_Plant'])
    model.addConstr(y['Customer_3_Airport', t] >= 0.5 * max_demand_customers['Customer_3_Airport'] * x['Customer_3_Airport'])
    model.addConstr(x['Customer_2_Chemical_Plant'] + x['Customer_3_Airport'] >= 1)


# The capacity of the electrolyzers must meet demands in GWh
for t in time_horizon:
    model.addConstr(capacity_PEM_electrolyzer * operating_hours_PEM_electrolyzer
                    + capacity_alkaline_electrolyzer * operating_hours_alkaline_electrolyzer  
                    >= y['Customer_1_Steel_Plant', t]
                    + y['Customer_2_Chemical_Plant', t] / efficiency_ammonia_synthesis
                    + y['Customer_3_Airport', t] /0.71 / efficiency_FT_synthesis
                    )

# The capacity of the ammonia synthesis must meet demand of chemical plant
for t in time_horizon:
    model.addConstr(capacity_ammonia_synthesis * operating_hours_ammonia_synthesis >= y['Customer_2_Chemical_Plant', t] + (y['Customer_1_Steel_Plant', t]  + (y['Customer_3_Airport', t] / (0.7 * 0.75))) * x_ammonia_splitting)

# The CO2 demand of the FT synthesis must not exceed the DAC availability
for t in time_horizon:
    model.addConstr(transported_jetfuel[t-1] * CO2_demand_per_unit_jetfuel  <= point_source_availability[t-1] * x_point_source[t-1] + gp.GRB.INFINITY * x_dac[t-1])

# The ammonia splitting capacity must be
for t in time_horizon:
    model.addConstr(capacity_ammonia_splitting * operating_hours_ammonia_splitting >= (y['Customer_1_Steel_Plant', t]  + (y['Customer_3_Airport', t] / (0.7 * 0.75))) * x_ammonia_splitting)

# model.addConstr(capacity_ammonia_splitting <= M * x_ammonia_splitting)

# Couple the CO2 captured from the air to the transported jet fuel
for t in time_horizon:
    model.addConstr(point_source_amount[t-1] * x_point_source[t-1] + dac_amount[t-1] * x_dac[t-1] == transported_jetfuel[t-1] * CO2_demand_per_unit_jetfuel)

# When dac_amount = [0, 0, 0, ..] x_dac should be zero, too
for t in time_horizon:
    model.addConstr(x_dac[t-1] <= dac_amount[t-1])
    model.addConstr(x_point_source[t-1] <= point_source_amount[t-1])
    model.addConstr(point_source_amount[t-1] <= point_source_availability[t-1])

# The capacity of the ammonia synthesis must meet demand of airport
for t in time_horizon:
    model.addConstr(capacity_FT_synthesis * operating_hours_FT_synthesis >= y['Customer_3_Airport', t] / 0.71)

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

# Battery capacity is linked to wind and photovoltaic
model.addConstr(capacity_battery == 1.2*(capacity_photovoltaic * 6.3 - capacity_PEM_electrolyzer * 12) * x1 
                                    + 1.2*(capacity_wind * 13.7 - capacity_PEM_electrolyzer * 20 ) *x2)

model.addConstr(x1 * M >= capacity_photovoltaic)
model.addConstr(x2 * M >= capacity_wind)
model.addConstr(x1 + x2 <= 1)

# Initial investment must be lower than 2bn
model.addConstr((0.5 + 0.5 / 1+i)* init_investment_var <= 2*10**9)



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
print(f"capacity of photovoltaic used: {round(capacity_photovoltaic.x, 8)} GW, i.e. a yearly energy demand of {round(capacity_photovoltaic.x * operating_hours_photovoltaic, 2)} GWh")
print(f"capacity of wind power used: {round(capacity_wind.x, 8)} GW, i.e. a yearly energy demand of {round(capacity_wind.x * operating_hours_wind, 2)} GWh")
print(f"capacity of PEM electrolyzer: {round(capacity_PEM_electrolyzer.x, 8)} GW, i.e. a yearly energy demand of {round(capacity_PEM_electrolyzer.x, 2) * operating_hours_PEM_electrolyzer} GWh")
print(f"capacity of alkaline electrolyzer: {round(capacity_alkaline_electrolyzer.x, 8)} GW, i.e. a yearly energy demand of {round(capacity_alkaline_electrolyzer.x, 2) * operating_hours_alkaline_electrolyzer} GWh")
print(f"capacity of FT-synthesis: {round(capacity_FT_synthesis.x, 8)}" )
print(f"capacity of ammonia splitting: {round(capacity_ammonia_splitting.x, 8)} GW, i.e. a yearly energy demand of {round(capacity_ammonia_splitting.x, 2) * operating_hours_ammonia_splitting} GWh")
print(f"capacity of ammonia synthesis: {round(capacity_ammonia_synthesis.x, 8)} GW, i.e. a yearly energy demand of {round(capacity_ammonia_synthesis.x, 2) * operating_hours_ammonia_synthesis} GWh")
print(f"capacity of battery: {round(capacity_battery.x, 8)} GWh")

# Print the supply for each customer
for c in customers:
    supply_values = [y[c, t].x for t in time_horizon]
    print(f"Supply to {c}: {supply_values} GWh")

# Print the x1 x2, which indicate if wind or photovoltaic is used
# print("x1: ", x1.x)
# print("x2: ", x2.x)

# Print all variables related to transport
# print("x_ammonia_splitting: ", x_ammonia_splitting.x)
#print("x_transport_ammonia: ", x_transport['ammonia'].x)
# print("x_transport_hydrogen: ", x_transport['hydrogen'].x)
# print("x_transport_jetfuel", x_transport['jetfuel'].x)
transported_ammonia_values = [round(expr.getValue(),2) for expr in transported_ammonia]
transported_jetfuel_values = [round(expr.getValue(),2) for expr in transported_jetfuel]
transported_hydrogen_values = [round(expr.getValue(),2) for expr in transported_hydrogen]

print("transported_ammonia:", transported_ammonia_values)
print("transported_jetfuel:", transported_jetfuel_values)
print("transported_hydrogen:", transported_hydrogen_values)

# Print all variables related to the CO2 source
print("CO2 required", [transported_jetfuel[t-1].getValue() * CO2_demand_per_unit_jetfuel for t in time_horizon])

print("x_dac:", [x_dac[t-1].x for t in time_horizon])
print("x_point_source:", [x_point_source[t-1].x for t in time_horizon]) 
print("point_source_availability:", [point_source_availability[t-1] for t in time_horizon]) 
print("point_source_amount:", [point_source_amount[t-1].x for t in time_horizon])
print("dac_amount:", [dac_amount[t-1].x for t in time_horizon])

# for expr in point_source_costs:
#     print("point_source_costs:", expr.getValue())
# for expr in dac_costs:
#     print("dac_costs:", expr.getValue())

cash_outflow_co2_print = [expr.getValue() for expr in cash_outflow_co2]
print("cash_outflow_co2: ", cash_outflow_co2_print)


print("init_investment:", init_investment_var.x)
print("area occupied:", capacity_photovoltaic.x / capacity_per_unit_area['photovoltaic'] + capacity_wind.x / capacity_per_unit_area['wind'])


# print("dac_costs:", [300 * dac_amount[t].x * x_dac for t in time_horizon])
# print("transported_ammonia: ", transported_ammonia)
# print("transported_hydrogen", transported_hydrogen)

# Print all vars
# all_vars = model.getVars()
# values = model.getAttr("X", all_vars)
# names = model.getAttr("VarName", all_vars)

# # for name, val in zip(names, values):
# #     print(f"{name} = {val}")


####### Testing for Finance Plan
# print("cash_inflow_customer_1: ", [model.getVarByName(f'y_Customer_1_Steel_Plant_{i}').x * price_per_unit['hydrogen'] for i in range(1, 11)])
# print("cash_inflow_customer_2: ", [model.getVarByName(f'y_Customer_2_Chemical_Plant_{i}').x * price_per_unit['ammonia'] for i in range(1, 11)])
# print("cash_inflow_customer_3: ", [model.getVarByName(f'y_Customer_3_Airport_{i}').x * price_per_unit['jetfuel'] for i in range(1, 11)])

# print(cash_outflow_photovoltaic.getValue())
# print(cash_outflow_wind.getValue())
# print(cash_outflow_PEM_electrolyzer.getValue())
# print(cash_outflow_alkaline_electrolyzer.getValue())
# print(cash_outflow_FT_synthesis.getValue())
# print(cash_outflow_ammonia_synthesis.getValue())
# print(cash_outflow_ammonia_splitting.getValue())
print("cash_outflow_transport: ",cash_outflow_transport[0].getValue())
# print(cash_outflow_co2[0].getValue())
# print(cash_outflow_battery.getValue())

####### Testing the NPV

NPV_t = {}
NPV_t[0] = - 0.5 * init_investment_var.x / (1+i)
NPV_t[1] = NPV_t[0] - 0.5 * init_investment_var.x / (1+i)** 2
for t in time_horizon:
    NPV_t[t+1] = NPV_t[t] + ( cash_inflow_customer_1[t - 1] 
    + cash_inflow_customer_2[t - 1] 
    + cash_inflow_customer_3[t - 1] 
    - cash_outflow_photovoltaic
    - cash_outflow_wind
    - cash_outflow_PEM_electrolyzer
    - cash_outflow_alkaline_electrolyzer
    - cash_outflow_FT_synthesis
    - cash_outflow_ammonia_synthesis
    - cash_outflow_ammonia_splitting
    - cash_outflow_transport[t - 1]
    - cash_outflow_co2[t-1]
    - cash_outflow_battery) / ((1 + i) ** (t+2))
# for index in NPV_t:
    # print(NPV_t[index])

# Export values to csv File
variable_values={}
for v in model.getVars():
    variable_values[v.VarName]=v.x
    
csv_file_path = 'results Pathway D.csv'

with open(csv_file_path, "w", newline="") as file:
    writer = csv.writer(file)

    # Write the header row (variable names)
    writer.writerow(["Variable", "Value"])

    # Write the variable values row by row
    for var_name, var_value in variable_values.items():
        writer.writerow([var_name, var_value])    
