from load_place import create_net_file_from
from ga import run_genetic_algorithm
from problem_definition import ProblemDefinition

place_name = "Borá, Brazil"

file_name = create_net_file_from(place_name)
problem = ProblemDefinition(file_name)
run_genetic_algorithm(problem)

