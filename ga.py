import random
from individual import Individual

from problem_definition import ProblemDefinition


class GeneticAlgorithm:
    def __init__(self, problem, mut_rate):
        self.problem = problem
        self.offspringSise = 5
        self.mutationRate = mut_rate

    def mutationAddLane(self, ind, trackIds, chanceToStop=0.1):

        metersThreshold = self.problem.budgetUpdate * 1000.0 - ind.getRegularInsertedKMeters() * 1000.0 - ind.getNewInsertedKMeters() * 1000 # threshold of change to be designed
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

        metersThreshold = self.problem.budgetUpdate * 1000.0 - ind.getRegularInsertedKMeters() * 1000.0 - ind.getNewInsertedKMeters() * 1000# threshold of change to be designed
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
            # random selection of a node source
            aleatoryNodeSource = str(random.randint(1, len(individual.problem.nodes)))
            nodeSourceLong = individual.problem.nodes[aleatoryNodeSource]['long']
            nodeSourceLat = individual.problem.nodes[aleatoryNodeSource]['lat']

            # random selection of a node target
            aleatoryNodeTarget = str(random.randint(1, len(individual.problem.nodes)))
            while aleatoryNodeSource == aleatoryNodeTarget:
                aleatoryNodeTarget = str(random.randint(1, len(individual.problem.nodes)))
            nodeTargetLong = individual.problem.nodes[aleatoryNodeTarget]['long']
            nodeTargetLat = individual.problem.nodes[aleatoryNodeTarget]['lat']

            # random selection of a track id
            aleatoryTrackId = str(random.randint(1, 1000))

            # random number for the option
            randomNumber = random.randint(1, 3)

            distance = individual.problem.haversine(nodeSourceLong, nodeSourceLat, nodeTargetLong, nodeTargetLat)

            if randomNumber == 1:
                individual.insertAdditionalTrack(aleatoryNodeSource, aleatoryNodeTarget, distance, 1,
                                                 self.problem.maxSpeed)
            elif randomNumber == 2:
                individual.setLaneValue(aleatoryTrackId, random.randint(1, 5))
            else:
                individual.removeAdditionalTrack(aleatoryNodeSource, aleatoryNodeTarget, aleatoryTrackId)
            count -= 1

        return individual
