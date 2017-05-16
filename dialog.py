import tkinter as tk
import tkinter.simpledialog as sd

class ConstraintDialog(sd.Dialog):

    def __init__(self, parent, title=None, params=None):
        self.params = params
        super(ConstraintDialog, self).__init__(parent, title)

    def body(self, master):
        self.ra_type = self.params[0]
        self.entries = []
        if self.ra_type == "T":
            tk.Label(master, text="Day:").grid(row=0)
            tk.Label(master, text="Time:").grid(row=1)
            e1 = tk.Entry(master)
            e2 = tk.Entry(master)

            e1.grid(row=0, column=1)
            e2.grid(row=1, column=1)
            self.entries = [e1, e2]
        elif self.ra_type == "SG":
            nb_teachers = self.params[1]

            for t in range(nb_teachers):
                tk.Label(master, text="T_{}:".format(t)).grid(row=t, column=0)
                e = tk.Entry(master)
                e.grid(row=t, column=1)
                self.entries.append(e)
        else:
            tk.Label(master, text="Day:").grid(row=0)
            tk.Label(master, text="Time:").grid(row=1)
            tk.Label(master, text="Room:").grid(row=2)
            e1 = tk.Entry(master)
            e2 = tk.Entry(master)
            e3 = tk.Entry(master)

            e1.grid(row=0, column=1)
            e2.grid(row=1, column=1)
            e3.grid(row=2, column=1)
            self.entries = [e1, e2, e3]


    def apply(self):
        self.result = [e.get() for e in self.entries]
