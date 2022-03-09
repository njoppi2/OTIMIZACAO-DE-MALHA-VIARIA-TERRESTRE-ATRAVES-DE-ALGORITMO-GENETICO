import osmnx as ox
import networkx as nx
import copy
import matplotlib.pyplot as plt
import utm
from utils import place_name

from math import radians, cos, sin, asin, sqrt


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the spherical surface of Earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    # Radius of earth in kilometers is 6371
    km = 6371* c
    return km * 1000.0

inputFile = place_name+'.net'

nodes = {}
roads = []

osmNetFile = open(inputFile, 'r')
lines = osmNetFile.readlines()

arcsPhase = False
roadId= 0
for line in lines:
    if line[0:4] == '*arc':
        arcsPhase = True
        continue
    data = line.split(' ')
    data[-1] = data[-1].replace('\n','')
    if not arcsPhase: 
        #node phase
        #1 90199676 -48.54448 -27.6634265 ellipse
        if len(data) < 4: continue
        nodeId = data[0]
        nodeLong = float(data[2])
        nodeLat = float(data[3])
        word = ""
        for i in range(5, len(data)):
            sub = data[i]
            word += str(sub) + " "
        nodes[nodeId] = {"id": int(nodeId), "lat": nodeLat, "long":nodeLong, "properties":word.strip()}
    else:
        #arc phase
        #9 9499 1.0 lanes 3 highway trunk name "Rodovia Governador Aderbal Ramos da Silva" maxspeed 80 ref SC-401 oneway yes
        s = data[0]
        t = data[1]
        distance = max(0.1,haversine(nodes[s]["long"],nodes[s]["lat"],nodes[t]["long"],nodes[t]["lat"]))
        #arc metadata
        arc={"s": s, "t": t, "distance": distance}
        for i in range(2, len(data)):
            word = data[i]
            if word == "oneway":
                arc["oneway"] = data[i+1]
            if word == "lanes":
                arc["lanes"] = int (data[i+1])
            if word == "maxspeed":
                arc["maxspeed"] = int (data[i+1])
            if word == "ref":
                if data[i+1][0] == "\"":
                    name = ""
                    c=0
                    for subw in data[i+1:]:
                        c+=1
                        name += subw.replace("\"","")+" "
                        if subw[-1] == "\"":
                            break
                    arc["ref"] = name.strip()
                    i+= c -1
                    continue
                else:
                    arc["ref"] = data[i+1]
            if word == "name":
                name = ""
                c=0
                for subw in data[i+1:]:
                    c+=1
                    name += subw.replace("\"","")+" "
                    if subw[-1] == "\"":
                        break
                arc["name"] = name.strip()
                i+= c -1 
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
            roadId+=1
            arc2["id"] = str(roadId)
            roads.append(arc2)
        roadId+=1
        arc["id"] = str(roadId)
        roads.append(arc)





#adjacent list
adjLst = {}
for road in roads:
    s = road["s"]
    t = road["t"]
    if s not in adjLst:
        adjLst[s]={}
    if t not in adjLst[s]:
        adjLst[s][t] = []
    adjLst[s][t].append(road)
    
maxSpeed = 50

    
#normalizing travel time (tt_i)
minTT = float("+inf")
for road in roads:
    speed = maxSpeed #kmh
    if "maxspeed" in road:
        speed = road["maxspeed"]
    if minTT > road["distance"]:
        minTT = road["distance"]/1000.0 * (1/speed)
for i in range(len(roads)):
    roads[i]["tt"] = (road["distance"]/1000.0 * (1/speed)) / minTT
    



minimum = float("+inf")

for road in roads:
    speed = maxSpeed #kmh
    if "maxspeed" in road:
        if maxSpeed< road["maxspeed"]: maxSpeed = road["maxspeed"]
        speed = road["maxspeed"]
    value = road["distance"]/1000.0 * (1/speed)
    if minimum > value:
        minimum = value




