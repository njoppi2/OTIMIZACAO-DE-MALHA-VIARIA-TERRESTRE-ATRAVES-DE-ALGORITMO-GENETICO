import osmnx as ox
import networkx as nx
import matplotlib.pyplot as pyplot
import utm
import random

from problem_definition import ProblemDefinition
from user_model import UMSalmanAlaswad_I


#reads the problem (a city graph) and creates new useful attributes/functions for a genetic algorithm
class Individual:

    def __init__(self, problem):
        self.fitness = None
        self.vehiclesByRoad = None
        self.tracks = {}  # positive or negative number of adapted lanes
        # for the tracks with new number of lanes
        self.newLanes = {}
        self.newTracks = {}
        # for preexisting tracks
        self.regularInsertedKMeters = 0
        self.regularRemovedKMeters = 0
        # for new tracks
        self.newInsertedKMeters = 0
        # id for new tracks
        self.nextTracksId = 0
        # no influences on the number of lanes for each track
        for track in problem.tracks:
            self.tracks[track["id"]] = 0


    #Funções gets faltantes
    #return the fitness metric
    def getFitnestracks(self):
        return self.fitness

    #return the vehicles by roads
    def getVehiclesByRoad(self):
        return self.vehiclesByRoad

    #return the Inserted Km in new tracks
    def getNewInsertedKMeters(self):
        return self.newInsertedKMeters

    #return the number of the new tracks
    def getNewTracksSize(self):
        return len(self.newTracks)

    #return the number of adapted tracks
    def getTracksSize(self): #returns total number of tracks
        return len(self.tracks)

    #return the next track id
    def getNextTracksId(self):
        return self.nextTracksId

  # return the number of adaptation on a track
    def getLaneValue(self, tid):
        return self.tracks[tid]

    def getModifications(self):
        return {
            "newTracks": self.newTracks,
            "newLanes": self.newLanes
        }

    # each modification has a 50% of being returned
    def getRandomModifications(self):
        modifications = self.getModifications()

        randomNewTracks = dict(filter(lambda _: random.random() > 0.5, modifications["newTracks"]))
        randomNewLanes = dict(filter(lambda _: random.random() > 0.5, modifications["newLanes"]))
        
        return {
            "newTracks": randomNewTracks,
            "newLanes": randomNewLanes
        }

    def setModifications(self, problem, fatherModifications, motherModifications):
        newTracks = fatherModifications["newTracks"] + motherModifications["newTracks"]
        newLanes = fatherModifications["newLanes"] + motherModifications["newLanes"]
        
        for source in newTracks.keys():
            for target in newTracks[source].keys():
                for track in newTracks[source][target]:
                    self.insertAdditionalTrack(problem, track["s"], track["t"], track["distance"], track["lanes"], track["maxspeed"])

        for tid, newNoLanes in newLanes.items():
            self.setLaneValue(problem, tid, newNoLanes)

    # set the number of lanes adapted in a track
    def setLaneValue(self, problem, tid, newNoLanes):
        i = int(tid)
        if self.tracks[tid] > 0:
            self.regularInsertedKMeters -= self.tracks[tid] * problem.tracks[i]["distance"] / 1000.0
        if self.tracks[tid] < 0:
            self.regularRemovedKMeters -= self.tracks[tid] * problem.tracks[i]["distance"] / 1000.0
        self.tracks[tid] = newNoLanes
        self.newLanes[tid] = newNoLanes
        if newNoLanes > 0:
            self.regularInsertedKMeters += newNoLanes * problem.tracks[i]["distance"] / 1000.0
        if newNoLanes < 0:
            self.regularRemovedKMeters += newNoLanes * problem.tracks[i]["distance"] / 1000.0

    # insert a new nonregular track between two nodes
    def insertAdditionalTrack(self, problem, source, target, distance, lanes, maxspeed):
        if source not in self.newTracks:
            self.newTracks[source] = {}
        if target not in self.newTracks[source]:
            self.newTracks[source][target] = []
        self.nextTracksId += 1
        tt = (distance / 1000.0 * (1 / maxspeed)) / problem.minTT
        self.newTracks[source][target].append(
            {"id": "nt_" + str(self.nextTracksId), "s": source, "t": target, "distance": distance, "lanes": lanes,
             "maxspeed": maxspeed, "tt": tt})
        self.newInsertedKMeters += lanes * distance / 1000.0

    # remove a new nonregular track between two nodes
    def removeAdditionalTrack(self, source, target, tid):
        if source not in self.newTracks:
            return False
        if target not in self.newTracks[source]:
            return False
        trackR = None
        for track in self.newTracks[source][target]:
            if track["id"] == tid:
                trackR = track

        if trackR == None:
            return False

        self.newInsertedKMeters -= trackR["lanes"] * trackR["distance"]
        self.newTracks[source][target].remove(trackR)

        return True

    def printDesign(self, problem, outputFilename="output", outputFormat=None):
        edgeColors = []
        for track in problem.tracks:  # regular tracks
            if (track["lanes"] + self.tracks[track["id"]]) == 0: continue
            color = ""
            if self.vehiclesByRoad[track["id"]] <= 7 * (track["distance"] / 1000.0) * (
                    track["lanes"] + self.tracks[track["id"]]):
                color = "green"
            elif self.vehiclesByRoad[track["id"]] <= 11 * (track["distance"] / 1000.0) * (
                    track["lanes"] + self.tracks[track["id"]]):
                color = "yellow"
            elif self.vehiclesByRoad[track["id"]] <= 22 * (track["distance"] / 1000.0) * (
                    track["lanes"] + self.tracks[track["id"]]):
                color = "orange"
            elif self.vehiclesByRoad[track["id"]] <= 28 * (track["distance"] / 1000.0) * (
                    track["lanes"] + self.tracks[track["id"]]):
                color = "purple"
            else:
                color = "red"
            edgeColors.append(color)
        for s in self.newTracks:  # non-regular tracks
            for t in self.newTracks[s]:
                for track in self.newTracks[s][t]:
                    if track["lanes"] == 0: continue
                    color = ""
                    if self.vehiclesByRoad[track["id"]] <= 7 * (track["distance"] / 1000.0) * (track["lanes"]):
                        color = "green"
                    elif self.vehiclesByRoad[track["id"]] <= 11 * (track["distance"] / 1000.0) * (track["lanes"]):
                        color = "yellow"
                    elif self.vehiclesByRoad[track["id"]] <= 22 * (track["distance"] / 1000.0) * (track["lanes"]):
                        color = "orange"
                    elif self.vehiclesByRoad[track["id"]] <= 28 * (track["distance"] / 1000.0) * (track["lanes"]):
                        color = "purple"
                    else:
                        color = "red"
                    edgeColors.append(color)

        # creating graph for presentation
        graph = nx.MultiDiGraph()

        i = 0
        for node in problem.nodes:
            graph.add_node(str(problem.nodes[node]["id"]))

        # arcs
        for track in problem.tracks:  # regular tracks
            if (track["lanes"] + self.tracks[track["id"]]) == 0: continue
            graph.add_edge(track["s"], track["t"])
        for s in self.newTracks:  # non-regular tracks
            for t in self.newTracks[s]:
                for track in self.newTracks[s][t]:
                    graph.add_edge(s, t)

        nodePos = {}
        # for node in nodes:
        for (node, data) in graph.nodes(data=True):
            l = utm.from_latlon(problem.nodes[node]["lat"], problem.nodes[node]["long"])
            x, y = l[0], l[1]
            nodePos[node] = [x, y]

        # labeling arcs
        edgeLabels = {}
        for tid in self.tracks:  # regular
            i = int(tid)
            lanes = self.tracks[tid]
            if lanes > 0:
                edgeLabels[(problem.tracks[i]["s"], problem.tracks[i]["t"])] = "+" + str(lanes)
            if lanes < 0:
                edgeLabels[(problem.tracks[i]["s"], problem.tracks[i]["t"])] = str(lanes)
        for s in self.newTracks:  # non-regular tracks
            for t in self.newTracks[s]:
                for track in self.newTracks[s][t]:
                    edgeLabels[(s, t)] = "New: (" + str(track["distance"]) + "m, " + str(
                        track["maxspeed"]) + "km/h) x " + str(track["lanes"]) + "."

        # nx.draw_networkx(graph, pos=nodePos,  arrows=True, arrowstyle='-|>', with_labels=False, node_size=0, edge_color=edgeColors)
        nx.draw(graph, pos=nodePos, arrows=True, arrowstyle='-|>', with_labels=False, node_size=0,
                edge_color=edgeColors)
        nx.draw_networkx_edge_labels(graph, pos=nodePos, edge_labels=edgeLabels, font_color='black')
        if outputFormat != None:
            pyplot.savefig(outputFilename + "." + str(outputFormat), format=outputFormat)
        # pyplot.savefig(outputFilename+".png", format="PNG")
        # pyplot.savefig(outputFilename+".pdf", format="PDF")
        pyplot.show()



