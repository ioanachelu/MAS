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
        self.relax = self.rules["relax"]
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

    def test_deadlock(self):
        if self.reservation:
            return True
        ok = False
        for day in range(self.rules["nb_days"]):
            for room in range(self.rules["nb_rooms"]):
                for time_slot in range(self.rules["nb_time_slots"]):
                    cell = self.env.get_cell([day, room, time_slot])
                    if BA.compatible_cell(self, cell, self.relax):
                        ok = True
        if ok == False:
            print("zis is bad")
        return ok

    def modify_induced_constraints(self, CB):
        self.CB = CB

    def remove_constraint(self, con):
        for constr in self.CI:
            if self.type == "T" and constr.type == self.type and constr.day == con["day"] and \
                            constr.time_slot == con["time_slot"] and constr.teacher == con["teacher"]:
                self.CI.remove(constr)
            elif constr.type == self.type and constr.tc_avail == con["T_courses_availability"]:
                self.CI.remove(constr)

    def add_constraint(self, con):
        con.owner = self
        self.CI.append(con)

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
                        self.cancel_reservation(extend_to_partner=False)
                    self.set_reservation(self.partnership.rCell)
                    self.inform_proxy_of_cell_reservation(self.proxy)
                else:
                    if self.reservation:
                        self.inform_ba_of_cell_reservation(self.partnership)

            if message.type == 'partnership_cancelation':
                print("BA {} received partnership cancelation message from {}".format(self.name, message.sender.name))
                if self.partner and self.partnership != message.sender:
                    self.cancel_partnership()
                if self.partner and self.partnership == message.sender:
                    self.cancel_partnership(inform=False)
                    if self.reservation and self.rCell.reservation != self:
                        self.cancel_reservation(extend_to_partner=False)

            if message.type == 'reservation_cancelation':
                print("BA {} received reservation cancelation message from {}".format(self.name, message.sender.name))
                if self.reservation:
                    self.cancel_reservation()

            if message.type == 'reservation':
                print("BA {} received reservation message from {} for cell [{}, {}, {}]".format(self.name,
                                                                                                message.sender.name,
                                                                                                message.partner_of_cell.day,
                                                                                                message.partner_of_cell.time_slot,
                                                                                                message.partner_of_cell.room))
                if self.reservation and self.rCell != message.partner_of_cell:
                    self.cancel_reservation(extend_to_partner=False)
                    self.set_reservation(message.partner_of_cell)
                    self.inform_proxy_of_cell_reservation(self.proxy)
                elif not self.reservation:
                    self.set_reservation(message.partner_of_cell)
                    self.inform_proxy_of_cell_reservation(self.proxy)

    def get_possibilities(self):
        day = self.cell.day
        room = self.cell.room
        time_slot = self.cell.time_slot

        possibilities = []
        directions = [day, room, time_slot]
        up_down = [1, -1]
        directions_end = [self.rules["nb_days"], self.rules["nb_rooms"], self.rules["nb_time_slots"]]

        for i in range(3):
            for j in up_down:
                new_directions = directions[:]
                new_directions[i] += j
                new_directions[i] %= directions_end[i]
                next_cell = self.env.get_cell(new_directions)
                if next_cell != self.cell:
                    possibilities.append(next_cell)

        return possibilities

    def move_to(self, cell):
        print("BA {} moved from cell DAY {} TIME {} ROOM {} to cell DAY {} TIME {} ROOM {}".format(self.name,
                                                                                                   self.cell.day,
                                                                                                   self.cell.time_slot,
                                                                                                   self.cell.room,
                                                                                                   cell.day,
                                                                                                   cell.time_slot,
                                                                                                   cell.room))

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
        m = Message("partnership_cancelation", sender=self)
        baj.mq.append(m)

    def inform_proxy_of_cell_reservation(self, ra):
        m = Message("reservation", self.rCell, self)
        ra.mq.append(m)

    def inform_proxy_of_cell_reservation_cancelation(self, ra):
        m = Message("reservation_cancelation", None, self)
        ra.mq.append(m)

    def inform_ba_of_cell_reservation(self, baj):
        m = Message("reservation", self.rCell, sender=self)
        baj.mq.append(m)

    def inform_ba_of_cell_reservation_cancelation(self, baj):
        m = Message("reservation_cancelation", sender=self)
        baj.mq.append(m)

    def partner_with(self, baj):
        print("BA {} partners with {}".format(self.name, baj.name))
        self.cancel_partnership()
        self.set_partnership(baj)

    def cancel_reservation(self, extend_to_partner=True):
        if self.reservation:
            self.reservation = False
            if self.rCell.reservation == self:
                self.rCell.reservation = None
            self.rCell = None
            self.time = 1
            self.CR = []
            if extend_to_partner == True and self.partner:
                # inform him of the cell reservation
                self.inform_ba_of_cell_reservation_cancelation(self.partnership)
            self.inform_proxy_of_cell_reservation_cancelation(self.proxy)

    def set_reservation(self, cell):
        self.cancel_reservation()
        if cell.reservation is not None and cell.reservation != self.partnership:
            cell.reservation.cancel_reservation()
        self.reservation = True
        self.rCell = cell
        if cell.reservation is None:
            cell.reservation = self
        if cell.reservation == self:
            self.CR = [Constraint("R", day=cell.day, time_slot=cell.time_slot, room=cell.room)]

    def cancel_partnership(self, inform=True):
        if self.partner:
            if inform:
                self.inform_ba_of_partnership_cancelation(self.partnership)
            self.inform_proxy_of_partnership_cancelation(self.proxy)
            self.partnership = None
            self.partner = False
            self.CP = []

    def set_partnership(self, baj, inform=True):
        self.partner = True
        self.partnership = baj
        self.CP = (baj.CI + baj.CR + baj.get_induced_constraints())
        if inform:
            self.inform_ba_of_partnership(baj)
        self.inform_proxy_of_partnership(self.proxy)

    def reserve_crt_cell(self):
        print("BA {} reserves cell: DAY {}, TIME {}, ROOM {}".format(self.name, self.cell.day, self.cell.time_slot,
                                                                     self.cell.room))
        # set the current reservation
        # treats also the partners case and the case other reservations of the cell exists and
        # the case I have a different reservation that needs to be canceled
        self.set_reservation(self.cell)

        # if I have a partner
        if self.partner:
            # inform him of the cell reservation
            self.inform_ba_of_cell_reservation(self.partnership)
        self.inform_proxy_of_cell_reservation(self.proxy)

    def process_crt_cell(self):
        # bas_in_cell = [ba for ba in self.cell.get_bas() if ba != self]
        # for baj in bas_in_cell:
        #     if baj in self.brothers:
        #         return 2

        # if this cell is compatible and..
        # my reservation goal is not achieved and...
        # the current cell is not already reserved by some other dude..
        # than book that damn thing immediately
        if BA.compatible_cell(self, self.cell, self.relax) and not self.reservation and self.cell.reservation is None:
            self.reserve_crt_cell()
            return 1

        # if this cell is compatible but...
        # I already have a reservation and it's not this one and..
        # the cost of the current cell is lower than the cost of my current reservation...
        # reserve this cell instead
        if BA.compatible_cell(self, self.cell, self.relax) and \
                (self.reservation and self.cell != self.rCell and (
                    BA.rCost(self, self.cell) < BA.rCost(self, self.rCell))):
            self.reserve_crt_cell()
            return 1

        if BA.compatible_cell(self, self.cell, self.relax) and \
            (not self.reservation and (BA.rCost(self, self.cell) < BA.rCost(self.cell.reservation, self.cell))):
            self.reserve_crt_cell()
            return 1

        if BA.compatible_cell(self, self.cell, self.relax) and \
                (self.reservation and self.cell != self.rCell and self.cell.reservation is not None and
                     (BA.rCost(self, self.cell) < BA.rCost(self.cell.reservation, self.cell)) and
                     (BA.rCost(self, self.cell) < BA.rCost(self, self.rCell))):
            self.reserve_crt_cell()
            return 1

        return 0

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
            if not BA.compatible(self, baj, self.relax) or (
                        self.partner and BA.pCost(self, baj) >= BA.pCost(self, self.partnership)):
                if not BA.compatible(self, baj, self.relax) and self.reservation and BA.compatible_without_his_reservation(self, baj, self.relax):
                    self.partner_with(baj)
                    return 1
                # self.knows.extend(baj.knows)
                continue
            # if he's compatible and...
            # if I don;t have a partnet and he doesn't have a partner
            if not self.partner and not baj.partner:
                self.partner_with(baj)
                return 1
            # if I have a partner but this guy is better and I am not competing with anyone
            if self.partner and BA.pCost(self, baj) < BA.pCost(self, self.partnership) and not baj.partner:
                self.partner_with(baj)
                return 1
            # if I have a partner, but this guy also has a partner, but our relationship is the best
            if self.partner and BA.pCost(self, baj) < BA.pCost(self, self.partnership) and baj.partner and BA.pCost(
                    self, baj) < BA.pCost(baj, baj.partnership):
                self.partner_with(baj)
                return 1
            # if I don;t have a partner, but this guy has
            if not self.partner and baj.partner and BA.pCost(self, baj) < BA.pCost(baj, baj.partnership):
                self.partner_with(baj)
                return 1
        return 0

    def perceive(self):
        self.process_messages()

    def step(self):
        self.time += 1
        if self.partner and self.reservation:
            # if goals are satisfied
            if BA.rCost(self, self.rCell) == 0:
                # if reservation is optimal that should move to it and stay there
                if self.cell == self.rCell:
                    print("Reservation is optimal and i am already in that cell")
                else:
                    print("Reservation is optimal and i am going there cell")
                    self.move_to(self.rCell)
                self.add_bas_to_memory()
            else:
                print("Reservation is not optimal. Exploring other opportunities")
                # self.explore()
                self.add_bas_to_memory()
                rez = self.process_crt_cell()
                if rez == 0:
                    print("Cell doesn't fit with constraints")
                if rez == 2:
                    print("Moving along. Brothers in cell")
        else:
            self.explore()
            self.add_bas_to_memory()  # analyse bas which are in the cell
            rez = self.process_encountered_bas()  # verify whether they fit with constraints
            if rez == 0:
                print("No BAs fit with constraints")
            # if goals are not reached
            if not self.partner or not self.reservation:
                # analyse the current cell
                rez = self.process_crt_cell()
                if rez == 0:
                    print("Cell doesn't fit with constraints")
                if rez == 2:
                    print("Moving along. Brothers in cell")

    def explore(self):
        possibilities = self.get_possibilities()
        pruned_possibilities = []
        for cell in possibilities:
            if cell not in self.knownCells:
                pruned_possibilities.append(cell)
        if len(pruned_possibilities) == 0:
            print("All cells are known. Choosing randomly of the known cells")
            choosen_cell = random.choice(self.knownCells)
        else:
            print("Exploring a new cell.")
            choosen_cell = random.choice(pruned_possibilities)
            self.knownCells.extend(pruned_possibilities)
        self.move_to(choosen_cell)

    @staticmethod
    def compatible_cell(bai, cj, relax=False):
        return len(BA.NC_cell(bai, cj, relax)) == 0

    @staticmethod
    def compatible(bai, baj, relax=False):
        return bai.type != baj.type and len(BA.NC_ba(bai, baj, relax)) == 0

    @staticmethod
    def compatible_without_his_reservation(bai, baj, relax=False):
        rez = bai.type != baj.type and len(BA.NC_ba_without_his_reservation(bai, baj, relax)) == 0
        if rez:
            print("sdasfas")
        return rez

    @staticmethod
    def NC_ba(bai, baj, relax=False):
        return BA.nonCompatible(bai.CI + bai.get_induced_constraints() + bai.CR,
                                baj.CI + baj.get_induced_constraints() + baj.CR, relax)

    @staticmethod
    def NC_ba_without_his_reservation(bai, baj, relax=False):
        return BA.nonCompatible(bai.CI + bai.get_induced_constraints() + bai.CR,
                                baj.CI + baj.get_induced_constraints(), relax)

    @staticmethod
    def NC_cell(bai, cj, relax=False):
        if cj is None:
            return None
        return BA.nonCompatible(bai.CI + bai.get_induced_constraints() + bai.CP, cj.C, relax)

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
    def nonCompatible(Ci, Cj, relax=False):
        non_c = [c for c in Ci if BA.nonCompatible_constraint_with_set(c, Cj, relax)]
        return non_c


    @staticmethod
    def nonCompatible_constraint_with_set(c, Cj, relax=False):
        res = []
        for cc in Cj:
            if BA.nonCompatible_constraints(c, cc, relax):
                res.append(c)
                break

        return res


    @staticmethod
    def nonCompatible_constraints(c, cc, relax=False):
        if cc.type == "U" or c.type == "U" and not relax:
            return True
        if not relax and (((c.type == "T" or c.type == "SG") and cc.type == "A" and 'projector' not in cc.tools) or ((cc.type == 'T' or
                                                                                                               cc.type == 'SG') and c.type == 'A' and 'projector' not in c.tools)):
            return True
        if c.type == "T" and cc.type == "T":
            return True
        if c.type == "SG" and cc.type == "SG":
            return True
        if ((c.type == 'T' and cc.type == 'R') or (
                c.type == 'R' and cc.type == 'T')) and c.day == cc.day and c.time_slot == cc.time_slot and not relax:
            return True
        if c.type == 'T' and cc.type == 'SG':
            nr_courses_taken_by_brothers = 0
            for con in cc.owner.CB:
                if con.type == 'B' and con.teacher == c.teacher and con.owner_name != cc.owner.name:
                    nr_courses_taken_by_brothers += 1
            # print("Constraints induced by brothers for sg {} for teacher {} = {}".format(cc.owner.name, c.teacher, nr_courses_taken_by_brothers))
            if cc.tc_avail[c.teacher] - 1 - nr_courses_taken_by_brothers < 0:
                return True
        if cc.type == 'T' and c.type == 'SG':
            nr_courses_taken_by_brothers = 0
            for con in c.owner.CB:
                if con.type == 'B' and con.teacher == cc.teacher and con.owner_name != c.owner.name:
                    nr_courses_taken_by_brothers += 1
            # print("Constraints induced by brothers for sg {} for teacher {} = {}".format(c.owner.name, cc.teacher,
            #                                                                              nr_courses_taken_by_brothers))
            if c.tc_avail[cc.teacher] - 1 - nr_courses_taken_by_brothers < 0:
                return True
        if c.type == 'T' and cc.type == 'R':
            for con in c.owner.CB:
                if con.type == 'I' and con.cell.day == cc.day and con.cell.time_slot == cc.time_slot and \
                                con.owner.ra_id == c.owner.ra_id and c.owner.id != con.owner.id and con.cell.room != cc.room:
                    return True
        if cc.type == 'T' and c.type == 'R':
            for con in cc.owner.CB:
                if con.type == 'I' and con.cell.day == c.day and con.cell.time_slot == c.time_slot and \
                                con.owner.ra_id == cc.owner.ra_id and cc.owner.id != con.owner.id:
                    return True
        if c.type == 'SG' and cc.type == 'R':
            for con in c.owner.CB:
                if con.type == 'I' and con.cell.day == cc.day and con.cell.time_slot == cc.time_slot and \
                                con.owner.ra_id == c.owner.ra_id and c.owner.id != con.owner.id and con.cell.room != cc.room:
                    return True
        if cc.type == 'SG' and c.type == 'R':
            for con in cc.owner.CB:
                if con.type == 'I' and con.cell.day == c.day and con.cell.time_slot == c.time_slot and \
                                con.owner.ra_id == cc.owner.ra_id and cc.owner.id != con.owner.id and con.cell.room != cc.room:
                    return True
        return False
