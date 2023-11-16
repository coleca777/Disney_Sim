import random
from copy import deepcopy
from math import ceil, log10
from collections import Counter
from graph_network import Map

adult_rides = ["Space Mountain", "Buzz Lightyear", "People Mover", "Astro Orbiter",
            "Tomorrowland Speedway", "Monster's Inc Laugh Floor", "Carousel of Progress",
            "Teacups", "Seven Dwarves Mine Train", "Winnie the Pooh", "Under the Sea",
            "Prince Charming's Carousel", "Mickey's Philhart Magic", "Small World", "Peter Pan",
            "Haunted Mansion", "Big Thunder Mountain",
            "Splash Mountain", "Pirates", "Jungle Cruise", "Aladdin"]

kid_rides = ["Buzz Lightyear", "People Mover", "Astro Orbiter",
            "Tomorrowland Speedway", "Monster's Inc Laugh Floor", "Carousel of Progress",
            "Teacups", "Seven Dwarves Mine Train", "Winnie the Pooh", "Under the Sea",
            "Prince Charming's Carousel", "Mickey's Philhart Magic", "Small World", "Peter Pan",
            "Dumbo", "Goofy Barnstormer", "Haunted Mansion",
            "Pirates", "Jungle Cruise", "Aladdin"]

rain_rides = ["Space Mountain", "Buzz Lightyear", "Monster's Inc Laugh Floor", "Carousel of Progress",
            "Winnie the Pooh", "Under the Sea", "Mickey's Philhart Magic", "Small World", "Peter Pan",
            "Haunted Mansion", "Pirates"]

class Party:
    def __init__(self, name: str, party_num: int, thought: str):
        #There are 4 (?) age groups (young child) (old child / young adult) (regular adult) (elder adult)
        self.guests = []
        self.party_size = party_num
        self.wait_time = 0
        self.rides = []
        self.failed_rides = []
        self.unique_rides = 0
        self.num_rides = 0
        self.walking_time = 0
        self.current_location = "Main Gate"
        self.next_location = ""
        self.path = []
        self.action = "Decide"
        self.thought = thought   #Random or KBAI or Closest

        #There must be at least 1 of the last 3 groups to ensure it is never just a child
        first_member_type = random.randint(1, 3)
        self.guests.append(Guest(name, first_member_type))
        name += 1
        party_num -= 1
        while party_num > 0:
            self.guests.append(Guest(name, random.randint(0, 3)))
            name += 1
            party_num -= 1

    def decide(self, map: Map, rides_dict: dict, do_rain_rides: bool, rain: bool):
        #Randomly chooses a ride that works for all guests
        tired_guest = False
        rides = adult_rides
        slowest_speed = 1000
        for guest in self.guests:
            if guest.energy <= 30:
                tired_guest = True
            if guest.age_range == 0:
                rides = kid_rides
            if guest.walk_speed < slowest_speed:
                slowest_speed = guest.walk_speed
            
        if do_rain_rides:
            rides = rain_rides

        if tired_guest:
            return "Main Gate", slowest_speed
        
        elif self.thought == "Random":
            best_ride = random.sample(rides, 1)


        elif self.thought == "KBAI":
            best_satisfaction = 0
            best_ride = ""
            current_satisfaction = self.get_satisfactions(0, 0, rain)
            for ride in rides:
                test_party = deepcopy(self)
                distance_travelled = map.shortest_paths[test_party.current_location][0][ride]
                walking_time = ceil(distance_travelled / slowest_speed)
                current_wait_time = rides_dict[ride]["waitTime"]
                test_party.wait_time += current_wait_time
                test_party.walking_time += walking_time
                test_party.rides.append(ride)
                test_party.num_rides = len(test_party.rides)
                test_party.unique_rides = len(Counter(test_party.rides))
                satisfaction = test_party.get_satisfactions(walking_time, current_wait_time, rain)
                if satisfaction > best_satisfaction:
                    best_satisfaction = satisfaction
                    best_ride = [ride]
            if current_satisfaction - 3 > best_satisfaction:
                best_ride = ["Main Gate"]

        elif self.thought == "Closest":
            closest = 100000
            best_ride = ""

            for ride in rides:
                if ride not in self.rides:
                    distance = map.shortest_paths[self.current_location][0][ride]
                    if distance < closest:
                        best_ride = [ride]
                        closest = distance
                elif len(self.rides) >= len(rides):
                    mult = len(self.rides) // len(rides)
                    start_ind = len(rides) * mult
                    compare = self.rides[start_ind:]
                    if ride not in compare:
                        distance = map.shortest_paths[self.current_location][0][ride]
                        if distance < closest:
                            best_ride = [ride]
                            closest = distance

                
        return best_ride[0], slowest_speed
    
    def get_satisfactions(self, newWalking: int, newWaiting: int, rain: bool):
        satisfaction_list = [] 
        if rain:
            rain_mult = 2
        else:
            rain_mult = 1
        for guest in self.guests:
            failed_ride_points = 0
            for ride in self.failed_rides:
                if ride in guest.interests:
                    failed_ride_points += 7
                else:
                    failed_ride_points += 5
            if self.num_rides == 0:
                guest.satisfaction = failed_ride_points
            else:
                guest.energy -= (0.75*newWalking*rain_mult + 0.2*newWaiting) * guest.energy_depletion
                interest_points = 0
                point_dict = {}
                for interest_ride in guest.interests:
                    point_dict[interest_ride] = 5

                for ride in self.rides:
                    if ride in point_dict:
                        interest_points += point_dict[ride]
                        point_dict[ride] /= 2
                        continue
                    for like_ride in point_dict:
                        if point_dict[like_ride] < 5:
                            point_dict[like_ride] += 0.5

                failed_ride_points = 0
                for ride in self.failed_rides:
                    if ride in guest.interests:
                        failed_ride_points += 7
                    else:
                        failed_ride_points += 5

                guest.satisfaction = round(self.num_rides*(1+(log10(self.unique_rides/self.num_rides)/2))*2 + interest_points + round(guest.energy/10, 0) - failed_ride_points, 2) 

            satisfaction_list.append(guest.satisfaction)

        return round(sum(satisfaction_list) / len(satisfaction_list), 2)
    
    def can_ride(self, ride):
        return ride in rain_rides

        

class Guest:
    def __init__(self, name: str, age_range: int):
        self.satisfaction = 0
        self.satisfaction_list = []
        self.name = str(name)
        self.energy = 100
        self.age_range = age_range

        if age_range != 0:
            self.interests = random.sample(adult_rides, 3)

        #Young Child assumes less than 40 inches
        else:
            self.interests = random.sample(kid_rides, 3)
            self.energy_depletion = 1.25
            self.walk_speed = 1.30 * 60                              #Walk speed is in meters/minute

        #old child to young adult
        if age_range == 1: 
            self.energy_depletion = 0.9
            self.walk_speed = 1.35 * 60

        #regular adult
        elif age_range == 2:      
            self.energy_depletion = 1
            self.walk_speed = 1.25 * 60

        #elder adult
        else:                   
            self.energy_depletion = 1.20
            self.walk_speed = 1.2 * 60

