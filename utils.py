class Message():
    def __init__(self, type, partner_or_cell=None, sender=None):
        self.type = type
        self.partner_of_cell = partner_or_cell
        self.sender = sender

class Constraint():
    def __init__(self, type, day=None, time_slot=None, course=None, teacher=None, cell=None, owner=None, room=None,
                 tc_avail=None, tools=None, weight=1):
        self.type = type
        self.day = day
        self.time_slot = time_slot
        self.course = course
        self.teacher = teacher
        self.cell = cell
        self.cell_owner = owner
        self.room = room
        self.tc_avail = tc_avail
        self.weight = weight
        self.tools = tools