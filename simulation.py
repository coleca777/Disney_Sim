from graph_network import Map
from queue import PriorityQueue
from guest import Party
import json
import random
from math import ceil
from datetime import datetime
from collections import Counter
import os
import shutil

from dataclasses import dataclass, field
from typing import Any

@dataclass(order=True)
class PrioritizedItem:
    priority: int
    item: Any=field(compare=False)

class Simulation:
    def __init__(self, knowledge_path: str):
        f = open(knowledge_path)
        data = json.load(f) 
        self.edges = data['edges']
        self.points = data['points']
        self.parties = []
        self.magic_kingdom = Map(self.edges)
        self.events = PriorityQueue()
        self.events.put(PrioritizedItem(0, "Start"))
        self.time = 0
        self.max_time = 14*60  #Park is generally open from 9 AM to 11 PM
        self.people = 0
        self.rain = False
        self.rain_rides = False
    
    def main(self, thought: str, weatherList: list = []):
        while self.events.qsize() != 0 and self.time <= self.max_time:
            print(self.time)
            #Remove the placeholder initialization 
            if self.time == 0:
                self.events.get()
                for weather in weatherList:
                    self.events.put(PrioritizedItem(weather, "Rain"))
                # testParty = Party(1, 1, thought)
                # self.events.put(PrioritizedItem(1, testParty))                            #This is used for testing purpose
                # self.parties.append(testParty)
                # self.people += 1
                # self.points["Main Gate"]["currPeople"] += 1

            # For the first 3 hours of park being open, roughly 310 people enter the park
            # This leads to an average of 55,800 guests
            if self.time < 3*60:
                num_people = 0  
                while num_people < 310:                                                     #If testing comment out this entire if block
                    #TODO: Change distribution instead of just random
                    party_size = random.randint(1, 6)
                    party = Party(self.people + 1, party_size, thought)
                    self.parties.append(party)
                    self.events.put(PrioritizedItem(self.time+1, party))
                    num_people += party_size
                    self.people += party_size
                    self.points["Main Gate"]["currPeople"] += party_size

            #Go through all events who's priority matches the current time
            while True:
                if self.events.qsize() == 0:
                    break
                event = self.events.get()
                priority = event.priority
                #If the current event's prioirty is not for this time, put in back in the queue
                if priority != self.time:
                    self.events.put(event)
                    break 

                currParty = event.item

                if currParty == "Rain":
                    if self.rain:
                        self.rain = False
                        print("Rain has Stopped")
                        self.events.put(PrioritizedItem(self.time+15, "Open"))
                    else:
                        self.rain = True
                        self.rain_rides = True
                        self.events = self.update_events()
                        rain_time = random.randint(25, 75)
                        print(f"Rain will stop at {self.time+ 60}")
                        self.events.put(PrioritizedItem(self.time + 60, "Rain"))

                elif currParty == "Open":
                    print("Rides have opened back up")
                    self.rain_rides = False

                elif currParty.action == "Decide":
                    #Chooses next ride based on the party's thought (random, KBAI, or closest)
                    ride, speed = currParty.decide(self.magic_kingdom, self.points, self.rain_rides, self.rain)

                    if ride == currParty.current_location:
                        currParty.action = "Ride"
                        self.events.put(PrioritizedItem(self.time, currParty))
                        continue

                    #Sets the path
                    #The [1:] is there to ensure the current location isn't included
                    currParty.path = self.magic_kingdom.shortest_paths[currParty.current_location][1][ride][1:]

                    #Grabs the next location and its distance       
                    next_location = currParty.path.pop(0)
                    currParty.next_location = next_location
                    distance = self.magic_kingdom.graph[currParty.current_location][next_location]["weight"]

                    #Calculate the time it will take based on slowest member
                    next_time = ceil(distance / speed) + self.time
                    
                    #Add a new event into the queue
                    self.events.put(PrioritizedItem(next_time, currParty))
                    
                    #Update the current people for both the old location and the next edge
                    oldLocation = currParty.current_location
                    self.points[oldLocation]["currPeople"] -= currParty.party_size
                    str1 = f"{oldLocation}/{next_location}"
                    str2 = f"{next_location}/{oldLocation}"
                    if str1 in self.edges:
                        self.edges[str1]["currPeople"] += currParty.party_size
                        currParty.current_location = str1
                    else:
                        self.edges[str2]["currPeople"] += currParty.party_size
                        currParty.current_location = str2

                    #Updates any other feature realted to the party    
                    currParty.walking_time += ceil(distance / speed)
                    currParty.action = "Walk"
                    currParty.get_satisfactions(ceil(distance / speed), 0, self.rain)

                elif currParty.action == "Walk":
                    #Update old location count and party's current location
                    self.edges[currParty.current_location]["currPeople"] -= currParty.party_size
                    currParty.current_location = currParty.next_location

                    if len(currParty.path) == 0:
                        currParty.action = "Ride"
                        self.points[currParty.current_location]["currPeople"] += currParty.party_size
                        self.events.put(PrioritizedItem(self.time, currParty))
                        continue

                    #Grabs the next location and its distance       
                    next_location = currParty.path.pop(0)
                    currParty.next_location = next_location
                    distance = self.magic_kingdom.graph[currParty.current_location][next_location]["weight"]

                    #Calculate the time it will take based on slowest member
                    next_time = ceil(distance / speed) + self.time

                    #Add a new event into the queue
                    self.events.put(PrioritizedItem(next_time, currParty))

                    #Update the current people for both the old location and the next edge
                    oldLocation = currParty.current_location
                    str1 = f"{oldLocation}/{next_location}"
                    str2 = f"{next_location}/{oldLocation}"
                    if str1 in self.edges:
                        self.edges[str1]["currPeople"] += currParty.party_size
                        currParty.current_location = str1
                    else:
                        self.edges[str2]["currPeople"] += currParty.party_size
                        currParty.current_location = str2

                    #Updates any other feature realted to the party    
                    currParty.walking_time += ceil(distance / speed)                    
                    currParty.get_satisfactions(ceil(distance / speed), 0, self.rain)
                    

                elif currParty.action == "Ride":
                    if currParty.current_location == "Main Gate":
                        currParty.action = "Going Home"
                        self.events.put(PrioritizedItem(self.time+1, currParty))
                        continue                        
                    
                    currParty.rides.append(currParty.current_location)
                    currParty.num_rides = len(currParty.rides)
                    currParty.unique_rides = len(Counter(currParty.rides))
                    wait_time = self.points[currParty.current_location]["waitTime"]

                    #This is the how long until the party's next decision as it will take on average 5 minutes to walk through queue, ride the ride,
                    #and exit even if the ride has 0 wait time
                    next_time = wait_time + 5 + self.time
                    currParty.wait_time += wait_time
                    currParty.action = "Decide" 
                    self.events.put(PrioritizedItem(next_time, currParty))
                    currParty.get_satisfactions(0, wait_time, self.rain)


                elif currParty.action == "Going Home":
                    self.points["Main Gate"]["currPeople"] -= currParty.party_size
                    currParty.action = "Resting"
                    self.events.put(PrioritizedItem(self.time+30, currParty))

                elif currParty.action == "Resting":
                    all_ready = True
                    for guest in currParty.guests:
                        guest.energy += 0.4
                        if guest.energy > 100:
                            guest.energy = 100
                        if guest.energy < 80:
                            all_ready = False
                    if all_ready:
                        currParty.action = "Going Back"
                        self.events.put(PrioritizedItem(self.time + 30, currParty))
                    else:
                        self.events.put(PrioritizedItem(self.time + 1, currParty))
                    currParty.get_satisfactions(0, 0, False)

                elif currParty.action == "Going Back":
                    currParty.action = "Decide"
                    self.points["Main Gate"]["currPeople"] += currParty.party_size  #Needs to be updated in the future, since it is technically incorrect
                    self.events.put(PrioritizedItem(self.time+30, currParty))

            self.update()
            self.time += 1
        print("done")

        guest_dict = {}
        party_dict = {}
        for party in self.parties:
            party_dict[party.guests[0].name] = {
                                                "rides": party.rides, 
                                                "walk": party.walking_time, 
                                                "wait": party.wait_time, 
                                                "num_guest": len(party.guests)}
            for guest in party.guests:
                guest_dict[guest.name] = guest.satisfaction_list


        combined_dict = {"points": self.points, "edges": self.edges}
        timestamp = datetime.now().strftime("%m_%d %H_%M")
        folder_path = f"Output/{thought}/{timestamp}"
        os.mkdir(folder_path)
        output_file = f"{folder_path}/Graph.json"
        output_file2 = f"{folder_path}/Guest.json"
        output_file3 = f"{folder_path}/Party.json"

        with open(output_file, 'w') as json_file:
            json.dump(combined_dict, json_file)

        with open(output_file2, 'w') as json_file:
            json.dump(guest_dict, json_file)

        with open(output_file3, 'w') as json_file:
            json.dump(party_dict, json_file)

        # Specify the destination zip file path
        zip_file_path = f"{folder_path}.zip"

        # Create a zip file
        shutil.make_archive(zip_file_path[:-4], 'zip', folder_path)

        shutil.rmtree(folder_path)
        return

    #Primiarly for the visualization and stats
    def update(self):
        for edge in self.edges:
            self.edges[edge]["peopleList"].append(self.edges[edge]["currPeople"])
        
        for point in self.points:
            self.points[point]["peopleList"].append(self.points[point]["currPeople"])
            if "waitTime" in self.points[point]:
                self.points[point]["waitTime"] = ceil(self.points[point]["currPeople"] / self.points[point]["throughput"])
                self.points[point]["waitList"].append(ceil(self.points[point]["currPeople"] / self.points[point]["throughput"]))

        for party in self.parties:
            for guest in party.guests:
                guest.satisfaction_list.append(guest.satisfaction)
    
    def update_events(self):
        newQueue = PriorityQueue()
        while self.events.qsize() > 0:
            event = self.events.get()
            priority = event.priority
            p = event.item

            if p.action in ["Resting", "Going Home", "Going Back"]:
                newQueue.put(PrioritizedItem(priority, p))

            #If the party is on the ride/in line for the ride
            elif p.action == "Decide" and priority != self.time:
                possible = p.can_ride(p.current_location)
                if possible or p.current_location == "Main Gate":
                    newQueue.put(PrioritizedItem(priority, p))
                else:
                    waitTimeRemaining = priority - self.time
                    p.wait_time -= waitTimeRemaining
                    removed_ride = p.rides.pop()
                    p.failed_rides.append(removed_ride)
                    p.num_rides = len(p.rides)
                    p.unique_rides = len(Counter(p.rides))
                    p.get_satisfactions(0, -waitTimeRemaining, self.rain)
                    newQueue.put(PrioritizedItem(self.time, p))
            
            elif p.action == "Decide":
                newQueue.put(PrioritizedItem(priority, p))

            elif p.action == "Ride":
                if not p.can_ride(p.current_location):
                    self.points[p.current_location]["currPeople"] -= p.party_size
                    p.action = "Decide"
                newQueue.put(PrioritizedItem(priority, p))
            
            elif p.action == "Walk":
                #If the party has is about to reach their destination
                if p.path == []:
                    if p.can_ride(p.next_location):
                        newQueue.put(PrioritizedItem(priority, p))
                    else:
                        self.edges[p.current_location]["currPeople"] -= p.party_size
                        p.current_location = p.next_location
                        self.points[p.current_location]["currPeople"] += p.party_size
                        p.action = "Decide"
                        newQueue.put(PrioritizedItem(priority, p))

                #If the party is planning on going to a ride that is open or leaving
                elif p.path[-1] == "Main Gate" or p.can_ride(p.path[-1]):
                    newQueue.put(PrioritizedItem(priority, p))

                #If the party is going to a now closed ride
                elif not p.can_ride(p.path[-1]):
                    p.path = []
                    p.action = "Decide"
                    self.edges[p.current_location]["currPeople"] -= p.party_size
                    p.current_location = p.next_location
                    self.points[p.current_location]["currPeople"] += p.party_size
                    newQueue.put(PrioritizedItem(self.time, p))

        return newQueue             
    
# knowledge_JSON = "knowledge.JSON"
# simulation = Simulation(knowledge_JSON)
# simulation.main("KBAI")

# knowledge_JSON = "knowledge.JSON"
# simulation = Simulation(knowledge_JSON)
# simulation.main("Random", [190])