from ra import RA
from collections import deque
import time
import threading
from utils import Constraint

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
                print("BA {} acted".format(ba.name))
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

    def print_pawns(self, time):
        double_line = '=' * (5 + 1 + (35 + 2 + 8) * self.rules["nb_rooms"])
        anchor = ' ' * int((5 + 1 + (35 + 2 + 8) * self.rules["nb_rooms"] - 7) / 2 - 2)
        print(double_line)
        print(('||' + anchor + " TIME {} " + anchor + '||').format(time))
        print(double_line)
        time_slot_encoder = [" 8-10", "10-12", "14-16", "16–18"]
        table_header = ">" * (5 + 2 + (35 + 2 + 8) * self.rules["nb_rooms"])
        table_footer = "<" * (5 + 2 + (35 + 2 + 8) * self.rules["nb_rooms"])
        print(bcolors.WARNING + table_header + bcolors.ENDC)
        for day in range(self.rules["nb_days"]):
            line = '-' * (5 + 2 + (35 + 2 + 8) * self.rules["nb_rooms"])
            double_line = '=' * (5 + 2 + (35 + 2 + 8) * self.rules["nb_rooms"])
            anchor = ' ' * int((5 + 2 + (35 + 2 + 8) * self.rules["nb_rooms"] - 7) / 2 - 2)
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

                    if cell.reservation:
                        if cell.reservation.partner:
                            info_rez[-1].append(cell.reservation.name + "/" + cell.reservation.partnership.name)
                        else:
                            info_rez[-1].append(cell.reservation.name + "/None")
                    else:
                        info_rez[-1].append("None/None")

            header = "|T / R|"
            for i in range(self.rules["nb_rooms"]):
                header += "|                     {}                     |".format(i)
            print(header)
            print(line)

            for time_slot, rooms in enumerate(info_grid):
                row = "|{}|".format(time_slot_encoder[time_slot])
                for t in rooms:
                    row += "|{}|".format(t.ljust(35 + 8))
                print(row)

                row_rez = "|{}|".format(time_slot_encoder[time_slot])
                for t in info_rez[time_slot]:
                    row_rez += "|{}|".format(t.ljust(35 + 8))
                print(bcolors.OKBLUE + row_rez + bcolors.ENDC)
                print(line)
                # print("--- ROOM {} ---".format(room))
                # for time_slot in range(self.rules["nb_time_slots"]):
                #     print("+ {} +".format(time_slot))
                #     cell = self.get_cell([day, room, time_slot])
                #     for ba in cell.bas:
                #         print(ba.name)
        print(bcolors.WARNING + table_footer + bcolors.ENDC)

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
        double_line = '=' * (5 + 1 + (35 + 2 + 8) * self.rules["nb_time_slots"])
        anchor = ' ' * int((5 + 1 + (35 + 2 + 8) * self.rules["nb_time_slots"] - 7) / 2 - 2)
        print(bcolors.FAIL + double_line + bcolors.ENDC)
        print(bcolors.FAIL + ('||' + anchor + " BOOK {} " + anchor + '||').format(booked) + bcolors.ENDC)
        print(bcolors.FAIL + double_line + bcolors.ENDC)
        if booked == self.rules["occupancy"]:
            self.print_solution()
            exit(0)

        # self.print_board()

    def get_cell(self, directions):
        return self.grid[directions[0]][directions[1]][directions[2]]

    def print_solution(self):
        double_line = '=' * (5 + 1 + (35 + 2 + 8) * self.rules["nb_rooms"])
        anchor = ' ' * int((5 + 1 + (35 + 2 + 8) * self.rules["nb_rooms"] - 7) / 2 - 2)
        print(double_line)
        print(('||' + anchor + " SOLUTION " + anchor + '||'))
        print(double_line)
        time_slot_encoder = [" 8-10", "10-12", "14-16", "16–18"]
        table_header = ">" * (5 + 2 + (35 + 2 + 8) * self.rules["nb_rooms"])
        table_footer = "<" * (5 + 2 + (35 + 2 + 8) * self.rules["nb_rooms"])
        print(bcolors.OKGREEN + table_header + bcolors.ENDC)
        for day in range(self.rules["nb_days"]):
            line = '-' * (5 + 2 + (35 + 2 + 8) * self.rules["nb_rooms"])
            double_line = '=' * (5 + 2 + (35 + 2 + 8) * self.rules["nb_rooms"])
            anchor = ' ' * int((5 + 2 + (35 + 2 + 8) * self.rules["nb_rooms"] - 7) / 2 - 2)
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
                    if cell.reservation:
                        one = cell.reservation.type + str(cell.reservation.ra_id + 1)
                        if cell.reservation.partner:
                            two = cell.reservation.partnership.type + str(cell.reservation.partnership.ra_id + 1)
                            info_rez[-1].append(one + "/" + two)
                        else:
                            info_rez[-1].append(one + "/None")
                    else:
                        info_rez[-1].append("None/None")

            header = "|T / R|"
            for i in range(self.rules["nb_rooms"]):
                header += "|                     {}                     |".format(i)
            print(header)
            print(line)

            for time_slot, rooms in enumerate(info_grid):
                row_rez = "|{}|".format(time_slot_encoder[time_slot])
                for t in info_rez[time_slot]:
                    row_rez += "|{}|".format(t.ljust(35 + 8))
                print(bcolors.FAIL + row_rez + bcolors.ENDC)
                print(line)
                # print("--- ROOM {} ---".format(room))
                # for time_slot in range(self.rules["nb_time_slots"]):
                #     print("+ {} +".format(time_slot))
                #     cell = self.get_cell([day, room, time_slot])
                #     for ba in cell.bas:
                #         print(ba.name)
        print(bcolors.OKGREEN + table_footer + bcolors.ENDC)

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
            c = Constraint("U", day=constr["day"],
                           time_slot=constr["time_slot"],
                           teacher=constr["room"], weight=2)
            self.C.append(c)

    def set_tools_constraints(self):
        for constr in self.rules["cell_constraints"]["tools_availability"]:
            if self.room == constr["room"]:
                c = Constraint("A", day=self.day,
                               time_slot=self.time_slot,
                               room=constr["room"], tools=constr["tools"], weight=2)
                self.C.append(c)








