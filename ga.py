import osmnx as ox
import networkx as nx
import copy
import matplotlib.pyplot as pyplot
import utm
import random

from math import radians, cos, sin, asin, sqrt

from translator import roads, road


class Utils:
    # returns zero from when dividing by zero
    def IndetZero(value, divisor):
        if divisor != 0:
            return value / divisor
        else:
            return 0


# reads the .net file from load_place.py and turns it into a graph
class ProblemDefinition:

    def __init__(self, inputFile):

        self.maxSpeed = 50  # in km/h
        self.nodes = None
        self.tracks = None
        self.adjLst = None
        self.adjLstInv = None
        self.minTT = None
        self.budgetUpdate = 10  # in km
        self.budgetAddition = 10  # in km

        self.nodes = {}
        self.tracks = []

        osmNetFile = open(inputFile, 'r')
        lines = osmNetFile.readlines()

        arcsPhase = False
        roadId = 0
        for line in lines:
            if line[0:4] == '*arc':
                arcsPhase = True
                continue
            data = line.split(' ')
            data[-1] = data[-1].replace('\n', '')
            if not arcsPhase:
                # node phase
                # 1 90199676 -48.54448 -27.6634265 ellipse
                if len(data) < 4: continue
                nodeId = data[0]
                nodeLong = float(data[2])
                nodeLat = float(data[3])
                word = ""
                for i in range(5, len(data)):
                    sub = data[i]
                    word += str(sub) + " "
                self.nodes[nodeId] = {"id": int(nodeId), "lat": nodeLat, "long": nodeLong, "properties": word.strip()}
            else:
                # arc phase
                # 9 9499 1.0 lanes 3 highway trunk name "Rodovia Governador Aderbal Ramos da Silva" maxspeed 80 ref SC-401 oneway yes
                s = data[0]
                t = data[1]
                distance = max(0.1, self.haversine(self.nodes[s]["long"], self.nodes[s]["lat"], self.nodes[t]["long"],
                                                   self.nodes[t]["lat"]))
                # arc metadata
                arc = {"s": s, "t": t, "distance": distance}
                for i in range(2, len(data)):
                    word = data[i]
                    if word == "oneway":
                        arc["oneway"] = data[i + 1]
                    if word == "lanes":
                        arc["lanes"] = int(data[i + 1])
                    if word == "maxspeed":
                        arc["maxspeed"] = int(data[i + 1])
                    if word == "ref":
                        if data[i + 1][0] == "\"":
                            name = ""
                            c = 0
                            for subw in data[i + 1:]:
                                c += 1
                                name += subw.replace("\"", "") + " "
                                if subw[-1] == "\"":
                                    break
                            arc["ref"] = name.strip()
                            i += c - 1
                            continue
                        else:
                            arc["ref"] = data[i + 1]
                    if word == "name":
                        name = ""
                        c = 0
                        for subw in data[i + 1:]:
                            c += 1
                            name += subw.replace("\"", "") + " "
                            if subw[-1] == "\"":
                                break
                        arc["name"] = name.strip()
                        i += c - 1
                        continue
                if "oneway" not in arc:
                    arc["oneway"] = "yes"
                if "lanes" not in arc:
                    arc["lanes"] = 1

                if arc["lanes"] > 1 and arc["oneway"] == "no":
                    arc["lanes"] = max(1, int(arc["lanes"] // 2))
                    arc2 = copy.deepcopy(arc)
                    arc2["s"] = arc["t"]
                    arc2["t"] = arc["s"]

                    arc2["id"] = str(roadId)
                    roadId += 1
                    self.tracks.append(arc2)

                arc["id"] = str(roadId)
                roadId += 1
                self.tracks.append(arc)

        # adjacent list
        self.adjLst = {}
        for road in self.tracks:
            s = road["s"]
            t = road["t"]
            if s not in self.adjLst:
                self.adjLst[s] = {}
            if t not in self.adjLst[s]:
                self.adjLst[s][t] = []
            self.adjLst[s][t].append(road)

        # adjacent list inverted
        self.adjLstInv = {}
        for road in self.tracks:
            s = road["s"]
            t = road["t"]
            if t not in self.adjLstInv:
                self.adjLstInv[t] = {}
            if s not in self.adjLstInv[t]:
                self.adjLstInv[t][s] = []
            self.adjLstInv[t][s].append(road)

        # normalizing travel time (tt_i)
        self.minTT = float("+inf")
        for road in self.tracks:
            speed = self.maxSpeed  # kmh
            if "maxspeed" in road:
                speed = road["maxspeed"]
            if self.minTT > road["distance"]:
                self.minTT = road["distance"] / 1000.0 * (1 / speed)
        for i in range(len(self.tracks)):
            road = self.tracks[i]
            speed = self.maxSpeed  # kmh
            if "maxspeed" in road:
                speed = road["maxspeed"]
            self.tracks[i]["tt"] = (self.tracks[i]["distance"] / 1000.0 * (1 / speed)) / self.minTT

    def haversine(self, lon1, lat1, lon2, lat2):
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        # haversine formula 
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        # Radius of earth in kilometers is 6371
        km = 6371 * c
        return km * 1000.0  # in meters


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


class UserModel:
    def fitness(self):
        return float("inf")


class UMSalmanAlaswad_I(UserModel):

    def __init__(self):
        self.vehiclesByRoad = 7

    def fitness(self, problem, individual):
        individual.vehiclesByRoad = {}

        # Is it required to renormalize travel time? (tt_i)
        minTT = problem.minTT
        nminTT = minTT

        for source in individual.newTracks:
            for target in individual.newTracks[source]:
                for track in individual.newTracks[source][target]:
                    speed = problem.maxSpeed  # kmh
                    if "maxspeed" in track:
                        speed = track["maxspeed"]
                    if nminTT > track["distance"]:
                        nminTT = track["distance"] / 1000.0 * (1 / speed)
        if minTT > nminTT:
            # update travel time information in problem instance / newroads
            for i in range(len(problem.tracks)):
                if "maxspeed" in problem.tracks[i]:
                    speed = track["maxspeed"]
                roads[i]["tt"] = (road["distance"] / 1000.0 * (1 / speed)) / nminTT
            for source in individual.newTracks:
                for target in individual.newTracks[source]:
                    for i in range(len(individual.newTracks[source][target])):
                        speed = problem.maxSpeed  # kmh
                        if "maxspeed" in individual.newTracks[source][target][i]:
                            speed = track["maxspeed"]
                        individual.newTracks[source][target][i]["tt"] = (individual.newTracks[source][target][i][
                                                                             "distance"] / 1000.0 * (
                                                                                     1 / speed)) / nminTT

        # calculating pmatriz
        pMatrix = {}
        for track in problem.tracks:  # pmatrix for regular tracks
            rid = track["id"]
            s = track["s"]
            t = track["t"]
            pMatrix[rid] = {}

            is_t_source_adjList = True
            is_t_source_adjIndividual = True

            if t not in problem.adjLst:
                is_t_source_adjList = False
            if t not in individual.newTracks:
                is_t_source_adjIndividual = False

            lanes = 0
            if is_t_source_adjList == True:
                for tl in problem.adjLst[t]:
                    for track2 in problem.adjLst[t][tl]:
                        speed = problem.maxSpeed  # kmh
                        if "maxspeed" in track2:
                            speed = track2["maxspeed"]
                        lanes += (track2["lanes"] + individual.tracks[track2["id"]]) * (1 / speed)

            if is_t_source_adjIndividual == True:
                for tl in individual.newTracks[t]:
                    for track2 in individual.newTracks[t][tl]:
                        speed = problem.maxSpeed  # kmh
                        if "maxspeed" in track2:
                            speed = track2["maxspeed"]
                        lanes += track2["lanes"] * (1 / speed)

            if is_t_source_adjList == True or is_t_source_adjIndividual == True:
                speed = problem.maxSpeed  # kmh
                if "maxspeed" in track:
                    speed = track["maxspeed"]
                if track["distance"] == 0.0:
                    pMatrix[rid][rid] = 0.0
                else:
                    pMatrix[rid][rid] = (track["tt"] - 1) / (track["tt"])

            if is_t_source_adjList == True:
                for tl in problem.adjLst[t]:
                    for track2 in problem.adjLst[t][tl]:
                        rid2 = track2["id"]
                        pMatrix[rid][rid2] = 0
                        speed = problem.maxSpeed  # km/h
                        if "maxspeed" in track2:
                            speed = track2["maxspeed"]
                        pMatrix[rid][rid2] += (1.0 - pMatrix[rid][rid]) * (
                                    ((track2["lanes"] + individual.tracks[track2["id"]]) * (1 / speed)) / (lanes))

            if is_t_source_adjIndividual == True:

                for tl in individual.newTracks[t]:
                    for track2 in individual.newTracks[t][tl]:
                        rid2 = track2["id"]
                        pMatrix[rid][rid2] = 0
                        speed = problem.maxSpeed  # km/h
                        if "maxspeed" in track2:
                            speed = track2["maxspeed"]
                        pMatrix[rid][rid2] += (1.0 - pMatrix[rid][rid]) * ((track2["lanes"] * (1 / speed)) / (lanes))

            if is_t_source_adjList == False and is_t_source_adjIndividual == False:
                pMatrix[rid][rid] = 1

        for s in individual.newTracks:
            for t in individual.newTracks[s]:  # pmatrix for non-regular tracks
                for track in individual.newTracks[s][t]:  # pmatrix for non-regular tracks
                    rid = track["id"]

                    pMatrix[rid] = {}

                    is_t_source_adjList = True
                    is_t_source_adjIndividual = True

                    if t not in problem.adjLst:
                        is_t_source_adjList = False
                    if t not in individual.newTracks:
                        is_t_source_adjIndividual = False

                    lanes = 0
                    if is_t_source_adjList == True:
                        for tl in problem.adjLst[t]:
                            for track2 in problem.adjLst[t][tl]:
                                speed = problem.maxSpeed  # kmh
                                if "maxspeed" in track2:
                                    speed = track2["maxspeed"]
                                lanes += (track2["lanes"] + individual.tracks[track2["id"]]) * (1 / speed)

                    if is_t_source_adjIndividual == True:
                        for tl in individual.newTracks[t]:
                            for track2 in individual.newTracks[t][tl]:
                                speed = problem.maxSpeed  # kmh
                                if "maxspeed" in track2:
                                    speed = track2["maxspeed"]
                                lanes += track2["lanes"] * (1 / speed)

                    if is_t_source_adjList == True or is_t_source_adjIndividual == True:
                        speed = problem.maxSpeed  # kmh
                        if "maxspeed" in track:
                            speed = track["maxspeed"]
                        if track["distance"] == 0.0:
                            pMatrix[rid][rid] = 0.0
                        else:
                            pMatrix[rid][rid] = (track["tt"] - 1) / (track["tt"])

                    if is_t_source_adjList == True:
                        for tl in problem.adjLst[t]:
                            for track2 in problem.adjLst[t][tl]:
                                rid2 = track2["id"]
                                pMatrix[rid][rid2] = 0
                                speed = problem.maxSpeed  # km/h
                                if "maxspeed" in track2:
                                    speed = track2["maxspeed"]
                                pMatrix[rid][rid2] += (1.0 - pMatrix[rid][rid]) * (
                                            ((track2["lanes"] + individual.tracks[track2["id"]]) * (1 / speed)) / (
                                        lanes))

                    if is_t_source_adjIndividual == True:
                        for tl in individual.newTracks[t]:
                            for track2 in individual.newTracks[t][tl]:
                                rid2 = track2["id"]
                                pMatrix[rid][rid2] = 0
                                speed = problem.maxSpeed  # km/h
                                if "maxspeed" in track2:
                                    speed = track2["maxspeed"]
                                pMatrix[rid][rid2] += (1.0 - pMatrix[rid][rid]) * (
                                            (track2["lanes"] * (1 / speed)) / (lanes))

                    if is_t_source_adjList == False and is_t_source_adjIndividual == False:
                        pMatrix[rid][rid] = 1

        # number of vehicles by track
        individual.vehiclesByRoad = {}
        for i in range(len(problem.tracks)):  # number of vehicles for regular tracks
            track = problem.tracks[i]
            rid = track["id"]
            s = track["s"]
            t = track["t"]
            if rid not in individual.vehiclesByRoad:
                individual.vehiclesByRoad[rid] = (self.vehiclesByRoad * (track["distance"] / 1000.0) * (
                            track["lanes"] + individual.tracks[rid])) * pMatrix[rid][rid]

            is_t_source_adjList = True
            is_t_source_adjIndividual = True

            if t not in problem.adjLst:
                is_t_source_adjList = False
            if t not in individual.newTracks:
                is_t_source_adjIndividual = False

            if is_t_source_adjList == True:
                for tl in problem.adjLst[t]:
                    for track2 in problem.adjLst[t][tl]:
                        rid2 = track2["id"]
                        if rid2 not in individual.vehiclesByRoad:
                            individual.vehiclesByRoad[rid2] = (self.vehiclesByRoad * (track2["distance"] / 1000.0) * (
                                        track2["lanes"] + individual.tracks[rid2])) * pMatrix[rid2][rid2]
                        individual.vehiclesByRoad[rid2] += pMatrix[rid][rid2] * (
                                    self.vehiclesByRoad * (track["distance"] / 1000.0) * (
                                        track["lanes"] + individual.tracks[rid]))
            if is_t_source_adjIndividual == True:
                for tl in individual.newTracks[t]:
                    for track2 in individual.newTracks[t][tl]:
                        rid2 = track2["id"]
                        if rid2 not in individual.vehiclesByRoad:
                            individual.vehiclesByRoad[rid2] = (self.vehiclesByRoad * (track2["distance"] / 1000.0) * (
                            track2["lanes"])) * pMatrix[rid2][rid2]
                        individual.vehiclesByRoad[rid2] += pMatrix[rid][rid2] * (
                                    self.vehiclesByRoad * (track["distance"] / 1000.0) * (
                                        track["lanes"] + individual.tracks[rid]))

        # for i in range(len(individual.newTracks)):
        for s in individual.newTracks:  # number of vehicles for non-regular tracks
            for t in individual.newTracks[s]:
                for track in individual.newTracks[s][t]:
                    rid = track["id"]

                    if rid not in individual.vehiclesByRoad:
                        individual.vehiclesByRoad[rid] = (self.vehiclesByRoad * (track["distance"] / 1000.0) * (
                        track["lanes"])) * pMatrix[rid][rid]

                    is_t_source_adjList = True
                    is_t_source_adjIndividual = True

                    if t not in problem.adjLst:
                        is_t_source_adjList = False
                    if t not in individual.newTracks:
                        is_t_source_adjIndividual = False

                    if is_t_source_adjList == True:
                        for tl in problem.adjLst[t]:
                            for track2 in problem.adjLst[t][tl]:
                                rid2 = track2["id"]
                                if rid2 not in individual.vehiclesByRoad:
                                    individual.vehiclesByRoad[rid2] = (self.vehiclesByRoad * (
                                                track2["distance"] / 1000.0) * (track2["lanes"] + individual.tracks[
                                        rid2])) * pMatrix[rid2][rid2]
                                individual.vehiclesByRoad[rid2] += pMatrix[rid][rid2] * (
                                            self.vehiclesByRoad * (track["distance"] / 1000.0) * (track["lanes"]))
                    if is_t_source_adjIndividual == True:
                        for tl in individual.newTracks[t]:
                            for track2 in individual.newTracks[t][tl]:
                                rid2 = track2["id"]
                                if rid2 not in individual.vehiclesByRoad:
                                    individual.vehiclesByRoad[rid2] = (self.vehiclesByRoad * (
                                                track2["distance"] / 1000.0) * (track2["lanes"])) * pMatrix[rid2][rid2]
                                individual.vehiclesByRoad[rid2] += pMatrix[rid][rid2] * (
                                            self.vehiclesByRoad * (track["distance"] / 1000.0) * (track["lanes"]))

        # fitnes value: average density
        densSum = 0.0
        densCount = 0
        for track in problem.tracks:  # regular tracks
            rid = track["id"]
            dens = Utils.IndetZero(individual.vehiclesByRoad[rid],
                                   ((track["distance"] / 1000.0) * (track["lanes"] + individual.tracks[rid])))
            densSum += dens
            densCount += 1
        for s in individual.newTracks:
            for t in individual.newTracks[s]:
                for track in individual.newTracks[s][t]:
                    rid = track["id"]
                    dens = Utils.IndetZero(individual.vehiclesByRoad[rid],
                                           ((track["distance"] / 1000.0) * (track["lanes"])))
                    densSum += dens
                    densCount += 1

        individual.fitness = densSum / densCount

        return individual.fitness


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
        trackId = random.randint(0, len(self.problem.tracks))
        track = self.problem.tracks[trackId]
        trackList = []
        metersReached += track["distance"]
        node = track["t"]
        while metersReached < metersThreshold:
            trackList.append(trackId)
            if random.random() < chanceToStop:
                break
            # select a new destination
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
            trackId = random.randint(0, len(self.problem.tracks))
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
            aleatoryTrackSource = individual.tracks[str(random.randint(1, len(individual.tracks)))]

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

    # def create_first_population(problem, individuals):
    #     population = []

    #     for i in range(individuals):
    #         population.append(Individual(problem))

    #     return population

    generation_individuals = ga.createInitialPopulation(TOTAL_NUMBER_OF_INDIVIDUALS, problem)

    def mate(father, mother):
        # do crossover
        # do mutation
        # return new individual ↓
        return Individual(problem)

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

    print(best_individual["solution"].regularInsertedKMeters)
    print("newInsertedKMeters: ", best_individual["solution"].newInsertedKMeters)
    print("fitness: ", best_individual["solution"].fitness)

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