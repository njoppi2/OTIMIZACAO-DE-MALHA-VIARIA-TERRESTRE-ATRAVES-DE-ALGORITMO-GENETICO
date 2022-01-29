import osmnx as ox
import networkx as nx
import matplotlib.pyplot as pyplot
import utm

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

