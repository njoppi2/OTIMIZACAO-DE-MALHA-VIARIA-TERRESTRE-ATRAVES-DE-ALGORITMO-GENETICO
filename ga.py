import osmnx as ox
import networkx as nx
import matplotlib.pyplot as pyplot
import utm
import random

from problem_definition import ProblemDefinition
from user_model import UMSalmanAlaswad_I


#reads the problem (a city graph) and creates new attributes/functions useful for a genetic algorithm
class Individual:

    def __init__(self, problem):
        self.fitness = None
        self.vehiclesByRoad = None
        self.tracks = {}  # positive or negative number of adapted lanes
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
    def getTracksSize(self):
        return len(self.tracks)

    #return the next track id
    def getNextTracksId(self):
        return self.nextTracksId

  # return the number of adaptation on a track
    def getLaneValue(self, tid):
        return self.tracks[tid]

    # set the number of lanes adapted in a track
    def setLaneValue(self, problem, tid, newNoLanes):
        i = int(tid)
        if self.tracks[tid] > 0:
            self.regularInsertedKMeters -= self.tracks[tid] * problem.tracks[i]["distance"] / 1000.0
        if self.tracks[tid] < 0:
            self.regularRemovedKMeters -= self.tracks[tid] * problem.tracks[i]["distance"] / 1000.0
        self.tracks[tid] = newNoLanes
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
            if node not in problem.nodes: continue
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
            ind.setLaneValue(self.problem, str(trackId), +1)

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
            if nodeStart not in problem.adjLst: break
            while len(list(problem.adjLst[nodeStart])) == 1:
                if nodeStart != lastNode:
                    track = problem.adjLst[nodeStart][lastNode][0]
                    metersReached += track["distance"]
                    trackId = int(track["id"])
                    trackList.append(trackId)
                    lastNode = nodeStart
                    if nodeStart in problem.adjLstInv:
                        nodeStart = next(iter(problem.adjLstInv[nodeStart]))
                else: break

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
            aleatoryTrackSource = str(random.randint(1, len(individual.tracks)))

            # random selection of a track target
            aleatoryTrackTarget = str(random.randint(1, len(individual.tracks)))

            # random selection of a track id
            aleatoryTrackId = str(random.randint(1, 1000))

            # random number for the option
            randomNumber = random.randint(1, 3)
            if randomNumber == 1:
                individual.insertAdditionalTrack(problem, aleatoryTrackSource, aleatoryTrackTarget, 1500000, 1,
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
    TOTAL_NUMBER_OF_GENERATIONS = 100
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
    generation_individuals = ga.createInitialPopulation(TOTAL_NUMBER_OF_INDIVIDUALS, problem)

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

        previous_fitness_sum = 0

        # find winner individual
        for i in range(TOTAL_NUMBER_OF_INDIVIDUALS):

            individual_fitness = fitness_list[i]
            previous_fitness_sum += individual_fitness
            if previous_fitness_sum > random_number:
                return generation_individuals[i]
        pass

    # runs the genetic algorithm on the number of generations specified
    for gen in range(TOTAL_NUMBER_OF_GENERATIONS):

        # fills the fitness_list and calculates total_fitness_sum
        for i in range(TOTAL_NUMBER_OF_INDIVIDUALS):

            individual = generation_individuals[i]
            # individual_fitness = userModel.fitness(individual)
            individual_fitness = random.randint(0, 100)
            fitness_list.append(individual_fitness)
            total_fitness_sum += fitness_list[i]

            # updates the best fitness found
            if individual_fitness > best_individual["fitness"]:
                best_individual["fitness"] = individual_fitness
                best_individual["solution"] = individual

        # selection / create selected_parents list
        for i in range(TOTAL_NUMBER_OF_INDIVIDUALS):

            father = draw_individual()
            mother = draw_individual()

            while mother == father:
                mother = draw_individual()

            selected_parents.append({
                "father": father,
                "mother": mother
            })

        # mate parents to create new generation
        for i in range(TOTAL_NUMBER_OF_INDIVIDUALS):
            generation_individuals[i] = mate(**selected_parents[i])

    print("fitness: ", best_individual["fitness"])

    print("regularInsertedKMeters: ", best_individual["solution"].regularInsertedKMeters)
    print("newInsertedKMeters: ", best_individual["solution"].newInsertedKMeters)
    print("fitness: ", best_individual["solution"].fitness)

    userModel.fitness(problem, best_individual["solution"])
    best_individual["solution"].printDesign(problem)
