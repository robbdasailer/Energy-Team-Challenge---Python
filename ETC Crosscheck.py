# This code will take the optimal pathway assessed by the linear optimization and based on this, will calculate the NPV "manually".
# In doing so, we check whether out linear optimization model returns realistic results.
# Overall units:
    # energy: GWh
    # capacity: GW
    # area: km^2
    # money: €
# Define customers
customers = ['Customer_1_Steel_Plant', 'Customer_2_Chemical_Plant', 'Customer_3_Airport']

# Define time horizon
time_horizon = range(1, 31)  # Time periods from 1 to 30, including a 2 year construction phase

# Define selling prices
price_per_unit = {
    'hydrogen': 210000,
    'ammonia': 287000,
    'jetfuel': 252000, 
}

# Define typical capacity per unit area in GW/km^2
capacity_per_unit_area = {
    'photovoltaic': 20,
    'wind': 30,
}

# CO2 demand for 1GWh of jetfuel in tons/GWh.
CO2_demand_per_unit_jetfuel = 260 

# CAPEX 
capex = {
    'photovoltaic': 650 * 10 ** 6,
    'wind': 1500 * 10 ** 6,
    'PEM_electrolyzer': 700 * 10 ** 6,
    'alkaline_electrolyzer': 650 * 10 ** 6,
    'FT_synthesis': 1200 * 10 ** 6,
    'ammonia_synthesis': 1400 * 10 ** 6,
    'ammonia_splitting': 700 * 10 **6,
    'battery': 250 * 10 **6, #in €/GWh
}

opex = {
    'photovoltaic': 0.03 * capex['photovoltaic'],
    'wind': 0.04 * capex['wind'],
    'PEM_electrolyzer': 0.04 * capex['PEM_electrolyzer'],
    'alkaline_electrolyzer': 0.04 * capex['alkaline_electrolyzer'],
    'FT_synthesis': 0.05 * capex['FT_synthesis'],
    'ammonia_synthesis': 0.05 * capex['ammonia_synthesis'],
    'ammonia_splitting': 0.05 * capex['ammonia_splitting'],
    'battery': 0 * capex['battery'], #Zahlen einfügen
}

transport_costs = {
    'hydrogen': 20 * 10**3, 
    'ammonia': 10 * 10**3,
    'jetfuel': 5 * 10**3,
}

point_source_costs = 70 

# Decision variables
x = {
    'photovoltaic': 0,              # Do you want to use PV..
    'wind': 1,                      # or do you want to use wind?
    'PEM_electrolyzer': 1,          # Do you want to use PEM..
    'alkaline_electrolyzer': 0,     # or do you want to use Alkaline?
    'FT_synthesis': 1,
    'ammonia_synthesis': 1,
    'ammonia_splitting': 0,
    'battery': 1,
    }

x_transport = {
    'hydrogen': 1,                  # Do you want to produce hydrogen in morocco?
    'ammonia': 1,                   # Do you want to produce ammonia in morocco?
    'jetfuel': 0,                   # Do you want to produce jetfuel in morocco?
}

# Define supply to customers
y = {}
y['Customer_1_Steel_Plant'] = {}
y['Customer_2_Chemical_Plant'] = {}
y['Customer_3_Airport'] = {}

for t in time_horizon:
    y['Customer_1_Steel_Plant'][t-1] = 1000
    y['Customer_2_Chemical_Plant'][t-1] = 433.33
    y['Customer_3_Airport'][t-1] = 250
    
# Define the size of technologies in GW
capacity = {
    'photovoltaic': 0,
    'wind': 0.5746,
    'PEM_electrolyzer': 0.328,
    'alkaline_electrolyzer': 0,
    'FT_synthesis': 0.0333,
    'ammonia_synthesis': 0.0578,
    'ammonia_splitting':0,
    'battery': 1.5752, #in GWh
}

# Compute transportedd amounts in GWh
transported_product = {
    'ammonia':  433.33,
    'jetfuel': 0,
    'hydrogen': 1469.48
}

