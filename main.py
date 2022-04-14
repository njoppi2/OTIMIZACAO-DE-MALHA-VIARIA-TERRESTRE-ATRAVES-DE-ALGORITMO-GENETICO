import random
from time import time
from individual import Individual
from load_place import create_net_file_from
from ga import GeneticAlgorithm
from problem_definition import ProblemDefinition
from user_model import UMSalmanAlaswad_I
from utils import place_name
import os

def run_genetic_algorithm(user_model, iteration, dirName, n_ind = 20, n_gen = 50, mut_rate = 0.1, elite_ind = 0.1, mated_ind = 0.25, selection_technique = "torneio"):
    # timeA = time.time()
    problem = user_model.problem
    best_individual_history = []
    average_fitness_history = []

    TOTAL_NUMBER_OF_GENERATIONS = n_gen
    TOTAL_NUMBER_OF_INDIVIDUALS = n_ind
    TOTAL_NUMBER_OF_ELITE_INDIVIDUALS = int(TOTAL_NUMBER_OF_INDIVIDUALS * elite_ind)
    TOTAL_NUMBER_OF_MATED_INDIVIDUALS = int(TOTAL_NUMBER_OF_INDIVIDUALS * mated_ind)
    TOTAL_NUMBER_OF_RANDOM_INDIVIDUALS = TOTAL_NUMBER_OF_INDIVIDUALS - TOTAL_NUMBER_OF_ELITE_INDIVIDUALS - TOTAL_NUMBER_OF_MATED_INDIVIDUALS
    SELECTION_TECHNIQUE = selection_technique
    RANDOM_INDIVIDUAL_TECHNIQUE = "new population"
    
    ga = GeneticAlgorithm(user_model, mut_rate)
    fitness_list = []
    selected_parents = []
    total_fitness_sum = 0
    best_individual = None

    current_generation_individuals = ga.createInitialPopulation(TOTAL_NUMBER_OF_INDIVIDUALS)
    new_generation_individuals = []

    #receives two Individuals, does crossover, mutation, and returns a new Individual
    def mate(father, mother):
        # do crossover
        fatherModifications = father.getRandomModifications()
        motherModifications = mother.getRandomModifications()

        child = Individual(user_model)
        child.setModifications(fatherModifications, motherModifications)
        mutation(child)

        return child

    def getAleatoryTrackIdsForMutation():
        trackIds = []
        while len(trackIds) < round((len(problem.tracks) - 1) * ga.mutationRate):
            aleatoryId = random.randint(0, len(problem.tracks) - 1)
            if aleatoryId not in trackIds:
                trackIds.append(aleatoryId)
        return trackIds

    def mutation(ind):
        trackIds = getAleatoryTrackIdsForMutation()
        while len(trackIds) > 0:
            randomNumber = random.randint(1, 2)
            if randomNumber == 1:
                ga.mutationAddLane(ind, trackIds)
            elif randomNumber == 2:
                ga.mutationAddLaneOnRoad(ind, trackIds)
        return ind


    def draw_individual(selection_technique):
        if selection_technique == "roleta":
            worst_individual = min(fitness_list, key=lambda ind: ind.fitness)
            worst_fitness = worst_individual.fitness
            increased_difference_total_fitness_sum = total_fitness_sum - worst_fitness * TOTAL_NUMBER_OF_INDIVIDUALS
            random_number = random.uniform(0, 1) * increased_difference_total_fitness_sum

            #stores the sum of the population fitness until the current individual
            previous_fitness_sum = 0

            # find winner individual
            for i in range(TOTAL_NUMBER_OF_INDIVIDUALS):

                individual_fitness = fitness_list[i].fitness
                increased_difference_ind_fitness = individual_fitness - worst_fitness
                previous_fitness_sum += increased_difference_ind_fitness
                if previous_fitness_sum >= random_number:
                    return current_generation_individuals[i]

        elif selection_technique == "torneio":
            # picks k random individuals from current_generation_individuals
            competitors = random.choices(current_generation_individuals, k=5)

            # returns competitor with max fitness
            winner = max(competitors, key=lambda ind: ind.fitness)

            return winner

        elif selection_technique == "aleatorio":
            
            # returns ANY individual, with no criteria
            return random.choice(current_generation_individuals)
        



    # runs the genetic algorithm on the number of generations specified
    for gen in range(TOTAL_NUMBER_OF_GENERATIONS):

        # fills the fitness_list and calculates total_fitness_sum
        for i in range(TOTAL_NUMBER_OF_INDIVIDUALS):

            individual = current_generation_individuals[i]
            individual.calculateFitness()
            fitness_list.append(individual)
            total_fitness_sum += (individual.fitness or 0)

        # we need to sort the fitness_list by their fitness in order to easily find the best individuals
        sorted_fitness_list = sorted(fitness_list, key=lambda d: d.fitness, reverse=True)
        best_individual = sorted_fitness_list[0]

        average_fitness_history.append("gen: " + str(gen + 1) + "\t\t\t" + "average fitness: " + str(round(total_fitness_sum / TOTAL_NUMBER_OF_INDIVIDUALS, 4)))
        best_individual_history.append("gen: " + str(gen + 1) + "\t\t\t" + "best fitness: " + str(round(best_individual.fitness, 4)) + "\t" + str(best_individual))


        # selection / create selected_parents list
        for i in range(TOTAL_NUMBER_OF_MATED_INDIVIDUALS):

            father = draw_individual(SELECTION_TECHNIQUE)
            mother = draw_individual(SELECTION_TECHNIQUE)

            while mother == father:
                mother = draw_individual(SELECTION_TECHNIQUE)

            selected_parents.append({
                "father": father,
                "mother": mother
            })

            # mate parents to create new generation
            new_generation_individuals.append(mate(**selected_parents[i]))


        # add elite individuals to generation_individuals
        for i in range(TOTAL_NUMBER_OF_ELITE_INDIVIDUALS):
            new_generation_individuals.append(sorted_fitness_list[i])


        # add random_individuals to generation_individuals
        if RANDOM_INDIVIDUAL_TECHNIQUE == "new population":
            new_generation_individuals.extend(ga.createInitialPopulation(TOTAL_NUMBER_OF_RANDOM_INDIVIDUALS))
        elif RANDOM_INDIVIDUAL_TECHNIQUE == "current population":
            non_elitist_individuals = current_generation_individuals[TOTAL_NUMBER_OF_ELITE_INDIVIDUALS:]
            chosen_individuals = random.choices(non_elitist_individuals, k=TOTAL_NUMBER_OF_RANDOM_INDIVIDUALS)
            new_generation_individuals.extend(chosen_individuals)

        #updates the current_population
        current_generation_individuals = new_generation_individuals
        new_generation_individuals = []
        fitness_list = []
        total_fitness_sum = 0

    #trecho de código a ser utilizado durante os testes, deve ser removido após isso

    if (dirName):
        arquivo = open(dirName + '/arq' + str(iteration) + '.txt', 'w')
        arquivo.write("\n\nPARAMETROS:\n\n")
        arquivo.write("TOTAL_NUMBER_OF_INDIVIDUALS:\t\t\t" + str(TOTAL_NUMBER_OF_INDIVIDUALS) + "\n")
        arquivo.write("TOTAL_NUMBER_OF_GENERATIONS:\t\t\t" + str(TOTAL_NUMBER_OF_GENERATIONS) + "\n")
        arquivo.write("TOTAL_NUMBER_OF_ELITE_INDIVIDUALS:\t\t" + str(TOTAL_NUMBER_OF_ELITE_INDIVIDUALS) + "\n")
        arquivo.write("TOTAL_NUMBER_OF_RANDOM_INDIVIDUALS:\t\t" + str(TOTAL_NUMBER_OF_RANDOM_INDIVIDUALS) + "\n")
        arquivo.write("TOTAL_NUMBER_OF_MATED_INDIVIDUALS:\t\t" + str(TOTAL_NUMBER_OF_MATED_INDIVIDUALS) + "\n")
        arquivo.write("SELECTION_TECHNIQUE:\t\t\t\t\t" + SELECTION_TECHNIQUE + "\n")
        arquivo.write("MUTATION_RATE:\t\t\t\t\t\t\t" + str(ga.mutationRate * 100) + "%" + "\n")
        
        arquivo.write("\n\nAVERAGE_FITNESS_HISTORY:\n\n"+"\n".join(average_fitness_history))
        arquivo.write("\n\nBEST_INDIVIDUAL_HISTORY:\n\n"+"\n".join(best_individual_history))
        arquivo.close()

        print(dirName + " created")

    return best_individual

    # best_individual.printDesign()





