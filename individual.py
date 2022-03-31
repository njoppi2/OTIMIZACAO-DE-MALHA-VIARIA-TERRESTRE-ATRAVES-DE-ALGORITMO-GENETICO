import osmnx as ox
from user_model import UMSalmanAlaswad_I
import random
import networkx as nx
import matplotlib.pyplot as pyplot
import utm

#reads the problem (a city graph) and creates new attributes/functions useful for a genetic algorithm
class Individual:

    def __init__(self, problem):

        self.userModel = UMSalmanAlaswad_I(problem)
        self.problem = problem
        self.fitness = None
        self.vehiclesByRoad = None
        # variable ↓ for crossover
        # for the tracks with new number of lanes
        self.newLanes = {}
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

    #return the Inserted Km in new tracks
    def getNewInsertedKMeters(self):
        return self.newInsertedKMeters

    #return the inserted km in regular tracks
    def getRegularInsertedKMeters(self):
        return self.regularInsertedKMeters

    # method for crossover
    def getModifications(self):
        return {
            "newTracks": self.newTracks,
            "newLanes": self.newLanes
        }

    # method for crossover
    # each modification has a 50% of being returned
    def getRandomModifications(self):
        modifications = self.getModifications()

        randomNewTracks = self.getAleatoryNewTracksModifications(modifications["newTracks"])
        randomNewLanes = self.getAleatoryNewLanesModifications(modifications["newLanes"])

        return {
            "newTracks": randomNewTracks,
            "newLanes": randomNewLanes
        }

    def getAleatoryNewTracksModifications(self, modifications):
        randomNewTracks = modifications.copy()
        for i in range(len(modifications)):
            randomKeyForNewTracks = random.choice(list(randomNewTracks.keys()))
            if random.random() < 0.5:
                randomNewTracks.pop(randomKeyForNewTracks)
        return randomNewTracks

    def getAleatoryNewLanesModifications(self, modifications):
        randomNewLanes = modifications.copy()
        for i in range(len(modifications)):
            randomKeyForNewLanes = random.choice(list(randomNewLanes.keys()))
            if random.random() < 0.5:
                randomNewLanes.pop(randomKeyForNewLanes)
        return randomNewLanes

    # method for crossover
    def setModifications(self, fatherModifications, motherModifications):
        newTracks = {**fatherModifications["newTracks"], **motherModifications["newTracks"]}
        newLanes = {**fatherModifications["newLanes"], **motherModifications["newLanes"]}

        for source in newTracks.keys():
            for target in newTracks[source].keys():
                for track in newTracks[source][target]:
                    self.insertAdditionalTrack(track["s"], track["t"], track["distance"], track["lanes"], track["maxspeed"])

        for tid, newNoLanes in newLanes.items():
            self.setLaneValue(tid, newNoLanes)

        self.resetFitness()
    
    # set the number of lanes adapted in a track
    def setLaneValue(self, tid, newNoLanes):
        i = int(tid)
        if self.tracks[tid] > 0:
            self.regularInsertedKMeters -= self.tracks[tid] * self.problem.tracks[i]["distance"] / 1000.0
        if self.tracks[tid] < 0:
            self.regularRemovedKMeters -= self.tracks[tid] * self.problem.tracks[i]["distance"] / 1000.0
        self.tracks[tid] = newNoLanes
        self.newLanes[tid] = newNoLanes
        if newNoLanes > 0:
            self.regularInsertedKMeters += newNoLanes * self.problem.tracks[i]["distance"] / 1000.0
        if newNoLanes < 0:
            self.regularRemovedKMeters += newNoLanes * self.problem.tracks[i]["distance"] / 1000.0

        self.resetFitness()

    #return the fitness metric
    def calculateFitness(self):
        self.fitness = self.userModel.fitness(self)
        return self.fitness

    def resetFitness(self):
        self.fitness = None

    # insert a new nonregular track between two nodes
    def insertAdditionalTrack(self, source, target, distance, lanes, maxspeed):
        metersThreshold = self.problem.budgetUpdate * 1000.0 - self.getRegularInsertedKMeters() * 1000.0 - self.getNewInsertedKMeters() * 1000 # threshold of change to be designed

        if metersThreshold >= distance:
            if source not in self.newTracks:
                self.newTracks[source] = {}
            if target not in self.newTracks[source]:
                self.newTracks[source][target] = []
            self.nextTracksId += 1
            tt = distance / 1000.0 * (1 / maxspeed)
            normalized_tt = self.problem.normalize_tt(tt)
            self.newTracks[source][target].append(
                {"id": "nt_" + str(self.nextTracksId), "s": source, "t": target, "distance": distance, "lanes": lanes,
                 "maxspeed": maxspeed, "normalized_tt": normalized_tt, "tt": tt})
            self.newInsertedKMeters += lanes * distance / 1000.0
            self.resetFitness()

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
        self.resetFitness()

        return True

    def printDesign(self, dirName=None, outputFormat=None, plot=False):
        edgeColors = []
        for track in self.problem.tracks:  # regular tracks
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
        for node in self.problem.nodes:
            graph.add_node(str(self.problem.nodes[node]["id"]))

        # arcs
        for track in self.problem.tracks:  # regular tracks
            if (track["lanes"] + self.tracks[track["id"]]) == 0: continue
            graph.add_edge(track["s"], track["t"])
        for s in self.newTracks:  # non-regular tracks
            for t in self.newTracks[s]:
                for track in self.newTracks[s][t]:
                    graph.add_edge(s, t)

        nodePos = {}
        # for node in nodes:
        for (node, data) in graph.nodes(data=True):
            if node not in self.problem.nodes: continue
            l = utm.from_latlon(self.problem.nodes[node]["lat"], self.problem.nodes[node]["long"])
            x, y = l[0], l[1]
            nodePos[node] = [x, y]

        # remove new nodes 
        nodosGraph = []

        for i in graph.nodes:
            if i not in nodePos:
                nodosGraph.append(i)

        for j in nodosGraph:
            graph.remove_node(j)

        # labeling arcs
        edgeLabels = {}
        for tid in self.tracks:  # regular
            i = int(tid)
            # don't show labels from new nodes
            if i not in nodosGraph:
                lanes = self.tracks[tid]
                if lanes > 0:
                    edgeLabels[(self.problem.tracks[i]["s"], self.problem.tracks[i]["t"])] = "+" + str(lanes)
                if lanes < 0:
                    edgeLabels[(self.problem.tracks[i]["s"], self.problem.tracks[i]["t"])] = str(lanes)
        for s in self.newTracks:  # non-regular tracks
            for t in self.newTracks[s]:
                # dont show tracks from or to new nodes
                if s not in nodosGraph and t not in nodosGraph:
                    for track in self.newTracks[s][t]:
                        edgeLabels[(s, t)] = "New: (" + str(round(track["distance"]/1000, 2)) + "km, " + str(
                            track["maxspeed"]) + "km/h) x " + str(track["lanes"]) + "."

        # nx.draw_networkx(graph, pos=nodePos,  arrows=True, arrowstyle='-|>', with_labels=False, node_size=0, edge_color=edgeColors)
        nx.draw(graph, pos=nodePos, arrows=True, arrowstyle='-|>', with_labels=False, node_size=0,
                edge_color=edgeColors)
        nx.draw_networkx_edge_labels(graph, pos=nodePos, edge_labels=edgeLabels, font_color='black')
        if outputFormat != None:
            pyplot.savefig(dirName + "." + str(outputFormat), format=outputFormat)

        if dirName:
            pyplot.savefig(dirName+"/best_individual.png", format="PNG")
            # pyplot.savefig(outputFilename+".pdf", format="PDF")

        if plot:
            pyplot.show()

        pyplot.clf()

