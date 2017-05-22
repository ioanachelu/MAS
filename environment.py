from ra import RA
from ba import BA
from collections import deque
import time
import threading
from utils import Constraint
import itertools

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Environment():

    def __init__(self, rules):
        self.lock = threading.RLock()
        self.rules = rules
        self.build_grid()
        self.all_bas = []
        self.ras = {"T": [], "SG": []}
        for teacher in range(rules["nb_teachers"]):
            self.ras["T"].append(RA("T", teacher, rules, self))
            self.all_bas.extend(self.ras["T"][-1].bas)

        for st_group in range(rules["nb_st_groups"]):
            self.ras["SG"].append(RA("SG", st_group, rules, self))
            self.all_bas.extend(self.ras["SG"][-1].bas)

        # self.step_count = 0
        self.all_ras = self.ras["T"] + self.ras["SG"]

    def build_grid(self):
        self.grid = []
        for day in range(self.rules["nb_days"]):
            self.grid.append([])
            for room in range(self.rules["nb_rooms"]):
                self.grid[-1].append([])
                for time_slot in range(self.rules["nb_time_slots"]):
                    c = Cell(day, room, time_slot, self.rules)
                    self.grid[-1][-1].append(c)

    def set_relax(self):
        for ba in self.all_bas:
            ba.relax = bool(self.rules["relax"])


    def step(self):
        time = 0
        self.print_info(time)
        while True:
            for ba in self.all_bas:
                ba.step()
                # rez = ba.test_deadlock()
                # if not rez:
                #     print("DEADLOCK")
                #     exit(0)
                print("[Info] BA {} acted".format(ba.name))
                self.perceive_cycle()
                self.print_info(time)
            time += 1

    def perceive_cycle(self):
        for i in range(2):
            for baj in self.all_bas:
                baj.perceive()
            for ra in self.all_ras:
                ra.perceive()
    # def start(self):
    #     for ra in self.all_ras:
    #         ra.start()
    #     while(1):
    #         time.sleep(10)
    #         self.print_info()
    #         booked = 0
    #         for day in range(self.rules["nb_days"]):
    #             for room in range(self.rules["nb_rooms"]):
    #                 for time_slot in range(self.rules["nb_time_slots"]):
    #                     cell = self.get_cell([day, room, time_slot])
    #                     if cell.reservation is not None and cell.reservation.partner:
    #                         booked += 1
    #         if booked == self.rules["occupancy"]:
    #             exit(0)
    def print_violated_constraint(self, v):
        if v.type == "R":
            text = "Constraint {} ".format(v.type)
        else:
            text = "Constraint {} owner: {} ".format(v.type, v.owner.name)
        if v.type == "T":
            text += "teacher: {} day: {} time_slot: {} ".format(v.teacher, v.day,
                               v.time_slot)
        if v.type == "SG":
            text += "teacher course availability {} ".format(v.tc_avail)

        if v.type == "U" or v.type == "R":
            text += "cell day: {}, room: {}, time_slot: {}".format(v.day, v.room, v.time_slot)

        print(bcolors.OKBLUE + text + bcolors.ENDC)

    def calc_occupancy(self):
        occupancy = 0
        for teacher in range(self.rules["nb_teachers"]):
            occupancy += self.rules['ra_constraints']["T"][str(teacher)]["nb_courses"]

        return occupancy

    def print_violated_constraints(self, vc):
        table_header = ">" * (5 + 2 + (53 + 2) * self.rules["nb_rooms"])
        anchor = '^' * int((5 + 1 + (53 + 2) * self.rules["nb_rooms"] - 20) / 2 - 2)
        print(('||' + anchor + " Violated Constraints" + anchor + '||').format(time))
        table_footer = "<" * (5 + 2 + (53 + 2) * self.rules["nb_rooms"])
        print(bcolors.BOLD + table_header + bcolors.ENDC)
        for v in vc:
            self.print_violated_constraint(v)
        print(bcolors.BOLD + table_footer + bcolors.ENDC)

    def print_pawns(self, time):
        total_violated_constraints = []
        double_line = '=' * (5 + 1 + (53 + 2) * self.rules["nb_rooms"])
        anchor = ' ' * int((5 + 1 + (53 + 2) * self.rules["nb_rooms"] - 7) / 2 - 2)
        print(double_line)
        print(('||' + anchor + " TIME {} " + anchor + '||').format(time))
        print(double_line)
        time_slot_encoder = [" 8-10", "10-12", "14-16", "16–18"]
        table_header = ">" * (5 + 2 + (53 + 2) * self.rules["nb_rooms"])
        table_footer = "<" * (5 + 2 + (53 + 2) * self.rules["nb_rooms"])
        print(bcolors.WARNING + table_header + bcolors.ENDC)
        for day in range(self.rules["nb_days"]):
            line = '-' * (5 + 2 + (53 + 2) * self.rules["nb_rooms"])
            double_line = '=' * (5 + 2 + (53 + 2) * self.rules["nb_rooms"])
            anchor = ' ' * int((5 + 2 + (53 + 2) * self.rules["nb_rooms"] - 7) / 2 - 2)
            print(double_line)
            print(('||' + anchor + " DAY {} " + anchor + '||').format(day))
            print(double_line)
            info_grid = []
            info_rez = []
            for time_slot in range(self.rules["nb_time_slots"]):
                info_grid.append([])
                info_rez.append([])
                for room in range(self.rules["nb_rooms"]):
                    cell = self.get_cell([day, room, time_slot])
                    if len(cell.bas) == 0:
                        info_grid[-1].append("  ")
                    else:
                        info_bas = []
                        for ba in cell.bas:
                            ba_info = ba.name
                            ba_info += "("
                            if ba.partner:
                                ba_info += 't'
                            else:
                                ba_info += "f"
                            ba_info += "/"
                            if ba.reservation:
                                ba_info += 't'
                            else:
                                ba_info += "f"
                            ba_info += ")"
                            info_bas.append(ba_info)

                        info_grid[-1].append(", ".join(info_bas))
                        #info_grid[-1].append(", ".join([ba.name for ba in cell.bas]))

                    text = ""
                    violated_constraints = []

                    if cell.reservation:
                        one = cell.reservation.name
                        violated_constraints.append(BA.NC_cell(cell.reservation, cell))

                        if cell.reservation.partner:
                            two = cell.reservation.partnership.name
                            # info_rez[-1].append(cell.reservation.name + "/" + cell.reservation.partnership.name)
                            text += one + "/" + two
                            violated_constraints.append(BA.NC_ba(cell.reservation, cell.reservation.partnership))
                        else:
                            # info_rez[-1].append(cell.reservation.name + "/None")
                            text += one + "/None"
                    else:
                        # info_rez[-1].append("None/None")
                        text += "None/None"

                    violated_constraints = list(set(itertools.chain(*violated_constraints)))
                    violated_constraints = [v for v in violated_constraints if v.type != "I"]
                    total_violated_constraints.extend(violated_constraints)
                    vc = len(violated_constraints)

                    if vc == 0:
                        info_rez[-1].append(bcolors.OKBLUE + text + bcolors.ENDC)
                    else:
                        info_rez[-1].append(bcolors.FAIL + text + bcolors.ENDC)

            header = "|T / R|"
            for i in range(self.rules["nb_rooms"]):
                header += "|                          {}                          |".format(i)
            print(header)
            print(line)

            for time_slot, rooms in enumerate(info_grid):
                row = "|{}|".format(time_slot_encoder[time_slot])
                for t in rooms:
                    row += "|{}|".format(t.ljust(53))
                print(row)

                row_rez = bcolors.OKBLUE + "|{}|".format(time_slot_encoder[time_slot]) + bcolors.ENDC
                for t in info_rez[time_slot]:
                    row_rez += "|{}|".format(t.ljust(53 + 9))
                print(row_rez)
                print(line)
                # print("--- ROOM {} ---".format(room))
                # for time_slot in range(self.rules["nb_time_slots"]):
                #     print("+ {} +".format(time_slot))
                #     cell = self.get_cell([day, room, time_slot])
                #     for ba in cell.bas:
                #         print(ba.name)
        print(bcolors.WARNING + table_footer + bcolors.ENDC)
        if len(total_violated_constraints) != 0:
            self.print_violated_constraints(total_violated_constraints)

    def print_board(self):
        pass

    def print_info(self, time):
        self.print_pawns(time)
        booked = 0
        for day in range(self.rules["nb_days"]):
            for room in range(self.rules["nb_rooms"]):
                for time_slot in range(self.rules["nb_time_slots"]):
                    cell = self.get_cell([day, room, time_slot])
                    if cell.reservation is not None and cell.reservation.partner:
                        booked += 1
        double_line = '=' * (5 + 1 + (53 + 2) * self.rules["nb_rooms"])
        anchor = ' ' * int((5 + 1 + (53 + 2) * self.rules["nb_rooms"] - 7) / 2 - 2)
        print(bcolors.FAIL + double_line + bcolors.ENDC)
        print(bcolors.FAIL + ('||' + anchor + " BOOK {} " + anchor + '||').format(booked) + bcolors.ENDC)
        print(bcolors.FAIL + double_line + bcolors.ENDC)
        if booked == self.calc_occupancy():
            violated_constraints = self.print_solution()
            return violated_constraints
        return -1
            # exit(0)

        # self.print_board()

    def get_cell(self, directions):
        return self.grid[directions[0]][directions[1]][directions[2]]

    def print_solution(self):
        total_violated_constraints = 0
        double_line = '=' * (5 + 1 + (53 + 2) * self.rules["nb_rooms"])
        anchor = ' ' * int((5 + 1 + (53 + 2) * self.rules["nb_rooms"] - 7) / 2 - 2)
        print(double_line)
        print(('||' + anchor + " SOLUTION " + anchor + '||'))
        print(double_line)
        time_slot_encoder = [" 8-10", "10-12", "14-16", "16–18"]
        table_header = ">" * (5 + 2 + (53 + 2) * self.rules["nb_rooms"])
        table_footer = "<" * (5 + 2 + (53 + 2) * self.rules["nb_rooms"])
        print(bcolors.OKGREEN + table_header + bcolors.ENDC)
        for day in range(self.rules["nb_days"]):
            line = '-' * (5 + 2 + (53 + 2) * self.rules["nb_rooms"])
            double_line = '=' * (5 + 2 + (53 + 2) * self.rules["nb_rooms"])
            anchor = ' ' * int((5 + 2 + (53 + 2) * self.rules["nb_rooms"] - 7) / 2 - 2)
            print(double_line)
            print(('||' + anchor + " DAY {} " + anchor + '||').format(day))
            print(double_line)
            info_grid = []
            info_rez = []
            for time_slot in range(self.rules["nb_time_slots"]):
                info_grid.append([])
                info_rez.append([])
                for room in range(self.rules["nb_rooms"]):
                    violated_constraints = []
                    cell = self.get_cell([day, room, time_slot])
                    text = ""

                    if cell.reservation:
                        violated_constraints.append(BA.NC_cell(cell.reservation, cell))
                        one = cell.reservation.type + str(cell.reservation.ra_id + 1)
                        # violated_constraints += len(BA.NC_cell(cell.reservation, cell))
                        if cell.reservation.partner:
                            two = cell.reservation.partnership.type + str(cell.reservation.partnership.ra_id + 1)
                            # info_rez[-1].append(one + "/" + two)
                            text += one + "/" + two
                            violated_constraints.append((BA.NC_ba(cell.reservation, cell.reservation.partnership)))
                        else:
                            # info_rez[-1].append(one + "/None")
                            text += one + "/None"
                    else:
                        # info_rez[-1].append("None/None")
                        text += "None/None"
                    violated_constraints = list(set(itertools.chain(*violated_constraints)))
                    violated_constraints = [v for v in violated_constraints if v.type != "I"]
                    vc = len(violated_constraints)

                    if vc == 0:
                        info_rez[-1].append(bcolors.OKGREEN + text + bcolors.ENDC)
                    else:
                        info_rez[-1].append(bcolors.FAIL + text + "({})".format(vc) + bcolors.ENDC)
                    total_violated_constraints += vc

            header = "|T / R|"
            for i in range(self.rules["nb_rooms"]):
                header += "|                     {}                     |".format(i)
            print(header)
            print(line)

            for time_slot, rooms in enumerate(info_grid):
                row_rez = "|{}|".format(time_slot_encoder[time_slot])
                for t in info_rez[time_slot]:
                    row_rez += "|{}|".format(t.ljust(53))
                print(row_rez)
                print(line)
                # print("--- ROOM {} ---".format(room))
                # for time_slot in range(self.rules["nb_time_slots"]):
                #     print("+ {} +".format(time_slot))
                #     cell = self.get_cell([day, room, time_slot])
                #     for ba in cell.bas:
                #         print(ba.name)
        print(bcolors.OKGREEN + table_footer + bcolors.ENDC)

        return total_violated_constraints

    def remove_cell_unavailability_constraint(self, con):
        for day in range(self.rules["nb_days"]):
            for room in range(self.rules["nb_rooms"]):
                for time_slot in range(self.rules["nb_time_slots"]):
                    if con["day"] == day and con["time_slot"] == time_slot and con["room"] == room:
                        cell = self.get_cell([day, room, time_slot])
                        cell.remove_cell_unavailability_constraint()

    def add_cell_constraint(self, con):
        for day in range(self.rules["nb_days"]):
            for room in range(self.rules["nb_rooms"]):
                for time_slot in range(self.rules["nb_time_slots"]):
                    if con["day"] == day and con["time_slot"] == time_slot and con["room"] == room:
                        cell = self.get_cell([day, room, time_slot])
                        cell.add_cell_unavailability_constraint(con)

