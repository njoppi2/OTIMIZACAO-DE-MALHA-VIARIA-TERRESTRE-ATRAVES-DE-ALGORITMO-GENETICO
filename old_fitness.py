def old_fitness(self, individual):
    individual.vehiclesByRoad = {}

    # timeA = time.time() * 10000

    # Is it required to renormalize travel time? (tt_i)
    minTT = self.problem.minTT
    new_tracks_minTT = minTT

    #0.07
    # get the smallest travel time from new_tracks
    for source in individual.newTracks:
        for target in individual.newTracks[source]:
            for track in individual.newTracks[source][target]:
                speed = self.problem.maxSpeed  # kmh
                if "maxspeed" in track:
                    speed = track["maxspeed"]
                track["tt"] = track["distance"] / 1000.0 * (1 / speed)
                if new_tracks_minTT > track["tt"]:
                    new_tracks_minTT = track["tt"]

    # timeB = time.time() * 10000
    # print("until 36: ",timeB - timeA)

    #0.4 (1 print demora uns 0.3)
    if minTT > new_tracks_minTT:
        # update travel time information in self.problem instance / newroads
        for track in self.problem.tracks:
            if "maxspeed" in track:
                speed = track["maxspeed"]
            #essa linha foi modificada↓:
            #roads[i]["normalized_tt"] = (road["distance"] / 1000.0 * (1 / speed)) / nminTT
            track["normalized_tt"] = track["tt"] / new_tracks_minTT
        for source in individual.newTracks:
            for target in individual.newTracks[source]:
                for newTrack in individual.newTracks[source][target]:
                    speed = self.problem.maxSpeed  # kmh
                    if "maxspeed" in newTrack:
                        speed = track["maxspeed"]
                    newTrack["normalized_tt"] = (newTrack["distance"] / 1000.0 * (1 / speed)) / new_tracks_minTT
    # timeC = time.time() * 10000
    # print("36-53: ",timeC - timeB)

    # calculating pmatriz
    pMatrix = {}

    # 66.5
    for track in self.problem.tracks:  # pmatrix for regular tracks
        rid = track["id"]
        s = track["s"]
        t = track["t"]
        pMatrix[rid] = {}


        is_t_source_adjList = t in self.problem.adjLst # True or False
        is_t_source_adjIndividual = t in individual.newTracks # True or False

        total_lanes_with_tt = 0
        if is_t_source_adjList == True:
            for tl in self.problem.adjLst[t]:
                for track2 in self.problem.adjLst[t][tl]:
                    speed = self.problem.maxSpeed  # kmh
                    if "maxspeed" in track2:
                        speed = track2["maxspeed"]
                    total_lanes_with_tt += (track2["lanes"] + individual.tracks[track2["id"]]) * track["normalized_tt"]

        if is_t_source_adjIndividual == True:
            for tl in individual.newTracks[t]:
                for track2 in individual.newTracks[t][tl]:
                    speed = self.problem.maxSpeed  # kmh
                    if "maxspeed" in track2:
                        speed = track2["maxspeed"]
                    total_lanes_with_tt += track2["lanes"] * track["normalized_tt"]

        if is_t_source_adjList == True or is_t_source_adjIndividual == True:
            speed = self.problem.maxSpeed  # kmh
            if "maxspeed" in track:
                speed = track["maxspeed"]
            if track["distance"] == 0.0:
                pMatrix[rid][rid] = 0.0
            else:
                pMatrix[rid][rid] = track["normalized_tt"]


        if is_t_source_adjList == True:
            for tl in self.problem.adjLst[t]:
                for track2 in self.problem.adjLst[t][tl]:
                    rid2 = track2["id"]
                    pMatrix[rid][rid2] = 0
                    speed = self.problem.maxSpeed  # km/h
                    if "maxspeed" in track2:
                        speed = track2["maxspeed"]
                    pMatrix[rid][rid2] += (1.0 - pMatrix[rid][rid]) * (
                                ((track2["lanes"] + individual.tracks[track2["id"]]) * track["normalized_tt"]) / (total_lanes_with_tt))

        if is_t_source_adjIndividual == True:

            for tl in individual.newTracks[t]:
                for track2 in individual.newTracks[t][tl]:
                    rid2 = track2["id"]
                    pMatrix[rid][rid2] = 0
                    speed = self.problem.maxSpeed  # km/h
                    if "maxspeed" in track2:
                        speed = track2["maxspeed"]
                    pMatrix[rid][rid2] += (1.0 - pMatrix[rid][rid]) * ((track2["lanes"] * track["normalized_tt"]) / (total_lanes_with_tt))

        if is_t_source_adjList == False and is_t_source_adjIndividual == False:
            pMatrix[rid][rid] = 1

    # timeD = time.time() * 10000
    # print("53-122: ",timeD - timeC)

    #0.5
    for s in individual.newTracks:
        for t in individual.newTracks[s]:  # pmatrix for non-regular tracks
            for track in individual.newTracks[s][t]:  # pmatrix for non-regular tracks
                rid = track["id"]

                pMatrix[rid] = {}

                is_t_source_adjList = True
                is_t_source_adjIndividual = True

                if t not in self.problem.adjLst:
                    is_t_source_adjList = False
                if t not in individual.newTracks:
                    is_t_source_adjIndividual = False

                total_lanes_with_tt = 0
                if is_t_source_adjList == True:
                    for tl in self.problem.adjLst[t]:
                        for track2 in self.problem.adjLst[t][tl]:
                            speed = self.problem.maxSpeed  # kmh
                            if "maxspeed" in track2:
                                speed = track2["maxspeed"]
                            total_lanes_with_tt += (track2["lanes"] + individual.tracks[track2["id"]]) * (1 / speed)

                if is_t_source_adjIndividual == True:
                    for tl in individual.newTracks[t]:
                        for track2 in individual.newTracks[t][tl]:
                            speed = self.problem.maxSpeed  # kmh
                            if "maxspeed" in track2:
                                speed = track2["maxspeed"]
                            total_lanes_with_tt += track2["lanes"] * (1 / speed)

                if is_t_source_adjList == True or is_t_source_adjIndividual == True:
                    speed = self.problem.maxSpeed  # kmh
                    if "maxspeed" in track:
                        speed = track["maxspeed"]
                    if track["distance"] == 0.0:
                        pMatrix[rid][rid] = 0.0
                    else:
                        pMatrix[rid][rid] = track["normalized_tt"]

                if is_t_source_adjList == True:
                    for tl in self.problem.adjLst[t]:
                        for track2 in self.problem.adjLst[t][tl]:
                            rid2 = track2["id"]
                            pMatrix[rid][rid2] = 0
                            speed = self.problem.maxSpeed  # km/h
                            if "maxspeed" in track2:
                                speed = track2["maxspeed"]
                            pMatrix[rid][rid2] += (1.0 - pMatrix[rid][rid]) * (
                                        ((track2["lanes"] + individual.tracks[track2["id"]]) * (1 / speed)) / (
                                    total_lanes_with_tt))

                if is_t_source_adjIndividual == True:
                    for tl in individual.newTracks[t]:
                        for track2 in individual.newTracks[t][tl]:
                            rid2 = track2["id"]
                            pMatrix[rid][rid2] = 0
                            speed = self.problem.maxSpeed  # km/h
                            if "maxspeed" in track2:
                                speed = track2["maxspeed"]
                            pMatrix[rid][rid2] += (1.0 - pMatrix[rid][rid]) * (
                                        (track2["lanes"] * (1 / speed)) / (total_lanes_with_tt))

                if is_t_source_adjList == False and is_t_source_adjIndividual == False:
                    pMatrix[rid][rid] = 1

    # timeE = time.time() * 10000
    # print("122-190: ",timeE - timeD)

    # number of vehicles by track
    individual.vehiclesByRoad = {}

    # separar as newTrack e onde elas incidem (ver adjList e adjInt)
    # fazer o calculo so pro problema e reutilizar o max possivel
    # ranking de 30 a 1 na roleta ou fazer max - min

    #66.0
    for track in self.problem.tracks:  # number of vehicles for regular tracks
        rid = track["id"]
        s = track["s"]
        t = track["t"]
        if rid not in individual.vehiclesByRoad:
            individual.vehiclesByRoad[rid] = (self.vehiclesByRoad * (track["distance"] / 1000.0) * (
                        track["lanes"] + individual.tracks[rid])) * pMatrix[rid][rid]
        
        # if individual.vehiclesByRoad[rid] < 0:
        #     print(individual.vehiclesByRoad[rid])

        is_t_source_adjList = True
        is_t_source_adjIndividual = True

        if t not in self.problem.adjLst:
            is_t_source_adjList = False
        if t not in individual.newTracks:
            is_t_source_adjIndividual = False

        if is_t_source_adjList == True:
            for tl in self.problem.adjLst[t]:
                for track2 in self.problem.adjLst[t][tl]:
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

    # timeF = time.time() * 10000
    # print("190-231: ",timeF - timeE)

    # for i in range(len(individual.newTracks)):

    #0.6
    for s in individual.newTracks:  # number of vehicles for non-regular tracks
        for t in individual.newTracks[s]:
            for track in individual.newTracks[s][t]:
                rid = track["id"]

                if rid not in individual.vehiclesByRoad:
                    individual.vehiclesByRoad[rid] = (self.vehiclesByRoad * (track["distance"] / 1000.0) * (
                    track["lanes"])) * pMatrix[rid][rid]

                is_t_source_adjList = True
                is_t_source_adjIndividual = True

                if t not in self.problem.adjLst:
                    is_t_source_adjList = False
                if t not in individual.newTracks:
                    is_t_source_adjIndividual = False

                if is_t_source_adjList == True:
                    for tl in self.problem.adjLst[t]:
                        for track2 in self.problem.adjLst[t][tl]:
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

    # timeG = time.time() * 10000
    # print("231-270: ",timeG - timeF)

    # fitnes value: average density
    total_vehiclesXtt = 0.0
    total_kmXlanes = 0

    #19.8
    for track in self.problem.tracks:  # regular tracks
        rid = track["id"]

        total_vehiclesXtt += individual.vehiclesByRoad[rid]
        total_kmXlanes += (track["distance"] / 1000.0) * (track["lanes"] + individual.tracks[rid])
        
    for s in individual.newTracks:
        for t in individual.newTracks[s]:
            for track in individual.newTracks[s][t]:
                rid = track["id"]
                
                total_vehiclesXtt += individual.vehiclesByRoad[rid]
                total_kmXlanes += (track["distance"] / 1000.0) * (track["lanes"])

    individual.fitness = total_kmXlanes * 100 / total_vehiclesXtt
    
    # timeH = time.time() * 10000
    # print("270-292: ",timeH - timeG)
    
    return individual.fitness

    # 1km * 1faixa = 1kmf || 1 km/f
    # 100km * 10faixas = 1000kmf || 10km/f

