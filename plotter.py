import math
import os
import shutil
import numpy as np
import re
import matplotlib.pyplot as plt


TOTAL_NUMBER_OF_INDIVIDUALS_LIST = [10, 20, 40]
MUTATION_RATE = [0, 0.05, 0.2]
TOTAL_NUMBER_OF_ELITE_INDIVIDUALS_LIST = [0, 0.1, 0.3]
TOTAL_NUMBER_OF_MATED_INDIVIDUALS_LIST = [0.2, 0.5, 0.7]
SELECTION_TECHNIQUES_LIST = ["tournament", "roulette", "random"]
RANDOM_INDIVIDUAL_TECHNIQUE = ["new population", "current population"]
NUMBER_OF_GENERATIONS = 50
ITERATIONS_FROM_SAME_PARAMETERS = 10
analysis_folder = "analysis"
#average_fitness
average_fitness_dict = {}
average_of_best_fitnesses_dict = {}
all_absolute_averages = []
all_absolute_averages_of_best_individual = []
#best_individual
best_file_per_folder_dict = {}
all_best_folder_ind = []
final_fitness_of_files_per_folder = {}

def mean(a):
    return sum(a) / len(a)

def parseSelectionName(name):
    return {
        "tournament": "torneio",
        "roulette": "roleta",
        "random": "aleatorio"
    }[name]

for individuals in TOTAL_NUMBER_OF_INDIVIDUALS_LIST:
    for mut_rate in MUTATION_RATE:
        for elite in TOTAL_NUMBER_OF_ELITE_INDIVIDUALS_LIST:
            for mated_individuals in TOTAL_NUMBER_OF_MATED_INDIVIDUALS_LIST:
                for selection_technique in SELECTION_TECHNIQUES_LIST:
                    for random_ind_technique in RANDOM_INDIVIDUAL_TECHNIQUE:
                        dirname = "ind-"+str(individuals) + "-mut-"+str(mut_rate) + "-elite-"+str(elite) + "-mated-" + str(mated_individuals) + "-sel-" + str(parseSelectionName(selection_technique)) + "-rand-" + str(random_ind_technique)
                        folder_avr_fitnesses_per_file = []
                        folder_best_fitnesses_per_file = []

                        for file_number in range(ITERATIONS_FROM_SAME_PARAMETERS):
                            file_avr_fitness_per_gen = []
                            file_best_fitness_per_gen = []
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
                                            file_avr_fitness_per_gen.append(gen_fitness)
                                    if is_after_best_individual_history:
                                        if "gen" in line:
                                            regex_match = re.search('(?<=fitness: )[^\s]+', line)
                                            gen_individual = float(regex_match.group(0))
                                            file_best_fitness_per_gen.append(gen_individual)
                            folder_avr_fitnesses_per_file.append(file_avr_fitness_per_gen)
                            folder_best_fitnesses_per_file.append(file_best_fitness_per_gen)
                            # plt.plot(file_individuals, label = "line " + str(file_number), color="black")

                        #average_fitness
                        folder_average_fitness_per_gen = list(map(mean, zip(*folder_avr_fitnesses_per_file)))
                        folder_absolute_average = mean(folder_average_fitness_per_gen)
                        average_fitness_dict[dirname] = folder_average_fitness_per_gen
                        all_absolute_averages.append({
                            "folder_absolute_average": folder_absolute_average,
                            "dirname": dirname
                        })

                        #best_individual
                        folder_last_fitness_per_file = list(map(lambda k: k[-1], folder_best_fitnesses_per_file))
                        final_fitness_of_files_per_folder[dirname] = folder_last_fitness_per_file
                        max_value_in_folder = max(folder_last_fitness_per_file)
                        best_file_number = folder_last_fitness_per_file.index(max_value_in_folder)
                        best_file_per_folder_dict[dirname] = best_file_number
                        all_best_folder_ind.append({ 
                            "max_value_in_folder": max_value_in_folder,
                            "dirname": dirname,
                            "individuals": folder_best_fitnesses_per_file[best_file_number]
                        })
                        # best average of best individual per folder
                        folder_average_of_best_fitnesses = list(map(mean, zip(*folder_best_fitnesses_per_file)))
                        folder_final_average_of_best_individual = folder_average_of_best_fitnesses[-1]
                        average_of_best_fitnesses_dict[dirname] = folder_average_of_best_fitnesses
                        all_absolute_averages_of_best_individual.append({
                            "folder_final_average_of_best_individual": folder_final_average_of_best_individual,
                            "dirname": dirname,
                            "label": "individuals: " + str(individuals) + ", selection: " + selection_technique + ", mutation rate: " + str(mut_rate) + ", elitism rate: " + str(elite) + ", mated rate: " + str(mated_individuals) + ", random individuals: " + str(random_ind_technique)
                        })

def plot_graph(title, xlabel = 'generation', ylabel = 'fitness'):
    # naming the x axis
    plt.xlabel(xlabel)
    # naming the y axis
    plt.ylabel(ylabel)
    # giving a title to my graph
    plt.title(title)
    # show a legend on the plot
    plt.legend()
    
    # function to show the plot
    plt.show()
    plt.clf()


# # print average

# sorted_all_absolute_averages = sorted(all_absolute_averages, key=lambda k: k["folder_absolute_average"], reverse=True) 

# for j in range(1):
#     for i in range(j*50, (j+1)*50-40):
#         position_i = average_fitness_dict[sorted_all_absolute_averages[i]["dirname"]]
#         plt.plot(position_i, label = sorted_all_absolute_averages[i]["dirname"])
#         plt.ylim([142.5, 143.7])
#         plt.margins(x=0.003, y=0.001)