class GeneticAlgorithm:
    def __init__(self, problem):
        self.problem = problem
        self.generationSize = 10
        self.offspringSise = 5
        self.mutationRate = 0.1

    #def criapopulacao

    #def crianovoindividuoaleatorio

    def run(self):
        return None

    def crossover(self, ind1, ind2):
        return None

    def mutation(self, ind):
        return None

    def mutationAddLane(self, ind, chanceToStop=0.1):

        metersThreshold = self.problem.budgetUpdate * 1000.0 - ind.regularInsertedKMeters * 1000.0  # threshold of change to be designed
        metersReached = 0  # meters chaged

        # select a random node
        trackId = random.randint(0, len(self.problem.tracks) - 1)
        track = self.problem.tracks[trackId]
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
            ind.setLaneValue(self.problem, str(trackId), +1)

    def mutationAddLaneOnRoad(self, ind):

        metersThreshold = self.problem.budgetUpdate * 1000.0 - ind.regularInsertedKMeters * 1000.0  # threshold of change to be designed
        metersReached = 0  # meters chaged

        trackList = []

        # repeat until find a road with more than one track
        while len(trackList) <= 1:
            trackList = []

            # select a random node
            trackId = random.randint(0, len(self.problem.tracks) - 1)
            track = self.problem.tracks[trackId]
            metersReached = 0

            # finding the road starting node
            nodeStart = track["s"]
            lastNode = track["t"]
            if nodeStart not in problem.adjLst: break
            while len(list(problem.adjLst[nodeStart])) == 1:
                track = problem.adjLst[nodeStart][lastNode][0]
                metersReached += track["distance"]
                trackId = int(track["id"])
                trackList.append(trackId)
                lastNode = nodeStart
                if nodeStart in problem.adjLstInv:
                    nodeStart = next(iter(problem.adjLstInv[nodeStart]))

            # finding the road last node

            lastNode = track["t"]
            if lastNode not in problem.adjLst: break
            while len(list(problem.adjLst[lastNode])) == 1:
                nextNode = next(iter(problem.adjLst[lastNode]))
                track = problem.adjLst[lastNode][nextNode][0]
                metersReached += track["distance"]
                trackId = int(track["id"])
                trackList.append(trackId)
                lastNode = nextNode
                if lastNode not in problem.adjLst: break

        if metersReached < metersThreshold:
            # updating new lanes
            print(trackList)
            for trackId in trackList:
                ind.setLaneValue(self.problem, str(trackId), +1)

    def fitness(self, ind):
        return None

    def createInitialPopulation(self, size, initialProblem):
        initialPopulation = list()
        count = 0
        while count < size:
            initialPopulation.append(self.createNewRadomIndividual(initialProblem))
            count += 1
        return initialPopulation

    def createNewRadomIndividual(self, initialProblem):
        # create the individual
        individual = Individual(initialProblem)

        # number of the iterations
        count = random.randint(1, 100)

        while count > 0:
            # random selection of a track source
            aleatoryTrackSource = individual.tracks[str(random.randint(1, len(individual.tracks) - 1))]

            # random selection of a track target
            aleatoryTrackTarget = individual.tracks[str(aleatoryTrackSource)]

            # random selection of a track id
            aleatoryTrackId = str(random.randint(1, 1000))

            # random number for the option
            randomNumber = random.randint(1, 3)
            if randomNumber == 1:
                individual.insertAdditionalTrack(problem, aleatoryTrackSource, aleatoryTrackTarget, 10, 1,
                                                 problem.maxSpeed)
            elif randomNumber == 2:
                individual.setLaneValue(initialProblem, aleatoryTrackId, random.randint(1, 5))
            else:
                individual.removeAdditionalTrack(aleatoryTrackSource, aleatoryTrackTarget, aleatoryTrackId)
            count -= 1
        return individual

