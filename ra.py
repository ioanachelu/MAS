from ba import BA
import random
from utils import Constraint
from collections import deque
from threading import Thread
import time
import copy

class RA():
    def __init__(self, type, id, rules, env):
        # super(RA, self).__init__(name=type + str(id))
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
            ba = BA(type, self, course, rules, cell, self.copy_constraints(self.CI), [], deque(), env)
            # add BA to list of BAs of the RA
            self.bas.append(ba)
            # add BA to list of BAs in the cell
            cell.bas.append(ba)

        # set the BAs brothers
        for ba in self.bas:
            ba.brothers = [baj for baj in self.bas if baj != ba]

        # set the RA as alive
        self.alive = True

    def copy_constraints(self, CI):
        new_CI = []
        for c in CI:
            new_CI.append(copy.deepcopy(c))
        return new_CI

    # build the intrinsic constraints of the RA given the data from the test
    # different rules apply for different RA types: teachers vs students
    # teachers are constrained by the specific day and time
    # students are constraint by specific teacher and course number
    def build_intrinsic_constraints(self):
        self.CI = []

        if self.type == "T":
            for constr in self.rules["ra_constraints"][self.type][self.id]["constraints"]:
                c = Constraint(self.type, day=constr["day"],
                               time_slot=constr["time_slot"],
                               teacher=constr["teacher"])
                self.CI.append(c)
        else:
            for constr in self.rules["ra_constraints"][self.type][self.id]["constraints"]:
                c = Constraint(self.type, tc_avail=constr["T_courses_availability"])
                self.CI.append(c)

    # add constraints induced by other BAs - reservation constraints.
    # call all the BAs to modify their induced constraints
    def add_induced_constraint(self, c):
        self.CB.append(c)
        for ba in self.bas:
            ba.modify_induced_constraints(self.CB)

    def remove_induced_constraint(self, type, owner):
        for constr in self.CB:
            if constr.type == type and constr.owner_name and constr.owner_name == owner:
                self.CB.remove(constr)
                return

    # continually process the messages in the message queue to see if any mess about reservations from the BAs need to
    # be propagated to all brothers
    def process_messages(self):
        while self.mq:
            message = self.mq.popleft()
            if message.type == 'partnership':
                if self.type == 'SG' and message.sender.type == 'SG':
                    sg = message.sender
                    t = message.partner_of_cell
                    print(
                        "RA {} received partnership message from sg {} about adding constraint from teacher {}".format(
                            self.name, sg.name, t.ra_id))
                    self.add_induced_constraint(Constraint("B", teacher=t.ra_id, owner_name=sg.name))
            if message.type == 'partnership_cancelation':
                if self.type == 'SG' and message.sender.type == 'SG':
                    sg = message.sender
                    t = message.partner_of_cell
                    print(
                        "RA {} received partnership cancelation message from sg {} about removing constraint from teacher {}".format(
                            self.name, sg.name, t.ra_id))
                    self.remove_induced_constraint("B", sg.name)
            if message.type == 'reservation':
                print(
                    "RA {} received reservation message from {} about reserving cell DAY {} TIME {} ROOM {}".format(
                        self.name, message.sender.name, message.partner_of_cell.day, message.partner_of_cell.time_slot,
                        message.partner_of_cell.room))
                self.add_induced_constraint(Constraint("I", cell=message.partner_of_cell, owner_name=message.sender.name, owner=message.sender))
            if message.type == 'reservation_cancelation':
                print(
                    "RA {} received reservation cancelation message from {}".format(
                        self.name, message.sender.name))
                self.remove_induced_constraint("I", message.sender.name)

    # cycle for each RA
    # start BAs. Then continually process messages while alive
    def perceive(self):
        self.process_messages()