class Cell():
    lock = threading.RLock()

    def __init__(self, day, room, time_slot, rules):
        self.day = day
        self.room = room
        self.time_slot = time_slot
        self.rules = rules
        self.C = [Constraint("R", day=day, time_slot=time_slot, room=room)]
        self.bas = []
        self.reservation = None
        self.set_unavailability_constraints()
        self.set_tools_constraints()
        self.f = open("messages.txt", "a")

    def set_reservation(self, new_value):
        with self.lock:
            self.reservation = new_value

    def move_ba_here(self, ba):
        with self.lock:
            self.bas.append(ba)

    def remove_ba_from_here(self, ba):
        with self.lock:
            self.bas.remove(ba)

    def get_bas(self):
        return self.bas

    def set_unavailability_constraints(self):
        for constr in self.rules["cell_constraints"]["unavailability"]:
            if constr["day"] == self.day and \
                    constr["time_slot"] == self.time_slot and \
                    constr["room"] == self.room:
                c = Constraint("U", day=constr["day"],
                               time_slot=constr["time_slot"],
                               teacher=constr["room"], weight=1)
                self.C.append(c)

    def set_tools_constraints(self):
        for constr in self.rules["cell_constraints"]["tools_availability"]:
            if self.room == constr["room"]:
                c = Constraint("A", day=self.day,
                               time_slot=self.time_slot,
                               room=constr["room"], tools=constr["tools"], weight=1)
                self.C.append(c)

    def remove_cell_unavailability_constraint(self):
        for c in self.C:
            if c.type == "U":
                self.C.remove(c)


    def add_cell_unavailability_constraint(self, constr):
        c = Constraint("U", day=constr["day"],
                       time_slot=constr["time_slot"],
                       teacher=constr["room"], weight=1)

        self.C.append(c)