#     plot_graph("Average fitness")


# # print best individuals

sorted_all_best_folder_ind = sorted(all_best_folder_ind, key=lambda k: k["max_value_in_folder"], reverse=True)

# for i in range(5):
#     label = sorted_all_best_folder_ind[i]["dirname"]
#     values = sorted_all_best_folder_ind[i]["individuals"]
#     plt.plot(values, label = label)

# plot_graph("Individuals with best fitness")

# print folder best individuals

sorted_all_absolute_averages_of_best_individual = sorted(all_absolute_averages_of_best_individual, key=lambda k: k["folder_final_average_of_best_individual"], reverse=True) 

for j in range(1):
    for i in range(j*5, (j+1)*5):
        position_i = average_of_best_fitnesses_dict[sorted_all_absolute_averages_of_best_individual[i]["dirname"]]
        plt.plot(position_i, label = sorted_all_absolute_averages_of_best_individual[i]["label"])
        plt.ylim([143.5, 144.7])
        plt.margins(x=0.003, y=0.001)
    plot_graph("Average of the best fitnesses")

# plotar curvas normais

values = {}
mutId = "mutation rate = "
eliteId = "elitism rate = "
matedId = "rate of mated individuals = "
indId =  "number of individuals = "

def increase_technique_values(technique, final_fitness_of_file):
    if technique not in values:
        values[technique] = np.zeros(NUMBER_OF_GENERATIONS) # creates a list of zeros, with size NUMBER_OF_GENERATIONS
    values[technique][math.ceil((final_fitness_of_file - fitness_start) / gen_increment)] += 1

def plot_techniques(list_of_techniques):
    id = ""
    title = ""
    colors = ['red', 'green', 'black']
    if list_of_techniques == SELECTION_TECHNIQUES_LIST:
        title = "Selection technique comparison"
    if list_of_techniques == RANDOM_INDIVIDUAL_TECHNIQUE:
        title = "Random individuals technique comparison"
    if list_of_techniques == MUTATION_RATE:
        title = "Mutation technique comparison"
        id = mutId
    if list_of_techniques == TOTAL_NUMBER_OF_ELITE_INDIVIDUALS_LIST:
        title = "Elitism technique comparison"
        id = eliteId
    if list_of_techniques == TOTAL_NUMBER_OF_MATED_INDIVIDUALS_LIST:
        title = "Mated individuals technique comparison"
        id = matedId
    if list_of_techniques == TOTAL_NUMBER_OF_INDIVIDUALS_LIST:
        title = "Number of individuals technique comparison"
        id = indId
    for index, technique in enumerate(list_of_techniques):
        plt.margins(x=0.003, y=0.001)  
        plt.plot(list(map(lambda x: x * gen_increment + fitness_start, range(NUMBER_OF_GENERATIONS))), values[id+str(technique)], label = id+str(technique), color = colors[index])

    plot_graph(title, 'fitness', 'number of occurences')


for random_ind_technique in RANDOM_INDIVIDUAL_TECHNIQUE:
    fitness_start = 143
    fitness_end = 144.80
    gen_increment = (fitness_end - fitness_start) / NUMBER_OF_GENERATIONS

    for selection_technique in SELECTION_TECHNIQUES_LIST:
        for mut_rate in MUTATION_RATE:
            for elite in TOTAL_NUMBER_OF_ELITE_INDIVIDUALS_LIST:
                for mated_individuals in TOTAL_NUMBER_OF_MATED_INDIVIDUALS_LIST:
                    for individuals in TOTAL_NUMBER_OF_INDIVIDUALS_LIST:
                        dirname = "ind-"+str(individuals) + "-mut-"+str(mut_rate) + "-elite-"+str(elite) + "-mated-" + str(mated_individuals) + "-sel-" + str(parseSelectionName(selection_technique)) + "-rand-" + str(random_ind_technique)
                        for final_fitness_of_file in final_fitness_of_files_per_folder[dirname]:
                            increase_technique_values(random_ind_technique, final_fitness_of_file)
                            increase_technique_values(selection_technique, final_fitness_of_file)
                            increase_technique_values(mutId+str(mut_rate), final_fitness_of_file)
                            increase_technique_values(eliteId+str(elite), final_fitness_of_file)
                            increase_technique_values(matedId+str(mated_individuals), final_fitness_of_file)
                            increase_technique_values(indId+str(individuals), final_fitness_of_file)
                            # criar um values para cada tecnica de cada parametro

plot_techniques(SELECTION_TECHNIQUES_LIST)
plot_techniques(MUTATION_RATE)
plot_techniques(TOTAL_NUMBER_OF_ELITE_INDIVIDUALS_LIST)
plot_techniques(TOTAL_NUMBER_OF_MATED_INDIVIDUALS_LIST)
plot_techniques(TOTAL_NUMBER_OF_INDIVIDUALS_LIST)
plot_techniques(RANDOM_INDIVIDUAL_TECHNIQUE)

#create table of best individuals
if not os.path.isdir(analysis_folder):
    os.mkdir(analysis_folder)
    
arquivo = open(analysis_folder + '/ind_table.txt', 'w')

arquivo.write("\n\nRANKING DE MELHORES INDIVÍDUOS:\n\n")
for index, individual in enumerate(sorted_all_best_folder_ind):
    arquivo.write("Colocação: " + str(index + 1) + "º\t\t" "Conjunto de parâmetros: \t" + "{:<50}".format(str(individual["dirname"])) + "  \tFitness: \t" + str(individual["max_value_in_folder"]) + "\n")
    shutil.copy2( individual["dirname"]+'/best_individual.png', analysis_folder + "/" + str(index + 1) + 'individual-' + individual["dirname"] + '.png')

