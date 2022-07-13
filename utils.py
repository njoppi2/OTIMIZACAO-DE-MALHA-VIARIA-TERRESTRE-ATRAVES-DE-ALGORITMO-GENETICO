place_name = "São Pedro, Juiz de Fora, Brazil"
# place_name = "Borá, Brazil"
formated_place_name = place_name.replace(',', '_').replace(' ', '_')

# returns zero from when dividing by zero
def indentZero(value, divisor):
    if divisor != 0:
        return value / divisor
    else:
        return 0
