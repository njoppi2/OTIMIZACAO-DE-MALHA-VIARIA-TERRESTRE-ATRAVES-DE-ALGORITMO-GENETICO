import copy
from math import radians, cos, sin, asin, sqrt


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
