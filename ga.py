import random
from individual import Individual

from problem_definition import ProblemDefinition
from user_model import UMSalmanAlaswad_I


class GeneticAlgorithm:
    def __init__(self, problem):
        self.problem = problem
        self.generationSize = 10
        self.offspringSise = 5
        self.mutationRate = 0.001

    def mutationAddLane(self, ind, trackIds, chanceToStop=0.1):

        metersThreshold = self.problem.budgetUpdate * 1000.0 - ind.regularInsertedKMeters * 1000.0  # threshold of change to be designed
        metersReached = 0  # meters chaged

        # select a random node
        trackId = random.choice(trackIds)
        track = self.problem.tracks[trackId]
        trackIds.remove(trackId)
        trackList = []
        metersReached += track["distance"]
        node = track["t"]
        while metersReached < metersThreshold:
            trackList.append(trackId)
            if random.random() < chanceToStop:
                break
            # select a new destination
            if node in self.problem.adjLst:
                res = random.choice(list(self.problem.adjLst[node].items()))
                if res == None: break
                t = res[0]
                if t not in self.problem.adjLst[node]: break
                track = random.choice(self.problem.adjLst[node][t])
                if track == None: break
                trackId = track["id"]
                metersReached += track["distance"]
                node = track["t"]
        # updating new lanes
        for trackId in trackList:
            ind.setLaneValue(str(trackId), +1)

    def mutationAddLaneOnRoad(self, ind, trackIds):

        metersThreshold = self.problem.budgetUpdate * 1000.0 - ind.regularInsertedKMeters * 1000.0  # threshold of change to be designed
        metersReached = 0  # meters chaged

        trackList = []

        # repeat until find a road with more than one track
        while len(trackList) <= 1:
            trackList = []

            # select a random node
            if len(trackIds) == 0: break
            trackId = random.choice(trackIds)
            track = self.problem.tracks[trackId]
            metersReached = 0
            trackIds.remove(trackId)

            # finding the road starting node
            nodeStart = track["s"]
            lastNode = track["t"]
            if nodeStart not in self.problem.adjLst: break
            while len(list(self.problem.adjLst[nodeStart])) == 1:
                if nodeStart != lastNode:
                    track = self.problem.adjLst[nodeStart][lastNode][0]
                    metersReached += track["distance"]
                    trackId = int(track["id"])
                    trackList.append(trackId)
                    lastNode = nodeStart
                    if nodeStart in self.problem.adjLstInv:
                        nodeStart = next(iter(self.problem.adjLstInv[nodeStart]))
                else: break

            # finding the road last node

            lastNode = track["t"]
            if lastNode not in self.problem.adjLst: break
            while len(list(self.problem.adjLst[lastNode])) == 1:
                nextNode = next(iter(self.problem.adjLst[lastNode]))
                track = self.problem.adjLst[lastNode][nextNode][0]
                metersReached += track["distance"]
                trackId = int(track["id"])
                trackList.append(trackId)
                lastNode = nextNode
                if lastNode not in self.problem.adjLst: break

        if metersReached < metersThreshold:
            # updating new lanes
            for trackId in trackList:
                ind.setLaneValue(str(trackId), +1)

    def fitness(self, ind):
        return None

    def createInitialPopulation(self, size):
        initialPopulation = list()
        count = 0
        while count < size:
            initialPopulation.append(self.createNewRadomIndividual())
            count += 1
        return initialPopulation

    def createNewRadomIndividual(self):
        # create the individual
        individual = Individual(self.problem)

        # number of the iterations
        count = random.randint(1, 100)

        while count > 0:
            # random selection of a track source
            aleatoryTrackSource = str(random.randint(1, len(individual.tracks)))

            # random selection of a track target
            aleatoryTrackTarget = str(random.randint(1, len(individual.tracks)))

            # random selection of a track id
            aleatoryTrackId = str(random.randint(1, 1000))

            # random number for the option
            randomNumber = random.randint(1, 3)
            if randomNumber == 1:
                individual.insertAdditionalTrack(aleatoryTrackSource, aleatoryTrackTarget, 1500000, 1,
                                                 self.problem.maxSpeed)
            elif randomNumber == 2:
                individual.setLaneValue(aleatoryTrackId, random.randint(1, 5))
            else:
                individual.removeAdditionalTrack(aleatoryTrackSource, aleatoryTrackTarget, aleatoryTrackId)
            count -= 1

        return individual

