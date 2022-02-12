from load_place import create_net_file_from
from ga import run_genetic_algorithm
from problem_definition import ProblemDefinition
import os

place_name = "Borá, Brazil"

file_name = create_net_file_from(place_name)
problem = ProblemDefinition(file_name)


TOTAL_NUMBER_OF_INDIVIDUALS_LIST = [10, 15, 20]
MUTATION_RATE = [0.01, 0.1]
TOTAL_NUMBER_OF_ELITE_INDIVIDUALS_LIST = [0.1, 0.2]
TOTAL_NUMBER_OF_MATED_INDIVIDUALS_LIST = [0.25, 0.5]
SELECTION_TECHNIQUES_LIST = ["torneio", "roleta", "aleatorio"]

for individuals in TOTAL_NUMBER_OF_INDIVIDUALS_LIST:
    for mut_rate in MUTATION_RATE:
        for elite in TOTAL_NUMBER_OF_ELITE_INDIVIDUALS_LIST:
            for mated_individuals in TOTAL_NUMBER_OF_MATED_INDIVIDUALS_LIST:
                for selection_technique in SELECTION_TECHNIQUES_LIST:
                    dirName = "ind-"+str(individuals) + "-mut-"+str(mut_rate) + "-elite-"+str(elite) + "-mated-" + str(mated_individuals) + "-sel-" + str(selection_technique)
                    best_individual_per_file = []
                    if not os.path.isdir(dirName):
                        os.mkdir(dirName)
                    
                    parameters = {
                        "individuals": individuals,
                        "mut_rate": mut_rate,
                        "elite": elite,
                        "mated_individuals": mated_individuals,
                        "selection_technique": selection_technique
                    }
                    for iteration in range(10):
                        best_individual = run_genetic_algorithm(problem, iteration + 1, dirName, **parameters)
                        best_individual_per_file.append(best_individual)

                    #create PNG for best individual in folder

                    best_folder_individual = max(best_individual_per_file, key=lambda k: k.fitness)
                    best_folder_individual.printDesign(dirName)