pMatrix = {}
for road in roads:
    rid = road["id"]
    s = road["s"]
    t = road["t"]
    pMatrix[rid] = {}
    
    
    
    
    if t not in adjLst:
        pMatrix[rid][rid] = 1
        continue
        
    
    
    lanes = 0
    for tl in adjLst[t]:
        for road2 in adjLst[t][tl]:
            speed = maxSpeed #kmh
            if "maxspeed" in road2:
                speed = road2["maxspeed"]
            lanes += road2["lanes"]*(1/speed)
            
    speed = maxSpeed #kmh
    if "maxspeed" in road:
        speed = road["maxspeed"] 
    if road["distance"] == 0.0:
        pMatrix[rid][rid] = 0.0
    else:
        
        pMatrix[rid][rid] = (road["tt"]-1) / (road["tt"])                        
        #pMatrix[rid][rid] = ((1/speed) - 1/maxSpeed)/ ((1/speed))                        
        #pMatrix[rid][rid] = (road["distance"]/1000.0 * (1/speed) - 1/60)/ (road["distance"]/1000.0 * (1/speed))                        
        #pMatrix[rid][rid] = ((road["lanes"] * (150-speed) - value)/ lanes)                        
    
    for tl in adjLst[t]:
        for road2 in adjLst[t][tl]:
            rid2 = road2["id"]
            pMatrix[rid][rid2] = 0
            speed = maxSpeed #kmh
            if "maxspeed" in road2:
                speed = road2["maxspeed"]
            pMatrix[rid][rid2] += (1.0-pMatrix[rid][rid])*((road2["lanes"] * (1/speed))/ (lanes) )
            
    

    



#distributing vehicles
numVehicles = 7 #por km por pista
vehiclesByRoad = {}
for i in range(len(roads)):
    road = roads[i]
    rid = road["id"]
    s = road["s"]
    t = road["t"]
    if rid not in vehiclesByRoad:
        vehiclesByRoad[rid] = (numVehicles*(road["distance"]/1000.0)*road["lanes"])*pMatrix[rid][rid]
    if t not in adjLst:
        continue
    for tl in adjLst[t]:
        for road2 in adjLst[t][tl]:
            rid2 = road2["id"]
            if rid2 not in vehiclesByRoad:
                vehiclesByRoad[rid2] = (numVehicles*(road2["distance"]/1000.0)*road2["lanes"])*pMatrix[rid2][rid2]
            vehiclesByRoad[rid2] += pMatrix[rid][rid2]*(numVehicles*(road["distance"]/1000.0)*road["lanes"])

maxDensity = 0
maxId = []
for i in range(len(roads)):
    road = roads[i]
    rid = road["id"]
    roads[i]["dens"] = vehiclesByRoad[rid]
    if vehiclesByRoad[rid] > maxDensity:
        maxDensity = vehiclesByRoad[rid]
        maxId.clear()
    if vehiclesByRoad[rid] == maxDensity:
        maxId.append(road)
        


# print(maxId)
# print(maxDensity)

edgeColors = []
for road in roads:
    color = ""
    if road["dens"] <= 7*(road["distance"]/1000.0)*road["lanes"]:
        color="green"
    elif road["dens"] <= 11*(road["distance"]/1000.0)*road["lanes"]:
        color="yellow"
    elif road["dens"] <= 22*(road["distance"]/1000.0)*road["lanes"]:
        color="orange"
    elif road["dens"] <= 28*(road["distance"]/1000.0)*road["lanes"]:
        color="purple"
    else:
        color="red"
    edgeColors.append(color)
        
        
#creating graph for presentation
graph = nx.MultiGraph()

i=0
for node in nodes:
    graph.add_node(str(nodes[node]["id"]))

#arcs
for road in roads:
    #if road["s"] not in graph.nodes() or road["t"] not in graph.nodes(): continue
    graph.add_edge(road["s"], road["t"])


nodePos={}
#for node in nodes:
for (node, data) in graph.nodes(data=True):
    l = utm.from_latlon(nodes[node]["lat"], nodes[node]["long"])
    x, y =  l[0], l[1]
    nodePos[node] = [x,y]






nx.draw_networkx(graph, pos=nodePos,  with_labels=False, node_size=0, edge_color=edgeColors)
plt.savefig(place_name+".png", format="PNG")
plt.savefig(place_name+".pdf", format="PDF")
#plt.show()


#nx.draw_networkx(graph, pos=nodePos, with_labels=True, edge_color=edgeColors)
#plt.tight_layout()
#plt.savefig("output.pdf", format="PDF")

#plt.savefig("output.png", format="PNG")
#nx.draw(graph, edge_color=edgeColors)
#fig, ax = ox.plot_graph(graph, edge_color=edgeColors)


