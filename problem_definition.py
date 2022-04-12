import copy
from functools import reduce
from math import radians, cos, sin, asin, sqrt
from matplotlib import pyplot as plt
import numpy as np



# reads the .net file from load_place.py and turns it into a graph
class ProblemDefinition:

    def __init__(self, inputFile):

        # max speed
        self.maxSpeed = 50  # in km/h
        # every intersection between 2+ roads
        self.nodes = None
        # segment of roads, with different maxSpeed, lanes, etc..
        self.tracks = None
        # a dict of all nodes, each containing a list of their targets
        self.adjLst = None
        # a dict of all nodes, each containing a list of nodes that target them
        self.adjLstInv = None
        # minimal travel time
        self.minTT = None
        self.budgetUpdate = 10  # in km
        self.budgetAddition = 10  # in km
        self.valueAt50percent = None

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
        for track in self.tracks:
            s = track["s"]
            t = track["t"]
            if s not in self.adjLst:
                self.adjLst[s] = {}
            if t not in self.adjLst[s]:
                self.adjLst[s][t] = []
            self.adjLst[s][t].append(track)

        # adjacent list inverted
        self.adjLstInv = {}
        for track in self.tracks:
            s = track["s"]
            t = track["t"]
            if t not in self.adjLstInv:
                self.adjLstInv[t] = {}
            if s not in self.adjLstInv[t]:
                self.adjLstInv[t][s] = []
            self.adjLstInv[t][s].append(track)

        # normalizing travel time (tt_i)
        self.minTT = float("+inf")
        tt_list = []
        for track in self.tracks:
            if "maxspeed" in track:
                speed = track["maxspeed"]
            else:
                speed = self.maxSpeed  # kmh

            track["tt"] = track["distance"] / 1000.0 * (1 / speed)

            if self.minTT > track["tt"]:
                self.minTT = track["tt"]
                
        # for track in self.tracks:
        #     # normalized in this case means its value is between 1 and infite
        #     track["normalized_tt"] = (track["tt"]) / self.minTT

            tt_list.append(track["tt"])
        tt_list.sort(reverse=True)
        current_sum = 0
        total_sum = sum(tt_list)
        index_middle_of_area = 0
        for i in range(len(tt_list)):
            tt = tt_list[i]
            if current_sum < total_sum / 2:
                current_sum += tt
            else:
                index_middle_of_area = i
                break

        self.valueAt50percent = tt_list[index_middle_of_area]
        # percentage = list(map(lambda x: 1 - pow(2, -x / valueAt50percent), tt_list))
        # current_distribuition = sorted(list(map(lambda x: (x['tt'] - 1) / x['tt'], self.tracks)), reverse=True)
        # plt.margins(x=0.003, y=0.001)
        # plt.plot(percentage)
        # plt.show()

        for track in self.tracks:
            # normalized_tt is a value between 0 and 1
            track["normalized_tt"] = self.normalize_tt(track["tt"])

    def normalize_tt(self, tt):
        return 1 - pow(2, -tt / self.valueAt50percent)

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
