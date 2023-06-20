capex = {
    'alkaline_electrolyzer': 10000,  # Example capital expenditure for alkaline electrolyzer
    'PEM_electrolyzer': 15000,  # Example capital expenditure for PEM electrolyzer
}

capacity_alkaline_electrolyzer = 10  # Example capacity of alkaline electrolyzer
capacity_PEM_electrolyzer = 15  # Example capacity of PEM electrolyzer

LCOH = {
    'alkaline_electrolyzer': capex['alkaline_electrolyzer'] * capacity_alkaline_electrolyzer,
    'PEM_electrolyzer': capex['PEM_electrolyzer'] * capacity_PEM_electrolyzer,
}

print(LCOH)  # Output the LCOH dictionary

