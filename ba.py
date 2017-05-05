import random
import copy
from threading import Thread
from utils import Message
import time
import threading
from utils import Constraint

class BA():
    def __init__(self, type, ra, id, rules, cell, CI, CB, mq, env):
        # super(BA, self).__init__(name=type + str(ra.id) + str(id))
        self.type = type
        self.ra_id = ra.id
        self.proxy = ra
        self.id = id
        self.rules = rules
        self.name = self.type + str(self.ra_id) + "_" + str(self.id)
        # current cell the agent is in
        self.cell = cell
        # current partnership goal achieved
        self.partner = False
        # current reservation goal achieved
        self.reservation = False
        # current partner
        self.partnership = None
        # current reservation cell
        self.rCell = None
        # time passed since no reservation
        self.time = 1
        # the list of agents - BA this one knows
        self.knows = []
        # the list of intrinsic constraints from the RA
        self.CI = CI
        for c in self.CI:
            c.owner = self
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

    def modify_induced_constraints(self, CB):
        self.CB = CB

    def get_induced_constraints(self):
        return self.CB

    # when you've got mail
    def process_messages(self):
        while self.mq:
            message = self.mq.popleft()
            # if somebody wants to partner than my partner goals should be acomplished
            if message.type == 'partnership':
                print("BA {} received partnership message from {}".format(self.name, message.partner_of_cell.name))
                if self.partner and self.partnership != message.partner_of_cell:
                    self.cancel_partnership()
                self.set_partnership(message.partner_of_cell, inform=False)
                if self.partnership.reservation:
                    if self.reservation and self.rCell != self.partnership.rCell:
                        self.cancel_reservation()
                    self.set_reservation(self.partnership.rCell)
                else:
                    if self.reservation:
                        self.inform_ba_of_cell_reservation(self.partnership)

            if message.type == 'partnership_cancelation':
                print("BA {} received partnership cancelation message".format(self.name))
                if self.partner:
                    self.cancel_partnership()

            if message.type == 'reservation_cancelation':
                print("BA {} received reservation cancelation message".format(self.name))
                if self.reservation:
                    self.cancel_reservation()

            if message.type == 'reservation':
                print("BA {} received reservation message for cell [{}, {}, {}]".format(self.name, message.partner_of_cell.day,
                                                                                       message.partner_of_cell.room,
                                                                                       message.partner_of_cell.time_slot))
                if self.reservation and self.rCell != message.partner_of_cell:
                    self.cancel_reservation()
                    self.set_reservation(message.partner_of_cell)
                elif not self.reservation:
                    self.set_reservation(message.partner_of_cell)

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

            # if directions[choose_direction] + up_down[choose_up_down] > 0 and \
            #     directions[choose_direction] + up_down[choose_up_down] < directions_end[choose_direction]:

            new_directions = directions[:]
            new_directions[choose_direction] += up_down[choose_up_down]
            new_directions[choose_direction] %= directions_end[choose_direction]
            next_cell = self.env.get_cell(new_directions)

            return next_cell

    def move_to(self, cell):
        print("BA {} moved from cell DAY {} ROOM {} TIME {} to cell DAY {} ROOM {} TIME {}".format(self.name,
                                                                                                   self.cell.day,
                                                                                                   self.cell.room,
                                                                                                   self.cell.time_slot,
                                                                                                   cell.day,
                                                                                                   cell.room,
                                                                                                   cell.time_slot))

        if cell == self.cell:
            return
        else:
            self.knownCells.append(cell)
            self.cell.remove_ba_from_here(self)
            cell.bas.append(self)
            old_cell = self.cell
            self.cell = cell

            #     print("BA {} is moving from [{},{},{}] to [{},{},{}]".format(self.name, old_cell.day, old_cell.room,
    #                                                              old_cell.time_slot, self.cell.day,
    #                                                              self.cell.room,
    #                                                              self.cell.time_slot))

    def inform_ba_of_partnership(self, baj):
        m = Message("partnership", self)
        baj.mq.append(m)

    def inform_proxy_of_partnership(self, ra):
        m = Message("partnership", self.partnership, self)
        ra.mq.append(m)

    def inform_proxy_of_partnership_cancelation(self, ra):
        m = Message("partnership_cancelation", self.partnership, self)
        ra.mq.append(m)

    def inform_ba_of_partnership_cancelation(self, baj):
        m = Message("partnership_cancelation")
        baj.mq.append(m)

    def inform_proxy_of_cell_reservation(self, ra):
        m = Message("reservation", self.rCell, self)
        ra.mq.append(m)

    def inform_proxy_of_cell_reservation_cancelation(self, ra):
        m = Message("reservation_cancelation", None, self)
        ra.mq.append(m)

    def inform_ba_of_cell_reservation(self, baj):
        m = Message("reservation", self.rCell)
        baj.mq.append(m)

    def inform_ba_of_cell_reservation_cancelation(self, baj):
        m = Message("reservation_cancelation")
        baj.mq.append(m)

    def partner_with(self, baj):
        print("BA {} partners with {}".format(self.name, baj.name))
        self.cancel_partnership()
        self.set_partnership(baj)

    def cancel_reservation(self):
        if self.reservation:
            self.reservation = False
            self.rCell.reservation = None
            self.rCell = None
            self.time = 1
            self.CR = []
            if self.partner:
                # inform him of the cell reservation
                self.inform_ba_of_cell_reservation_cancelation(self.partnership)
            self.inform_proxy_of_cell_reservation_cancelation(self.proxy)

    def set_reservation(self, cell):
        self.cancel_reservation()
        if cell.reservation is not None and self.cell.reservation != self.partnership:
            cell.reservation.cancel_reservation()
        self.reservation = True
        self.rCell = cell
        cell.reservation = self
        self.CR = [Constraint("R", day=cell.day, time_slot=cell.time_slot, room=cell.room)]

    def cancel_partnership(self):
        if self.partner:
            self.inform_ba_of_partnership_cancelation(self.partnership)
            self.inform_proxy_of_partnership_cancelation(self.proxy)
            self.partnership = None
            self.partner = False
            self.CP = []

    def set_partnership(self, baj, inform=True):
        self.partner = True
        self.partnership = baj
        self.CP = baj.CI
        if inform:
            self.inform_ba_of_partnership(baj)
        self.inform_proxy_of_partnership(self.proxy)

    def reserve_crt_cell(self):
        print("BA {} reserves cell: DAY {}, ROOM {}, TIME {}".format(self.name, self.cell.day, self.cell.room, self.cell.time_slot))
        # set the current reservation
        # treats also the partners case and the case other reservations of the cell exists and
        # the case I have a different reservation that needs to be canceled
        self.set_reservation(self.cell)

        # if I have a partner
        if self.partner:
            # inform him of the cell reservation
            self.inform_ba_of_cell_reservation(self.partnership)
        self.inform_proxy_of_cell_reservation(self.proxy)

        # if self.cell.reservation is not None:
        #     self.cell.reservation.rCell = None
        #
        #     # TODO inform him I have stolen the reservation
        #     self.cell.reservation.time = 1
        #     if self.cell.reservation.partner is not None:
        #         print("{} stole the reservation of cell: day-{} room-{} time-{} from {} and {}".format(self.name,
        #                                                                                                self.cell.day,
        #                                                                                                self.cell.room,
        #                                                                                                self.cell.time_slot,
        #                                                                                                self.cell.reservation.name,
        #                                                                                                self.cell.reservation.partner.name))
        #         self.cell.reservation.partner.rCell = None
        #         # TODO inform him I have stolen the reservation
        #         self.cell.reservation.partner.time = 1
        #     else:
        #         print("{} stole the reservation of cell: day-{} room-{} time-{} from {} and {}".format(self.name,
        #                                                                                                self.cell.day,
        #                                                                                                self.cell.room,
        #                                                                                                self.cell.time_slot,
        #                                                                                                self.cell.reservation.name,
        #                                                                                                None))
        #
        # if self.rCell is not None:
        #     self.rCell.set_reservation(None)
        #
        # self.rCell = self.cell
        # self.cell.set_reservation(self)
        # if self.partner is not None:
        #     self.inform_ba_of_cell_reservation(self.partner)
        # self.inform_proxy_of_cell_reservation(self.proxy)
        # self.time = 1

    def process_crt_cell(self):
        bas_in_cell = [ba for ba in self.cell.get_bas() if ba != self]
        for baj in bas_in_cell:
            if baj in self.brothers:
                return

        # if this cell is compatible and..
        # my reservation goal is not achieved and...
        # the current cell is not already reserved by some other dude..
        # than book that damn thing immediately
        if BA.compatible_cell(self, self.cell) and not self.reservation and self.cell.reservation is None:
            self.reserve_crt_cell()

        # if this cell is compatible but...
        # I already have a reservation and it's not this one and..
        # the cost of the current cell is lower than the cost of my current reservation...
        # reserve this cell instead
        if BA.compatible_cell(self, self.cell) and \
                (self.reservation and self.cell != self.rCell and (BA.rCost(self, self.cell) < BA.rCost(self, self.rCell))):
            self.reserve_crt_cell()

    # extend the BA acquaintances network. Hand shake a bit...
    def add_bas_to_memory(self):
        # get all BAs in the cell
        bas_in_cell = [ba for ba in self.cell.get_bas() if ba != self]
        for ba in bas_in_cell:
            if ba not in self.knows:
                # if I didn't know them before now I do
                self.knows.append(ba)
                # exchange lift of acquaintances as well
                for bak in ba.knows:
                    if bak not in self.knows:
                        self.knows.append(bak)

        # set as eligible bas as the one in the current cell
        # self.eligible_bas = self.knows

    # filter a bit the BAs in the cell. Some are really bad people..
    def process_encountered_bas(self):
        # pruned_eligible_bas = []
        # for baj in self.eligible_bas:
        #     # if his not my type... or
        #     if len(BA.NC_ba(self, baj)) != 0:
        #         continue
        #     # if self.reservation:
        #     #     # if he doesn't like my place..
        #     #     if len(BA.NC_cell(baj, self.rCell)) != 0:
        #     #         continue
        #     # if he's cool.. add him
        #     pruned_eligible_bas.append(baj)

        # self.eligible_bas = pruned_eligible_bas

        for baj in self.knows:
            # if partner is not compatible
            # or I already acieved the partnership goal and my partner is better than the new opportunity in front of me
            # ignore this guy
            if not BA.compatible(self, baj) or (
                self.partner and BA.pCost(self, baj) >= BA.pCost(self, self.partnership)):
                # self.knows.extend(baj.knows)
                continue
            # if he's compatible and...
            # if I don;t have a partnet and he doesn't have a partner
            if not self.partner and not baj.partner:
                self.partner_with(baj)
                break
            # if I have a partner but this guy is better and I am not competing with anyone
            if self.partner and BA.pCost(self, baj) < BA.pCost(self, self.partnership) and not baj.partner:
                self.partner_with(baj)
                break
            # if I have a partner, but this guy also has a partner, but our relationship is the best
            if self.partner and BA.pCost(self, baj) < BA.pCost(self, self.partnership) and baj.partner and BA.pCost(
                    self, baj) < BA.pCost(baj, baj.partnership):
                self.partner_with(baj)
                break
            # if I don;t have a partner, but this guy has
            if not self.partner and baj.partner and BA.pCost(self, baj) < BA.pCost(baj, baj.partnership):
                self.partner_with(baj)
                break

    def perceive(self):
        self.process_messages()

    def step(self):
        self.time += 1
        if self.partner and self.reservation:
            # if goals are satisfied
            if BA.rCost(self, self.rCell) == 0:
                # if reservation is optimal that should move to it and stay there
                self.move_to(self.rCell)
            else:
                self.process_crt_cell()
        else:
            # randomly sample a next cell. TODO: skip the one I know are no good. Maybe later when introducing cell constraints
            tries = 0
            while True:
                tries += 1
                next_cell = self.get_next_cell()
                if next_cell not in self.knownCells:
                    self.move_to(next_cell)
                    break
                if tries == 10:
                    self.move_to(next_cell)
                    break
            self.add_bas_to_memory()  # analyse bas which are in the cell
            self.process_encountered_bas()  # verify whether they fit with constraints
            # if goals are not reached
            if not self.partner or not self.reservation:
                # analyse the current cell
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
        if cc.type == "U" or c.type == "U":
            return True
        if ((c.type == "T" or c.type == "SG") and cc.type == "A" and 'projector' not in cc.tools) or ((cc.type == 'T' or
            cc.type == 'SG') and c.type == 'A' and 'projector' not in c.tools):
                return True
        if c.type == "T" and cc.type == "T":
            return True
        if c.type == "SG" and cc.type == "SG":
            return True
        if ((c.type == 'T' and cc.type == 'R') or (c.type == 'R' and cc.type == 'T')) and c.day == cc.day and c.time_slot == cc.time_slot:
            return True
        if c.type == 'T' and cc.type == 'SG':
            nr_courses_taken_by_brothers = 0
            for con in cc.owner.CB:
                if con.type == 'B' and con.teacher == c.teacher:
                    nr_courses_taken_by_brothers += 1
            print("Constraints induced by brothers for sg {} for teacher {} = {}".format(cc.owner.name, c.teacher, nr_courses_taken_by_brothers))
            if cc.tc_avail[c.teacher] - 1 - nr_courses_taken_by_brothers < 0:
                return True
        if cc.type == 'T' and c.type == 'SG':
            nr_courses_taken_by_brothers = 0
            for con in c.owner.CB:
                if con.type == 'B' and con.teacher == cc.teacher:
                    nr_courses_taken_by_brothers += 1
            print("Constraints induced by brothers for sg {} for teacher {} = {}".format(c.owner.name, cc.teacher,
                                                                                         nr_courses_taken_by_brothers))
            if c.tc_avail[cc.teacher] - 1 - nr_courses_taken_by_brothers < 0:
                return True
        return False