technologies = ['photovoltaic', 'wind', 'PEM_electrolyzer', 'alkaline_electrolyzer', 'FT_synthesis', 'ammonia_synthesis','ammonia_splitting','battery']
products = ['hydrogen', 'ammonia', 'jetfuel']


cash_inflow_customer = {}

for c in customers:
    cash_inflow_customer[c] = {}
    for t in time_horizon:
        if c == 'Customer_1_Steel_Plant':
            cash_inflow_customer[c][t-1] = price_per_unit['hydrogen'] * y[c][t-1]
        elif c == 'Customer_2_Chemical_Plant':
            cash_inflow_customer[c][t-1] = price_per_unit['ammonia'] * y[c][t-1]
        elif c == 'Customer_3_Airport':
            cash_inflow_customer[c][t-1] = price_per_unit['jetfuel'] * y[c][t-1] / 0.71
        


# Initial Investment
init_investment_tech = {}

for i in technologies:
    init_investment_tech[i] = capex[i] * capacity[i] 

init_investment = sum(init_investment_tech[i] for i in technologies)

# Test the initial investment
# for i in technologies:
#     print("initial investment for " + i + ":  "+ str(init_investment_tech[i]))
print("total initial investment: " + str(init_investment))

cash_inflow = {}

for t in time_horizon:
    cash_inflow[t-1] = sum(cash_inflow_customer[c][t-1] for c in customers)

# Testing 
print("cash inflow of customer ")

print("total cash inflow per period: ", cash_inflow)

print("total cash inflow over whole time frame: ", sum(cash_inflow[t-1] for t in time_horizon))

# CO2 costs
cash_outflow_CO2 = {}

for t in time_horizon:
    cash_outflow_CO2 [t-1] = CO2_demand_per_unit_jetfuel * point_source_costs * y['Customer_3_Airport'][t-1]

cash_outflow_technology = {}

for i in technologies:
    cash_outflow_technology[i] = {}
    for t in time_horizon:
        cash_outflow_technology[i][t-1] = opex[i]  * capacity[i]

cash_outflow_transport = {}
for i in products:
    cash_outflow_transport[i] = {}
    for t in time_horizon:
        cash_outflow_transport[i][t-1] = transported_product[i] * transport_costs[i]

cash_outflow = {}

for t in time_horizon:
    cash_outflow[t-1] = sum(cash_outflow_technology[i][t-1] for i in technologies) + sum(cash_outflow_transport[i][t-1] for i in products) + cash_outflow_CO2[t-1]

print(sum(cash_outflow[t-1]for t in time_horizon))
# # Test the Cash Outflows
# # Test the cash flow of technologies
# for i in technologies:
#     print(i)
#     for t in time_horizon:
#         print("cash outflow for technology " + i + " in " + str(t) +": " + str(cash_outflow_technology[i][t-1]))

# # Test the cash flow of transport
# for i in products:
#     print(i)
#     for t in time_horizon:
#         print("cash outflow " + "for transport of " + i + " in " + str(t) +": " + str(cash_outflow_transport[i][t-1]))

# # Test the cash flow of co2 source
# for t in time_horizon:
#     print("cash outflow for co2 source in " + str(t) + ": " + str(cash_outflow_CO2[t-1]))


# Calculate Net Present Value
i = 0.1
NPV = - 0.5 * init_investment / (1+i) - 0.5 * init_investment / (1+i)**2 + sum(( cash_inflow[t-1] - cash_outflow[t-1]) / ((1 + i) ** (t+2)) for t in time_horizon)
print("Resulting NPV: ", NPV)

NPV_t = {}
NPV_t[0] = - 0.5 * init_investment 
NPV_t[1] = NPV_t[0] - 0.5 * init_investment / (1+i)

for t in time_horizon:
    NPV_t[t+1] = NPV_t[t] + ( cash_inflow[t-1] - cash_outflow[t-1]) / ((1 + i) ** (t+1))
for index in NPV_t:
    print("NPV " + str(index+2023) + ": " + str(NPV_t[index]))



