import random
import copy
from threading import Thread
from utils import Message
import time
import threading

class BA(Thread):
    lock = threading.RLock()
    def __init__(self, type, ra, id, rules, cell, CI, CB, mq, env):
        super(BA, self).__init__(name=type + str(ra.id) + str(id))
        self.type = type
        self.ra_id = ra.id
        self.proxy = ra
        self.id = id
        self.rules = rules
        self.name = self.type + str(self.ra_id) + "_" + str(self.id)
        # current cell the agent is in
        self.cell = cell
        # current partner
        self.partner = None
        # current reservation cell
        self.rCell = None
        # time passed since no reservation
        self.time = 1
        # the list of agents - BA this one knows
        self.knows = []
        # the list of intrinsic constraints from the RA
        self.CI = CI
        # the list of constraints induced by this guy's brothers
        self.CB = CB
        # the list of constraints induced by this guy's partner
        self.CP = []
        # the list of constraints induced by the current reservation
        self.CR = []
        # the message queue
        self.mq = mq
        # the list of known cells. Starts with the cell the agent is first positioned
        self.knownCells = [cell]
        # a copy of the environment. Needs to be handled with care. Should not use almost anything
        self.env = env
        # start off being alive
        self.alive = True
        # the list of brothers this guy has
        self.brothers = []
        # whether this guy just woke up. This is very yacky..:(
        self.just_woke_up = True

    def modify_induced_constraints(self, CB):
        with self.lock:
            self.CB = CB

    def get_induced_constraints(self):
        with self.lock:
            return self.CB

    # when you've got mail
    def process_messages(self):
        while self.mq:
            message = self.mq.popleft()
            # if somebody wants to partner than my partner goals should be acomplished
            if message.type == 'partnership':
                self.partner = message.partner_of_cell
                if self.partner.rCell is not None:
                    self.rCell.set_reservation(None)
                else:
                    self.time = 1
                self.rCell = self.partner.rCell
            if message.type == 'reservation':
                self.rCell = message.partner_of_cell


    def get_next_cell(self):
        day = self.cell.day
        room = self.cell.room
        time_slot = self.cell.time_slot
        directions = [day, room, time_slot]
        up_down = [1, -1]
        directions_end = [self.rules["nb_days"], self.rules["nb_rooms"], self.rules["nb_time_slots"]]

        while True:
            choose_direction = random.randint(0, 2)
            choose_up_down = random.randint(0, 1)

            if directions[choose_direction] + up_down[choose_up_down] > 0 and \
                directions[choose_direction] + up_down[choose_up_down] < directions_end[choose_direction]:

                new_directions = directions[:]
                new_directions[choose_direction] += up_down[choose_up_down]
                next_cell = self.env.get_cell(new_directions)

                return next_cell

    def move_to(self, cell):
        if cell == self.cell:
            return
        else:
            self.knownCells.append(cell)
            self.cell.remove_ba_from_here(self)
            cell.bas.append(self)
            self.cell = cell
            self.time += 1


    def inform_ba_of_partnership(self, baj):
        m = Message("partnership", self)
        baj.mq.append(m)

    def inform_proxy_of_partnership(self, ra):
        m = Message("partnership", self.partner, self)
        ra.mq.append(m)

    def inform_proxy_of_cell_reservation(self, ra):
        m = Message("reservation", self.rCell, self)
        ra.mq.append(m)

    def inform_ba_of_cell_reservation(self, baj):
        m = Message("reservation", self.rCell)
        baj.mq.append(m)

    def partner_with(self, baj):
        self.partner = baj
        self.inform_ba_of_partnership(baj)
        self.inform_proxy_of_partnership(self.proxy)

    def reserve_crt_cell(self):
        if self.cell.reservation is not None:
            self.cell.reservation.rCell = None

            # TODO inform him I have stolen the reservation
            self.cell.reservation.time = 1
            if self.cell.reservation.partner is not None:
                print("{} stole the reservation of cell: day-{} room-{} time-{} from {} and {}".format(self.name,
                                                                                                       self.cell.day,
                                                                                                       self.cell.room,
                                                                                                       self.cell.time_slot,
                                                                                                       self.cell.reservation.name,
                                                                                                       self.cell.reservation.partner.name))
                self.cell.reservation.partner.rCell = None
                # TODO inform him I have stolen the reservation
                self.cell.reservation.partner.time = 1
            else:
                print("{} stole the reservation of cell: day-{} room-{} time-{} from {} and {}".format(self.name,
                                                                                                       self.cell.day,
                                                                                                       self.cell.room,
                                                                                                       self.cell.time_slot,
                                                                                                       self.cell.reservation.name,
                                                                                                       None))

        if self.rCell is not None:
            self.rCell.set_reservation(None)

        self.rCell = self.cell
        self.cell.set_reservation(self)
        if self.partner is not None:
            self.inform_ba_of_cell_reservation(self.partner)
        self.inform_proxy_of_cell_reservation(self.proxy)
        self.time = 1

    def process_crt_cell(self):
        for baj in self.eligible_bas:
            if baj in self.brothers:
                return
            #partnership incompetence
            if not BA.compatible(self, baj) or (self.partner is not None and BA.pCost(self, baj) >= BA.pCost(self, self.partner)):
                self.knows.extend(baj.knows)
                continue
            if BA.compatible(self, baj) and baj.partner != self and (self.partner is None or BA.pCost(self, baj) < BA.pCost(self, self.partner)):
                self.partner_with(baj)
                break

        if BA.compatible_cell(self, self.cell) and self.rCell is None and self.cell.reservation is None:
            self.reserve_crt_cell()

        if BA.compatible_cell(self, self.cell) and \
                (((self.rCell is not None) and self.cell != self.rCell and (BA.rCost(self, self.cell) < BA.rCost(self, self.rCell)))):
            self.reserve_crt_cell()




    def add_bas_to_memory(self):
        bas_in_cell = [ba for ba in self.cell.get_bas() if ba != self]
        for ba in bas_in_cell:
            if ba not in self.knows:
                self.knows.append(ba)
                for bak in ba.knows:
                    if bak not in self.knows:
                        self.knows.append(bak)


        self.eligible_bas = bas_in_cell


    def process_encountered_bas(self):
        pruned_eligible_bas = []
        for baj in self.eligible_bas:
            if not BA.NC_ba(self, baj) and (not self.rCell or not BA.NC_cell(baj, self.rCell)):
                pruned_eligible_bas.append(baj)

        self.eligible_bas = pruned_eligible_bas


    def run(self):
        while self.alive:
            time.sleep(10)
            if self.just_woke_up:
                self.add_bas_to_memory()  # analyse bas which are in the cell
                self.process_encountered_bas()  # verify whether they fit with constraints
                if self.rCell is None or self.partner is None:
                    self.process_crt_cell()
                self.just_woke_up = False
            else:
                self.process_messages()
                if self.partner is not None and self.rCell is not None:
                    if BA.rCost(self, self.rCell) == 0:
                        self.move_to(self.rCell)
                    else:
                        self.process_crt_cell() #analyse cell to find either partner or reservation
                else:
                    while True:
                        next_cell = self.get_next_cell()
                        if next_cell not in self.knownCells:
                            self.move_to(next_cell)
                            break
                    self.add_bas_to_memory() #analyse bas which are in the cell
                    self.process_encountered_bas() #verify whether they fit with constraints
                    if self.rCell is None or self.partner is None:
                        self.process_crt_cell()


    @staticmethod
    def compatible_cell(bai, cj):
        return len(BA.NC_cell(bai, cj)) == 0

    @staticmethod
    def compatible(bai, baj):
        return bai.type != baj.type and len(BA.NC_ba(bai, baj)) == 0

    @staticmethod
    def NC_ba(bai, baj):
         return BA.nonCompatible(bai.CI + bai.get_induced_constraints() + bai.CR, baj.CI + baj.get_induced_constraints() + baj.CR)

    @staticmethod
    def NC_cell(bai, cj):
        if cj is None:
            return None
        return BA.nonCompatible(bai.CI + bai.get_induced_constraints() + bai.CP, cj.C)

    @staticmethod
    def rCost(bai, cj):
        cost = 0
        for c in BA.NC_cell(bai, cj):
            cost += c.weight
        return cost / bai.time

    @staticmethod
    def pCost(bai, bj):
        cost = 0
        for c in BA.NC_ba(bai, bj):
            cost += c.weight
        return cost

    @staticmethod
    def nonCompatible(Ci, Cj):
        non_c = [c for c in Ci if BA.nonCompatible_constraint_with_set(c, Cj)]
        return non_c

    @staticmethod
    def nonCompatible_constraint_with_set(c, Cj):
        res = []
        for cc in Cj:
            if BA.nonCompatible_constraints(c, cc):
                res.append(c)
                break

        return res

    @staticmethod
    def nonCompatible_constraints(c, cc):
        if c.type == "T" and cc.type == "T" and c.day == cc.day and c.time_slot == cc.time_slot:
            return True
        if c.type == "SG" and cc.type == "SG" and c.teacher == cc.teacher:
            return True

        return False