random.seed(0)
file_name = create_net_file_from(place_name)
problem = ProblemDefinition(file_name)
salmanAlaswad_model = UMSalmanAlaswad_I(problem)

original_ind = Individual(salmanAlaswad_model)
original_ind.calculateFitness()
print("problem fitness: ", original_ind.fitness)

TOTAL_NUMBER_OF_INDIVIDUALS_LIST = [20]
MUTATION_RATE = [0.1]
TOTAL_NUMBER_OF_ELITE_INDIVIDUALS_LIST = [0.1]
TOTAL_NUMBER_OF_MATED_INDIVIDUALS_LIST = [0.25]
SELECTION_TECHNIQUES_LIST = ["torneio"]
NUMBER_OF_GENERATIONS = 10
ITERATIONS_FROM_SAME_PARAMETERS = 1

t1 = time()
for n_ind in TOTAL_NUMBER_OF_INDIVIDUALS_LIST:
    for mut_rate in MUTATION_RATE:
        for elite_ind in TOTAL_NUMBER_OF_ELITE_INDIVIDUALS_LIST:
            for mated_ind in TOTAL_NUMBER_OF_MATED_INDIVIDUALS_LIST:
                for selection_technique in SELECTION_TECHNIQUES_LIST:
                    dirName = "ind-"+str(n_ind) + "-mut-"+str(mut_rate) + "-elite-"+str(elite_ind) + "-mated-" + str(mated_ind) + "-sel-" + str(selection_technique)
                    best_ind_per_file = []
                    if not os.path.isdir(dirName):
                        os.mkdir(dirName)
                    
                    parameters = {
                        "n_ind": n_ind,
                        "n_gen": NUMBER_OF_GENERATIONS,
                        "mut_rate": mut_rate,
                        "elite_ind": elite_ind,
                        "mated_ind": mated_ind,
                        "selection_technique": selection_technique
                    }
                    for iteration in range(ITERATIONS_FROM_SAME_PARAMETERS):
                        best_ind = run_genetic_algorithm(salmanAlaswad_model, iteration + 1, dirName, **parameters)
                        best_ind_per_file.append(best_ind)

                    #create PNG for best individual in folder

                    best_folder_ind = max(best_ind_per_file, key=lambda k: k.fitness)
                    print("best fitness: ", best_folder_ind.fitness)
                    best_folder_ind.printDesign(dirName=dirName, plot=False)

t2 = time()
print("total time: ", t2 - t1)