def run_genetic_algorithm(problem):

    TOTAL_NUMBER_OF_INDIVIDUALS = 20
    TOTAL_NUMBER_OF_GENERATIONS = 10
    TOTAL_NUMBER_OF_ELITE_INDIVIDUALS = 2
    TOTAL_NUMBER_OF_RANDOM_INDIVIDUALS = int(TOTAL_NUMBER_OF_INDIVIDUALS / 2)
    TOTAL_NUMBER_OF_MATED_INDIVIDUALS = TOTAL_NUMBER_OF_INDIVIDUALS - TOTAL_NUMBER_OF_ELITE_INDIVIDUALS - TOTAL_NUMBER_OF_RANDOM_INDIVIDUALS
    ga = GeneticAlgorithm(problem)
    userModel = UMSalmanAlaswad_I()
    fitness_list = []
    selected_parents = []
    total_fitness_sum = 0
    best_individual = {
        "fitness": 0,
        "solution": None
    }

    current_generation_individuals = ga.createInitialPopulation(TOTAL_NUMBER_OF_INDIVIDUALS)
    new_generation_individuals = []

    #receives two Individuals, does crossover, mutation, and returns a new Individual
    def mate(father, mother):
        # do crossover
        fatherModifications = father.getRandomModifications()
        motherModifications = mother.getRandomModifications()

        child = Individual(problem)
        child.setModifications(problem, fatherModifications, motherModifications)
        mutation(child)

        return child

    def mutation(individual):
        aleatoryIndividualsMutationIndex = random.sample(range(TOTAL_NUMBER_OF_INDIVIDUALS), int(len(individual.newTracks)*ga.mutationRate))
        for i in range(len(individual.newTracks)):
            if i in aleatoryIndividualsMutationIndex:
                randomNumber = random.randint(1, 2)
                if randomNumber == 1:
                    ga.mutationAddLane(individual.newTracks[i])
                elif randomNumber == 2:
                    ga.mutationAddLaneOnRoad(individual.newTracks[i])

        return individual

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

    def mate(father, mother):
        # do crossover
        # do mutation
        # return new individual ↓
        return mutation(Individual(problem))

    def draw_individual():
        random_number = random.randint(0, total_fitness_sum)

        #stores the sum of the population fitness until the current individual
        previous_fitness_sum = 0

        # find winner individual
        for i in range(TOTAL_NUMBER_OF_INDIVIDUALS):

            individual_fitness = fitness_list[i]["fitness"]
            previous_fitness_sum += individual_fitness
            if previous_fitness_sum >= random_number:
                return current_generation_individuals[i]
        pass

    # runs the genetic algorithm on the number of generations specified
    for gen in range(TOTAL_NUMBER_OF_GENERATIONS):

        # fills the fitness_list and calculates total_fitness_sum
        for i in range(TOTAL_NUMBER_OF_INDIVIDUALS):

            individual = current_generation_individuals[i]
            # individual_fitness = userModel.fitness(individual)
            individual_fitness = random.randint(0, 100) #gambiarra
            fitness_list.append({
                "solution": individual,
                "fitness": individual_fitness
            })
            total_fitness_sum += fitness_list[i]["fitness"]

        # we need to sort the fitness_list by their fitness in order to easily find the best individuals
        sorted_fitness_list = sorted(fitness_list, key=lambda d: d["fitness"], reverse=True)
        best_individual = sorted_fitness_list[0]


        # selection / create selected_parents list
        for i in range(TOTAL_NUMBER_OF_MATED_INDIVIDUALS):

            father = draw_individual()
            mother = draw_individual()

            while mother == father:
                mother = draw_individual()

            selected_parents.append({
                "father": father,
                "mother": mother
            })

            # mate parents to create new generation
            new_generation_individuals.append(mate(**selected_parents[i]))


        # add elite individuals to generation_individuals
        for i in range(TOTAL_NUMBER_OF_ELITE_INDIVIDUALS):
            new_generation_individuals.append(sorted_fitness_list[i]["solution"])


        # add random_individuals to generation_individuals
        new_generation_individuals.extend(ga.createInitialPopulation(TOTAL_NUMBER_OF_RANDOM_INDIVIDUALS))

        #updates the current_population
        current_generation_individuals = new_generation_individuals
        new_generation_individuals = []
        fitness_list = []
        total_fitness_sum = 0
        print("generation: " + str(gen))

    # print("fitness: ", best_individual["fitness"])

    # print("regularInsertedKMeters: ", best_individual["solution"].regularInsertedKMeters)
    # print("newInsertedKMeters: ", best_individual["solution"].newInsertedKMeters)
    # print("fitness: ", best_individual["solution"].fitness)

    userModel.fitness(problem, best_individual["solution"])
    best_individual["solution"].printDesign(problem)
