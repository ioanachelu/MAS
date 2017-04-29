class Message():
    def __init__(self, type, partner_or_cell, sender=None):
        self.type = type
        self.partner_of_cell = partner_or_cell
        self.sender = sender

class Constraint():
    def __init__(self, type, day=None, time_slot=None, course=None, teacher=None, cell=None, owner=None):
        self.type = type
        self.day = day
        self.time_slot = time_slot
        self.course = course
        self.teacher = teacher
        self.cell = cell
        self.cell_owner = owner