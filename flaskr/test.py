import re;

# def get_cleaned_header(input_string):
#     if(input_string):
#         input_string = re.sub(r'\n+', '', str(input_string))
#         input_string = input_string.lower().strip().replace(" ", "_");
#         return re.sub(r'[^a-zA-Z0-9_]', '', input_string);
#     return input_string 
    
# def get_cleaned_string(input_string):
#     if(input_string):
#         return re.sub(r'\n\s+', '', input_string)
    
# print(get_cleaned_header(str("\n            Name\n          ")))
# print(get_cleaned_string(str("\n            Medinova Diagno.\n          ")))
# print(get_cleaned_header(str("\n            Medinova Diagno.\n          ")))

str = "price_to_earning < 10, price_to_earning < 0.8*(industry_pe), price_to_book_value < 1.5,    working_capital > market_capitalization, current_ratio < 1.5, eps_growth_5years > 20, free_cash_flow_last_year > free_cash_flow_3years, peg_ratio < 0.9, return_on_capital_employed > 100, company_id in ['807', '3178']"

target = re.split(r',\s*(?![^(\[]*[\)\]])', str)

print(target);