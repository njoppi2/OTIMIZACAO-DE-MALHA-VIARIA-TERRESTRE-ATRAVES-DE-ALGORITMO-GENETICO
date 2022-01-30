from utils import indentZero
from translator import roads, road


class UserModel:
    def fitness(self):
        return float("inf")


class UMSalmanAlaswad_I(UserModel):

    def __init__(self, problem):
        self.vehiclesByRoad = 7
        self.problem = problem

    def fitness(self, individual):
        individual.vehiclesByRoad = {}

        # Is it required to renormalize travel time? (tt_i)
        minTT = self.problem.minTT
        nminTT = minTT

        for source in individual.newTracks:
            for target in individual.newTracks[source]:
                for track in individual.newTracks[source][target]:
                    speed = self.problem.maxSpeed  # kmh
                    if "maxspeed" in track:
                        speed = track["maxspeed"]
                    if nminTT > track["distance"]:
                        nminTT = track["distance"] / 1000.0 * (1 / speed)
        if minTT > nminTT:
            # update travel time information in self.problem instance / newroads
            for i in range(len(self.problem.tracks)):
                if "maxspeed" in self.problem.tracks[i]:
                    speed = track["maxspeed"]
                roads[i]["tt"] = (road["distance"] / 1000.0 * (1 / speed)) / nminTT
            for source in individual.newTracks:
                for target in individual.newTracks[source]:
                    for i in range(len(individual.newTracks[source][target])):
                        speed = self.problem.maxSpeed  # kmh
                        if "maxspeed" in individual.newTracks[source][target][i]:
                            speed = track["maxspeed"]
                        individual.newTracks[source][target][i]["tt"] = (individual.newTracks[source][target][i][
                                                                             "distance"] / 1000.0 * (
                                                                                     1 / speed)) / nminTT

        # calculating pmatriz
        pMatrix = {}
        for track in self.problem.tracks:  # pmatrix for regular tracks
            rid = track["id"]
            s = track["s"]
            t = track["t"]
            pMatrix[rid] = {}

            is_t_source_adjList = True
            is_t_source_adjIndividual = True

            if t not in self.problem.adjLst:
                is_t_source_adjList = False
            if t not in individual.newTracks:
                is_t_source_adjIndividual = False

            lanes = 0
            if is_t_source_adjList == True:
                for tl in self.problem.adjLst[t]:
                    for track2 in self.problem.adjLst[t][tl]:
                        speed = self.problem.maxSpeed  # kmh
                        if "maxspeed" in track2:
                            speed = track2["maxspeed"]
                        lanes += (track2["lanes"] + individual.tracks[track2["id"]]) * (1 / speed)

            if is_t_source_adjIndividual == True:
                for tl in individual.newTracks[t]:
                    for track2 in individual.newTracks[t][tl]:
                        speed = self.problem.maxSpeed  # kmh
                        if "maxspeed" in track2:
                            speed = track2["maxspeed"]
                        lanes += track2["lanes"] * (1 / speed)

            if is_t_source_adjList == True or is_t_source_adjIndividual == True:
                speed = self.problem.maxSpeed  # kmh
                if "maxspeed" in track:
                    speed = track["maxspeed"]
                if track["distance"] == 0.0:
                    pMatrix[rid][rid] = 0.0
                else:
                    pMatrix[rid][rid] = (track["tt"] - 1) / (track["tt"])

            if is_t_source_adjList == True:
                for tl in self.problem.adjLst[t]:
                    for track2 in self.problem.adjLst[t][tl]:
                        rid2 = track2["id"]
                        pMatrix[rid][rid2] = 0
                        speed = self.problem.maxSpeed  # km/h
                        if "maxspeed" in track2:
                            speed = track2["maxspeed"]
                        pMatrix[rid][rid2] += (1.0 - pMatrix[rid][rid]) * (
                                    ((track2["lanes"] + individual.tracks[track2["id"]]) * (1 / speed)) / (lanes))

            if is_t_source_adjIndividual == True:

                for tl in individual.newTracks[t]:
                    for track2 in individual.newTracks[t][tl]:
                        rid2 = track2["id"]
                        pMatrix[rid][rid2] = 0
                        speed = self.problem.maxSpeed  # km/h
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

                    if t not in self.problem.adjLst:
                        is_t_source_adjList = False
                    if t not in individual.newTracks:
                        is_t_source_adjIndividual = False

                    lanes = 0
                    if is_t_source_adjList == True:
                        for tl in self.problem.adjLst[t]:
                            for track2 in self.problem.adjLst[t][tl]:
                                speed = self.problem.maxSpeed  # kmh
                                if "maxspeed" in track2:
                                    speed = track2["maxspeed"]
                                lanes += (track2["lanes"] + individual.tracks[track2["id"]]) * (1 / speed)

                    if is_t_source_adjIndividual == True:
                        for tl in individual.newTracks[t]:
                            for track2 in individual.newTracks[t][tl]:
                                speed = self.problem.maxSpeed  # kmh
                                if "maxspeed" in track2:
                                    speed = track2["maxspeed"]
                                lanes += track2["lanes"] * (1 / speed)

                    if is_t_source_adjList == True or is_t_source_adjIndividual == True:
                        speed = self.problem.maxSpeed  # kmh
                        if "maxspeed" in track:
                            speed = track["maxspeed"]
                        if track["distance"] == 0.0:
                            pMatrix[rid][rid] = 0.0
                        else:
                            pMatrix[rid][rid] = (track["tt"] - 1) / (track["tt"])

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
                                        lanes))

                    if is_t_source_adjIndividual == True:
                        for tl in individual.newTracks[t]:
                            for track2 in individual.newTracks[t][tl]:
                                rid2 = track2["id"]
                                pMatrix[rid][rid2] = 0
                                speed = self.problem.maxSpeed  # km/h
                                if "maxspeed" in track2:
                                    speed = track2["maxspeed"]
                                pMatrix[rid][rid2] += (1.0 - pMatrix[rid][rid]) * (
                                            (track2["lanes"] * (1 / speed)) / (lanes))

                    if is_t_source_adjList == False and is_t_source_adjIndividual == False:
                        pMatrix[rid][rid] = 1

        # number of vehicles by track
        individual.vehiclesByRoad = {}
        for i in range(len(self.problem.tracks)):  # number of vehicles for regular tracks
            track = self.problem.tracks[i]
            rid = track["id"]
            s = track["s"]
            t = track["t"]
            if rid not in individual.vehiclesByRoad:
                individual.vehiclesByRoad[rid] = (self.vehiclesByRoad * (track["distance"] / 1000.0) * (
                            track["lanes"] + individual.tracks[rid])) * pMatrix[rid][rid]

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

        # fitnes value: average density
        densSum = 0.0
        densCount = 0
        for track in self.problem.tracks:  # regular tracks
            rid = track["id"]
            dens = indentZero(individual.vehiclesByRoad[rid],
                                   ((track["distance"] / 1000.0) * (track["lanes"] + individual.tracks[rid])))
            densSum += dens
            densCount += 1
        for s in individual.newTracks:
            for t in individual.newTracks[s]:
                for track in individual.newTracks[s][t]:
                    rid = track["id"]
                    dens = indentZero(individual.vehiclesByRoad[rid],
                                           ((track["distance"] / 1000.0) * (track["lanes"])))
                    densSum += dens
                    densCount += 1

        individual.fitness = densSum / densCount

        return individual.fitness

