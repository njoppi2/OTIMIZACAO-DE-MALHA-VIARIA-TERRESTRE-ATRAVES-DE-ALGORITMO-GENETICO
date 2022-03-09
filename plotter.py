import os
import shutil
import numpy as np
import re
import matplotlib.pyplot as plt
 
TOTAL_NUMBER_OF_INDIVIDUALS_LIST = [10, 15, 20]
MUTATION_RATE = [0.01, 0.1]
TOTAL_NUMBER_OF_ELITE_INDIVIDUALS_LIST = [0.1, 0.2]
TOTAL_NUMBER_OF_MATED_INDIVIDUALS_LIST = [0.25, 0.5]
SELECTION_TECHNIQUES_LIST = ["torneio", "roleta", "aleatorio"]
analysis_folder = "analysis"
#average_fitness
average_fitness_dict = {}
all_absolute_averages = []
#best_individual
best_file_per_folder_dict = {}
all_best_folder_ind = []

def mean(a):
    return sum(a) / len(a)

for individuals in TOTAL_NUMBER_OF_INDIVIDUALS_LIST:
    for mut_rate in MUTATION_RATE:
        for elite in TOTAL_NUMBER_OF_ELITE_INDIVIDUALS_LIST:
            for mated_individuals in TOTAL_NUMBER_OF_MATED_INDIVIDUALS_LIST:
                for selection_technique in SELECTION_TECHNIQUES_LIST:
                    dirname = "ind-"+str(individuals) + "-mut-"+str(mut_rate) + "-elite-"+str(elite) + "-mated-" + str(mated_individuals) + "-sel-" + str(selection_technique)
                    folder_fitnesses = []
                    folder_invididuals = []

                    for file_number in range(10):
                        file_fitnesses = []
                        file_individuals = []
                        is_after_average_fitness_history = False
                        is_after_best_individual_history = False
                        with open(dirname + "/arq" + str(file_number + 1) + ".txt") as filestream:
                            for unstripped_line in filestream:
                                line = unstripped_line.strip()
                                if "AVERAGE_FITNESS_HISTORY:" in line:
                                    is_after_average_fitness_history = True
                                if "BEST_INDIVIDUAL_HISTORY:" in line:
                                    is_after_best_individual_history = True
                                if is_after_average_fitness_history and not is_after_best_individual_history:
                                    if "gen:" in line:
                                        regex_match = re.search('(?<=fitness: )[^\s]+', line)
                                        gen_fitness = float(regex_match.group(0))
                                        file_fitnesses.append(gen_fitness)
                                if is_after_best_individual_history:
                                    if "gen" in line:
                                        regex_match = re.search('(?<=fitness: )[^\s]+', line)
                                        gen_individual = float(regex_match.group(0))
                                        file_individuals.append(gen_individual)
                        folder_fitnesses.append(file_fitnesses)
                        folder_invididuals.append(file_individuals)
                        # plt.plot(file_individuals, label = "line " + str(file_number), color="black")

                    #average_fitness
                    folder_average_fitness_per_gen = list(map(mean, zip(*folder_fitnesses)))
                    folder_absolute_average = mean(folder_average_fitness_per_gen)
                    average_fitness_dict[dirname] = folder_average_fitness_per_gen
                    all_absolute_averages.append({
                        "folder_absolute_average": folder_absolute_average,
                        "dirname": dirname
                    })

                    #best_individual
                    folder_best_ind_per_file = list(map(lambda k: max(k), folder_invididuals))
                    max_value_in_folder = max(folder_best_ind_per_file)
                    best_file_number = folder_best_ind_per_file.index(max_value_in_folder)
                    best_file_per_folder_dict[dirname] = best_file_number
                    all_best_folder_ind.append({ 
                        "max_value_in_folder": max_value_in_folder,
                        "dirname": dirname,
                        "individuals": folder_invididuals[best_file_number]
                    })

def plot_graph(title):
    # naming the x axis
    plt.xlabel('geração')
    # naming the y axis
    plt.ylabel('fitness')
    # giving a title to my graph
    plt.title(title)
    
    # show a legend on the plot
    plt.legend()
    
    # function to show the plot
    plt.show()
    plt.clf()


#print average
sorted_all_absolute_averages = sorted(all_absolute_averages, key=lambda k: k["folder_absolute_average"], reverse=True) 

for i in range(10):
    position_i = average_fitness_dict[sorted_all_absolute_averages[i]["dirname"]]
    plt.plot(position_i, label = sorted_all_absolute_averages[i]["dirname"])

plot_graph("Fitness médio por geração")

#print best individuals
sorted_all_best_folder_ind = sorted(all_best_folder_ind, key=lambda k: k["max_value_in_folder"], reverse=True)

for i in range(10):
    label = sorted_all_best_folder_ind[i]["dirname"]
    values = sorted_all_best_folder_ind[i]["individuals"]
    plt.plot(values, label = label)

plot_graph("Indivíduo com maior fitness")


#create table of best individuals
if not os.path.isdir(analysis_folder):
    os.mkdir(analysis_folder)
    
arquivo = open(analysis_folder + '/ind_table.txt', 'w')

arquivo.write("\n\nRANKING DE MELHORES INDIVÍDUOS:\n\n")
for index, individual in enumerate(sorted_all_best_folder_ind):
    arquivo.write("Colocação: " + str(index + 1) + "º\t\t" "Conjunto de parâmetros: \t" + "{:<50}".format(str(individual["dirname"])) + "  \tFitness: \t" + str(individual["max_value_in_folder"]) + "\n")
    shutil.copy2( individual["dirname"]+'/best_individual.png', analysis_folder + "/" + str(index + 1) + 'individual-' + individual["dirname"] + '.png')

