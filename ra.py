from ba import BA
import random
from utils import Constraint
from collections import deque
from threading import Thread
import time

class RA(Thread):
    def __init__(self, type, id, rules, env):
        super(RA, self).__init__(name=type + str(id))
        self.type = type
        self.id = id
        self.name = self.type + str(self.id)
        self.rules = rules
        self.nb_courses = self.rules["ra_constraints"][self.type][id]["nb_courses"]
        self.bas = []
        self.build_intrinsic_constraints()
        self.mq = deque()
        self.CB = []

        # creating BAs for each course of the RA
        for course in range(self.nb_courses):
            # get random cell
            cell = env.grid[random.randint(0, rules["nb_days"]-1)][random.randint(0, rules["nb_rooms"]-1)][random.randint(0, rules["nb_time_slots"]-1)]
            # create ba in the random cell
            ba = BA(type, self, course, rules, cell, self.CI, [], deque(), env)
            # add BA to list of BAs of the RA
            self.bas.append(ba)
            # add BA to list of BAs in the cell
            cell.bas.append(ba)

        # set the BAs brothers
        for ba in self.bas:
            ba.brothers = [baj for baj in self.bas if baj != ba]

        # set the RA as alive
        self.alive = True

    # build the intrinsic constraints of the RA given the data from the test
    # different rules apply for different RA types: teachers vs students
    # teachers are constrained by the specific day and time
    # students are constraint by specific teacher and course number
    def build_intrinsic_constraints(self):
        self.CI = []

        if self.type == "T":
            for constr in self.rules["ra_constraints"][self.type][self.id]["constraints"]:
                c = Constraint(self.type, day=constr["day"],
                               time_slot=constr["time_slot"])
                self.CI.append(c)
        else:
            for constr in self.rules["ra_constraints"][self.type][self.id]["constraints"]:
                c = Constraint(self.type, course=constr["course"],
                               teacher=constr["teacher"])
                self.CI.append(c)

    # add constraints induced by other BAs - reservation constraints.
    # call all the BAs to modify their induced constraints
    def add_induced_constraint(self, c):
        self.CB.append(c)
        for ba in self.bas:
            ba.modify_induced_constraints(self.CB)

    # continually process the messages in the message queue to see if any mess about reservations from the BAs need to
    # be propagated to all brothers
    def process_messages(self):
        while self.mq:
            message = self.mq.popleft()
            # if message.type == 'partnership':
            #     self.partner = message.partner_of_cell
            if message.type == 'reservation':
                self.add_induced_constraint(Constraint("I", cell=message.partner_of_cell, owner=message.sender))

    # cycle for each RA
    # start BAs. Then continually process messages while alive
    def run(self):
        for ba in self.bas:
            ba.start()
        while self.alive:
            time.sleep(20)
            self.process_messages()