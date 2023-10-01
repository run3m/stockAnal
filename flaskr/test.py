import re;

def get_cleaned_header(input_string):
    if(input_string):
        input_string = re.sub(r'\n+', '', str(input_string))
        input_string = input_string.lower().strip().replace(" ", "_");
        return re.sub(r'[^a-zA-Z0-9_]', '', input_string);
    return input_string 
    
def get_cleaned_string(input_string):
    if(input_string):
        return re.sub(r'\n\s+', '', input_string)
    
print(get_cleaned_header(str("\n            Name\n          ")))
print(get_cleaned_string(str("\n            Medinova Diagno.\n          ")))
print(get_cleaned_header(str("\n            Medinova Diagno.\n          ")))

