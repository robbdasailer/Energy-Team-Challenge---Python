def calculate_npv(cashflows, discount_rate):
    npv = 0
    for i, cashflow in enumerate(cashflows):
        npv += cashflow / (1 + discount_rate) ** i
        print("NPV after period", i, ":", npv)
    return npv

def calculate_payback_period(cashflows, discount_rate):
    cumulative_discounted_cashflow = 0
    payback_period = 0
    for i, cashflow in enumerate(cashflows):
        print(i)
        discounted_cashflow = cashflow / (1 + discount_rate) ** (i)
        cumulative_discounted_cashflow += discounted_cashflow
        if cumulative_discounted_cashflow >= 0:
            payback_period = i  # Add 1 to get the period count
            break
    return payback_period

# Assumptions
discount_rate = 0.1  # Discount rate (10%)

# Cashflows
cashflows = [-1000, 500, 400, 300, 250]  # Cashflows for each period

def calc_Investment (price_photovoltaic, price_wind):
    investment = investment_costs_photovoltaic + investment_costs_wind
    
    investment_costs_photovoltaic = production_photovoltaic * price_photovoltaic
    investment_costs_wind = production_wind * price_wind
    
    return investment


# Boundary conditions
demand_steel_plant < 1000 #GWh
demand_steel_plant > 800 #GWh

demand_chemical_plant < 500 #GWh
demand_chemical_plant > 0 #GWh

demand_chemical_airport < 500 #GWh
demand_chemical_airport > 0 #GWh

price_photovoltaic = 0.11 #€/kWh
price_wind = 0.2 #€/kWh


# Calculate NPV
npv_result = calculate_npv(cashflows, discount_rate)
print("Net Present Value (NPV):", npv_result)

# Calculate Payback Period
payback_period = calculate_payback_period(cashflows, discount_rate)
if payback_period > 0:
    print("Payback period:", payback_period)
else:
    print("Investment never pays back")