def run_genetic_algorithm(place_name):

    global problem

    TOTAL_NUMBER_OF_INDIVIDUALS = 20
    TOTAL_NUMBER_OF_ELITE_INDIVIDUALS = 2
    TOTAL_NUMBER_OF_RANDOM_INDIVIDUALS = int(TOTAL_NUMBER_OF_INDIVIDUALS / 2)
    TOTAL_NUMBER_OF_MATED_INDIVIDUALS = TOTAL_NUMBER_OF_INDIVIDUALS - TOTAL_NUMBER_OF_ELITE_INDIVIDUALS - TOTAL_NUMBER_OF_RANDOM_INDIVIDUALS
    TOTAL_NUMBER_OF_GENERATIONS = 2
    problem = ProblemDefinition(place_name + ".net")
    ga = GeneticAlgorithm(problem)
    userModel = UMSalmanAlaswad_I()
    fitness_list = []
    selected_parents = []
    total_fitness_sum = 0
    best_individual = {
        "fitness": 0,
        "solution": None
    }
    current_generation_individuals = ga.createInitialPopulation(TOTAL_NUMBER_OF_INDIVIDUALS, problem)
    new_generation_individuals = []

    #receives two Individuals, does crossover, mutation, and returns a new Individual
    def mate(father, mother):
        # do crossover

        fatherModifications = father.getRandomModifications()
        motherModifications = mother.getRandomModifications()

        child = Individual(problem)

        child.setModifications(problem, fatherModifications, motherModifications)

        mutation(child)

        # return new individual ↓
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

    def draw_individual():
        random_number = random.randint(0, total_fitness_sum)

        #stores the sum of the population fitness until the current individual
        previous_fitness_sum = 0

        # find winner individual
        for i in range(TOTAL_NUMBER_OF_INDIVIDUALS):

            individual_fitness = fitness_list[i]["fitness"]
            previous_fitness_sum += individual_fitness
            if previous_fitness_sum > random_number:
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
        print("generation_individuals after mated ones: ", str(len(new_generation_individuals)))


        # add elite individuals to generation_individuals
        for i in range(TOTAL_NUMBER_OF_ELITE_INDIVIDUALS):
            new_generation_individuals.append(sorted_fitness_list[i]["solution"])
        print("generation_individuals after elite ones: ", str(len(new_generation_individuals)))


        # add random_individuals to generation_individuals
        new_generation_individuals.extend(ga.createInitialPopulation(TOTAL_NUMBER_OF_RANDOM_INDIVIDUALS, problem))
        print("generation_individuals after random: ", str(len(new_generation_individuals)))

        #updates the current_population
        current_generation_individuals = new_generation_individuals
        new_generation_individuals = []
        print("generation: " + str(gen))

    # print("fitness: ", best_individual["fitness"])

    # print(best_individual["solution"].regularInsertedKMeters)
    # print("newInsertedKMeters: ", best_individual["solution"].newInsertedKMeters)
    # print("fitness: ", best_individual["solution"].fitness)

    # ga.mutationAddLane(best_individual)
    ga.mutationAddLaneOnRoad(best_individual["solution"])
    userModel.fitness(problem, best_individual["solution"])

    best_individual["solution"].printDesign(problem)


# adaptation of a single individual
    # maior = 0
    # maiorId = None
    # maiorT = None
    # for i in range(len(problem.tracks)):
    #    track = problem.tracks[i]
    #    maiorId
    #    if track["distance"] > maior:
    #     maior = track["distance"]
    #     maiorT = track
    #     maiorId = i
    # print(maiorT)
    # print(maiorId)
    # exit(0)
    # {'s': '2918', 't': '2919', 'distance': 1006.5518963592865, 'oneway': 'yes', 'lanes': 1, 'id': '3188', 'tt': 26.852742937962635}
    # x.setLaneValue(problem, '3188',10)
    # x.insertAdditionalTrack(problem, '2918', '5133', 5000, 2, 50)
    # x.insertAdditionalTrack(problem, '5133', '2918', 5000, 2, 50)

# print(y.regularInsertedKMeters)
# print(y.newInsertedKMeters)
# print(y.fitness)
# print(x.vehiclesByRoad)
# y = Individual(problem)
# userModel.fitness(problem, y)