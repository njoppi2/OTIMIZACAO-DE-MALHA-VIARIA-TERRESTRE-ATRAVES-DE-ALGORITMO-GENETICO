import math
import time
from individual import Individual
from utils import indentZero
from old_fitness import old_fitness
import copy

class UserModel:
    def fitness(self):
        return float("inf")


class UMSalmanAlaswad_I(UserModel):

    def __init__(self, problem):
        self.vehiclesByRoad = 7 # 7 = free
        self.problem = problem
        self.pMatrix = {}
        individual = Individual(self)
        for track in problem.tracks:
            self.calculate_pMatrix(individual, track, useModificationsAndNewTracks=False)

        self.pMatrix = individual.pMatrix



    def calculate_pMatrix(self, individual, track, useModificationsAndNewTracks = False):
        #part1: fixed problem
        #part2: change all adjancent of
        #   individual.tracks_lanes_modifications != 0 and
        #   individual.newTracks
        rid = track["id"]
        s = track["s"]
        t = track["t"]
        individual.pMatrix[rid] = {}

        is_t_source_of_any_track = True
        is_t_source_of_any_newTrack = useModificationsAndNewTracks

        if t not in self.problem.adjLst:
            # no track has this target as source
            is_t_source_of_any_track = False
        if t not in individual.newTracks:
            # no newTrack has this target as source
            is_t_source_of_any_newTrack = False

        total_lanes_with_tt = 0 #

        #1: calculates total_lanes_with_tt
        #1.1 iterates over all regular targets of t
        if is_t_source_of_any_track == True:
            for target_of_t in self.problem.adjLst[t]:
                for track2 in self.problem.adjLst[t][target_of_t]:
                    total_lanes_with_tt += (track2["lanes"] + useModificationsAndNewTracks * individual.tracks_lanes_modifications[track2["id"]]) * track2["normalized_tt"]
        #1.2 iterates over all newTracks targets of t
        if is_t_source_of_any_newTrack == True:
            for target_of_t in individual.newTracks[t]:
                for track2 in individual.newTracks[t][target_of_t]:
                    total_lanes_with_tt += track2["lanes"] * track2["normalized_tt"]

        #makes sure total_lanes_with_tt is not 0 (caused by tracks with distance = 0)
        total_lanes_with_tt = total_lanes_with_tt or 1
        #/1

        #2: sets how many cars continue on the same track
        if is_t_source_of_any_track == True or is_t_source_of_any_newTrack == True:
                individual.pMatrix[rid][rid] = track["normalized_tt"]
        else:
            individual.pMatrix[rid][rid] = 1
        #/2

        #3: distributes the remaining cars from track to its targets (proportionaly to how wide/important they are)
        #3.1 distributes to regular tracks
        if is_t_source_of_any_track == True:
            for target_of_t in self.problem.adjLst[t]:
                for track2 in self.problem.adjLst[t][target_of_t]:
                    rid2 = track2["id"]
                    individual.pMatrix[rid][rid2] = 0
                    individual.pMatrix[rid][rid2] += (1.0 - individual.pMatrix[rid][rid]) * (
                        ((track2["lanes"] + useModificationsAndNewTracks * individual.tracks_lanes_modifications[track2["id"]]) * track2["normalized_tt"]) / (total_lanes_with_tt))
        #3.2 distributes to newTracks
        if is_t_source_of_any_newTrack == True:
            for target_of_t in individual.newTracks[t]:
                for track2 in individual.newTracks[t][target_of_t]:
                    rid2 = track2["id"]
                    individual.pMatrix[rid][rid2] = 0
                    individual.pMatrix[rid][rid2] += (1.0 - individual.pMatrix[rid][rid]) * (
                        (track2["lanes"] * track2["normalized_tt"]) / (total_lanes_with_tt))
        #/3


    def calculate_vehicles_number(self, individual, track, useModificationsAndNewTracks = False):
        # how vehicles number are be calculated: get pMatrix[rid] value to know how many cars are kept on the
        # same track (if pMatrix[rid] is 0.6, and current vehiclesByRoad is 7, then vehiclesByRoad[rid] = 4.2)
        # the other 40% you distribute between the target tracks of the rid track (using pMatrix[rid][rid2])

        rid = track["id"]
        t = track["t"]

        # if rid == 'nt_1':
        #     print(rid)

        def setInitialVehicles(track):
            trackId = track["id"]
            individual.vehiclesByRoad[trackId] = (self.vehiclesByRoad * (track["distance"] / 1000.0) * (
            track["lanes"] + useModificationsAndNewTracks * individual.tracks_lanes_modifications[trackId])) * individual.pMatrix[trackId][trackId]


        if rid not in individual.vehiclesByRoad: # remove ←
            setInitialVehicles(track)
        
        is_t_source_of_any_track = True
        is_t_source_of_any_newTrack = useModificationsAndNewTracks

        if t not in self.problem.adjLst:
            is_t_source_of_any_track = False
        if t not in individual.newTracks:
            is_t_source_of_any_newTrack = False

        # iterates over target tracks of the rid track, 
        if is_t_source_of_any_track == True:
            for target_of_t in self.problem.adjLst[t]:
                for track2 in self.problem.adjLst[t][target_of_t]:
                    rid2 = track2["id"]
                    if rid2 not in individual.vehiclesByRoad:
                        setInitialVehicles(track2)
                    individual.vehiclesByRoad[rid2] += individual.pMatrix[rid][rid2] * (
                                self.vehiclesByRoad * (track["distance"] / 1000.0) * (track["lanes"] + useModificationsAndNewTracks * individual.tracks_lanes_modifications[rid]))

        if is_t_source_of_any_newTrack == True:
            for target_of_t in individual.newTracks[t]:
                for track2 in individual.newTracks[t][target_of_t]:
                    rid2 = track2["id"]
                    if rid2 not in individual.vehiclesByRoad:
                        setInitialVehicles(track2)
                    individual.vehiclesByRoad[rid2] += individual.pMatrix[rid][rid2] * (
                                self.vehiclesByRoad * (track["distance"] / 1000.0) * (track["lanes"] + useModificationsAndNewTracks * individual.tracks_lanes_modifications[rid]))

        # if rid == '11':
        #     print(rid)


    def fitness(self, individual):
        # number of vehicles by track
        individual.vehiclesByRoad = {}

        #calculate_pMatrix
        for track in individual.modifiedTracks:
            self.calculate_pMatrix(individual, track, useModificationsAndNewTracks=True)
            if track["s"] not in self.problem.adjLstInv:
                continue
            sources_of_t = self.problem.adjLstInv[track["s"]]
            for _, list_of_tracks_of_same_s_and_t in sources_of_t.items():
                for track2 in list_of_tracks_of_same_s_and_t:
                    self.calculate_pMatrix(individual, track2, useModificationsAndNewTracks=True)
                
        
        for s in individual.newTracks:
            for t in individual.newTracks[s]:  # pmatrix for non-regular tracks
                for track in individual.newTracks[s][t]:
                    self.calculate_pMatrix(individual, track, useModificationsAndNewTracks=True)
                    if track["s"] not in self.problem.adjLstInv:
                        continue
                    sources_of_t = self.problem.adjLstInv[track["s"]]
                    for _, list_of_tracks_of_same_s_and_t in sources_of_t.items():
                        for track2 in list_of_tracks_of_same_s_and_t:
                            self.calculate_pMatrix(individual, track2, useModificationsAndNewTracks=True)


        #calculate_vehicles_number
        for track in self.problem.tracks:  # number of vehicles for regular tracks
            self.calculate_vehicles_number(individual, track, useModificationsAndNewTracks = True)

        for s in individual.newTracks:  # number of vehicles for non-regular tracks
            for t in individual.newTracks[s]:
                for track in individual.newTracks[s][t]:
                    self.calculate_vehicles_number(individual, track, useModificationsAndNewTracks = True)


        # fitnes value: average density
        densSum = 0.0
        densCount = 0

        #19.8
        tracks_sorted_by_tt = sorted(self.problem.tracks, key = lambda x: x['tt'], reverse=True)
        index_of_5_percent = math.ceil(len(tracks_sorted_by_tt)*0.05)
        most_important5percent_tracks = tracks_sorted_by_tt[:index_of_5_percent]

        for track in most_important5percent_tracks:  # regular tracks
            rid = track["id"]
            dens = indentZero(individual.vehiclesByRoad[rid],
                                   ((track["distance"]) * (track["lanes"] + individual.tracks_lanes_modifications[rid])))
            densSum += dens
            densCount += 1

        individual.fitness = densCount / densSum
        
        return individual.fitness

    def fitness2(self, individual):
        return old_fitness(self, individual)

    
