from ra import RA
from collections import deque
import time
import threading

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


    # def get_queues(self):
    #     for ba in self.all_bas:
    #         self.ba_mqs.append(ba.mq)


    def build_grid(self):
        self.grid = []
        for day in range(self.rules["nb_days"]):
            self.grid.append([])
            for room in range(self.rules["nb_rooms"]):
                self.grid[-1].append([])
                for time_slot in range(self.rules["nb_time_slots"]):
                    c = Cell(day, room, time_slot, self.rules)
                    self.grid[-1][-1].append(c)

    def start(self):
        for ra in self.all_ras:
            ra.start()
        while(1):
            time.sleep(10)
            self.print_info()
            booked = 0
            for day in range(self.rules["nb_days"]):
                for room in range(self.rules["nb_rooms"]):
                    for time_slot in range(self.rules["nb_time_slots"]):
                        cell = self.get_cell([day, room, time_slot])
                        if cell.reservation is not None and cell.reservation.partner is not None:
                            booked += 1
            if booked == self.rules["occupancy"]:
                exit(0)

    def print_pawns(self):
        table_header = ">" * (5 + 2 + (35 + 2 + 8) * self.rules["nb_time_slots"])
        table_footer = "<" * (5 + 2 + (35 + 2 + 8) * self.rules["nb_time_slots"])
        print(bcolors.WARNING + table_header + bcolors.ENDC)
        for day in range(self.rules["nb_days"]):
            line = '-' * (5 + 2 + (35 + 2 + 8) * self.rules["nb_time_slots"])
            double_line = '=' * (5 + 2 + (35 + 2 + 8) * self.rules["nb_time_slots"])
            anchor = ' ' * int((5 + 2 + (35 + 2 + 8) * self.rules["nb_time_slots"] - 7) / 2 - 2)
            print(double_line)
            print(('||' + anchor + " DAY {} " + anchor + '||').format(day))
            print(double_line)
            info_grid = []
            info_rez = []
            for room in range(self.rules["nb_rooms"]):
                info_grid.append([])
                info_rez.append([])
                for time_slot in range(self.rules["nb_time_slots"]):
                    cell = self.get_cell([day, room, time_slot])
                    if len(cell.bas) == 0:
                        info_grid[-1].append("  ")
                    else:
                        info_grid[-1].append(", ".join([ba.name for ba in cell.bas]))

                    if cell.reservation:
                        if cell.reservation.partner is not None:
                            info_rez[-1].append(cell.reservation.name + "/" + cell.reservation.partner.name)
                        else:
                            info_rez[-1].append(cell.reservation.name + "/None")
                    else:
                        info_rez[-1].append("None/None")

            header = "|R / T|"
            for i in range(self.rules["nb_time_slots"]):
                header += "|                     {}                     |".format(i)
            print(header)
            print(line)

            for room, time_slots in enumerate(info_grid):
                row = "|  {}  |".format(room)
                for t in time_slots:
                    row += "|{}|".format(t.ljust(35 + 8))
                print(row)

                row_rez = "|  {}  |".format(room)
                for t in info_rez[room]:
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

    def print_info(self):
        self.print_pawns()
        # self.print_board()

    def get_cell(self, directions):
        return self.grid[directions[0]][directions[1]][directions[2]]


class Cell():
    lock = threading.RLock()

    def __init__(self, day, room, time_slot, rules):
        self.day = day
        self.room = room
        self.time_slot = time_slot
        self.rules = rules
        self.C = []
        self.bas = []
        self.reservation = None

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







