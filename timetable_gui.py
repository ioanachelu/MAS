import tkinter as tk
from read_input import read_test
from environment import Environment
from dialog import ConstraintDialog
from tkinter import messagebox

class Timetable(tk.Frame):
    def __init__(self, args, root=None):
        tk.Frame.__init__(self, root)
        self.args = args
        self.root = root
        self.root.geometry("500x500")
        self.old_violated_constraints = None
        self.canvas = tk.Canvas(self.root, borderwidth=0)
        self.vsb = tk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.setup()

        self.create_widgets()

    def setup(self):
        self.random_explore = self.args.random_exploration
        self.rules = read_test(self.args.test)
        self.environment = Environment(self.rules, self.random_explore)

        self.time = 0
        self.environment.print_info(self.time)
        self.current_ba = 0
        self.running = False

    def relax_cb(self):
        # print("variable is", self.relax_var.get())
        self.rules["relax"] = int(self.relax_var.get())
        print("variable is", self.rules["relax"])
        self.environment.set_relax()

    def onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def populate(self):
        '''Put in some fake data'''
        for row in range(100):
            tk.Label(self.frame, text="%s" % row, width=3, borderwidth="1",
                     relief="solid").grid(row=row, column=0)
            t = "this is the second column for row %s" % row
            tk.Label(self.frame, text=t).grid(row=row, column=1)

    def create_widgets(self):

        self.frame = tk.Frame(self.canvas)

        self.frame.bind("<Configure>", self.onFrameConfigure)
        self.canvas.create_window((4, 4), window=self.frame, anchor="nw",
                                  tags="self.frame")

        self.play_button = tk.Button(self.frame)
        self.play_button["text"] = "Play"
        self.play_button["command"] = self.play
        self.play_button.grid(row=0, column=0)

        self.stop_button = tk.Button(self.frame)
        self.stop_button["text"] = "Pause"
        self.stop_button["command"] = self.stop
        self.stop_button.grid(row=0, column=1)

        self.step_button = tk.Button(self.frame)
        self.step_button["text"] = "Step"
        self.step_button["command"] = self.step
        self.step_button.grid(row=0, column=2)
        self.quit_button = tk.Button(self.frame, text="Stop", fg="red",
                              command=self.root.destroy)

        self.quit_button.grid(row=0, column=3)

        self.relax = bool(self.rules["relax"])
        # self.relax_label = tk.Label(self.frame,
        #       text="Relax: " + str(self.relax),
        #       font="Times").grid(row=1, column=0)

        self.relax_var = tk.BooleanVar()
        self.relax_var.set(bool(self.relax))
        relax_checkb = tk.Checkbutton(self.frame, variable=self.relax_var,
                                      text="Relax constraints", font="Times", command=self.relax_cb)
        relax_checkb.grid(row=1, column=0)

        self.nb_teachers = self.rules["nb_teachers"]
        self.nb_teachers_label = tk.Label(self.frame,
                                    text="Nb Teachers : " + str(self.nb_teachers),
                                    font="Times").grid(row=2, column=0)

        self.nb_sg = self.rules["nb_st_groups"]
        self.nb_sg_label = tk.Label(self.frame,
                                    text="Nb SG: " + str(self.nb_sg),
                                    font="Times").grid(row=3, column=0)
        row = 4
        for id in range(self.rules["nb_teachers"]):
            row = self.print_ra("T", id, row)

        for id in range(self.rules["nb_st_groups"]):
            row = self.print_ra("SG", id, row)

        add_con_button = tk.Button(self.frame, text='Add cell constraint',
                                       command=lambda : self.add_cell_constraint())
        add_con_button.grid(row=row, column=0)

        row += 1
        for c in self.rules["cell_constraints"]["unavailability"]:
            row = self.print_cell_unavailability(c, row)

    def add_cell_constraint(self):
        inputDialog = ConstraintDialog(self.frame, params=("C"))
        results = [int(e) for e in inputDialog.result]
        con = {"day": results[0], "time_slot": results[1], "room": results[2]}
        self.rules["cell_constraints"]["unavailability"].append(con)
        self.environment.add_cell_constraint(con)
        self.refresh()

    def add_constraint(self, entries):
        ra_type, id = entries
        if ra_type == "SG":
            nb_teachers = self.rules["nb_teachers"]
            inputDialog = ConstraintDialog(self.frame, params=(ra_type, nb_teachers))
        else:
            inputDialog = ConstraintDialog(self.frame, params=(ra_type,))
        the_ra = None
        for ra in self.environment.ras[ra_type]:
            if ra.id == id:
                the_ra = ra
        if inputDialog.result is None:
            return
        results = [int(e) for e in inputDialog.result]
        if ra_type == "T":
            con = {"day": results[0], "time_slot": results[1], "teacher": id}
        else:
            con = {"T_courses_availability": results}
        self.rules["ra_constraints"][ra_type][str(id)]["constraints"].append(con)
        the_ra.add_constraint(results)
        self.refresh()

    def refresh(self):
        # self.canvas.delete("all")
        self.frame.destroy()
        # self.vsb.destroy()
        self.create_widgets()

    def set_nb_bas(self, ra_type, id, nb_bas):
        nb_bas = int(nb_bas)
        the_ra = None
        for ra in self.environment.ras[ra_type]:
            if ra.id == id:
                the_ra = ra
        old_nb_bas = self.rules["ra_constraints"][ra_type][str(id)]["nb_courses"]
        if old_nb_bas < nb_bas:
            to_be_added = the_ra.add_bas(nb_bas - old_nb_bas)
            self.environment.all_bas.extend(to_be_added)
        else:
            to_be_removed = the_ra.remove_bas(old_nb_bas - nb_bas)
            for ba in self.environment.all_bas:
                ba.remove_dead_friends(to_be_removed)
            for ba in to_be_removed:
                self.environment.all_bas.remove(ba)
            self.environment.perceive_cycle()

        self.rules["ra_constraints"][ra_type][str(id)]["nb_courses"] = nb_bas
        self.frame.destroy()
        self.create_widgets()

    def print_cell_unavailability(self, con, r):
        tk.Label(self.frame, text="Cell unavailability").grid(row=r, column=0)
        tk.Label(self.frame, text="Day: " + str(con["day"])).grid(row=r+1, column=0)
        tk.Label(self.frame, text="Time: " + str(con["time_slot"])).grid(row=r+1, column=1)
        tk.Label(self.frame, text="Room: " + str(con["room"])).grid(row=r+1, column=2)
        tk.Button(self.frame, text="Remove",
                  command=lambda con=con: self.remove_cell_unavailability_constraint(con)).grid(row=r+1, column=3)
        return r+2

    def remove_cell_unavailability_constraint(self, con):
        self.environment.remove_cell_unavailability_constraint(con)
        self.rules["cell_constraints"]["unavailability"].remove(con)
        self.refresh()

    def print_constraint(self, ra_type, id, i, con, r):
        if ra_type == "T":
            tk.Label(self.frame, text="Unavailability").grid(row=r, column=0)
            tk.Label(self.frame, text="Day: " + str(con["day"])).grid(row=r, column=1)
            tk.Label(self.frame, text="Time: " + str(con["time_slot"])).grid(row=r, column=2)
            tk.Button(self.frame, text="Remove",
                      command=lambda entries=(ra_type, id, i, con): self.remove_constraint(entries)).grid(row=r , column=3)

        else:
            tk.Label(self.frame, text="Maximum Courses").grid(row=r, column=0)
            maximum_courses = []
            for teacher_ra_id, num_courses in enumerate(con["T_courses_availability"]):
                maximum_courses.append("T_{}[{}]".format(teacher_ra_id, num_courses))
            tk.Label(self.frame, text='  '.join(maximum_courses)).grid(row=r, column=1)
            tk.Button(self.frame, text="Remove",
                      command=lambda entries=(ra_type, id, i, con): self.remove_constraint(entries)).grid(row=r, column=3)

        return r+1

    def remove_constraint(self, entries):
        ra_type, id, i, con = entries
        self.rules["ra_constraints"][ra_type][str(id)]["constraints"].remove(con)
        the_ra = None
        for ra in self.environment.ras[ra_type]:
            if ra.id == id:
                the_ra = ra
        the_ra.remove_constraint(ra_type, id, i, con)
        self.refresh()
        # self.environment.remove_constraint(ra_type, id, i, con)

    def print_ra(self, ra_type, id, r):

        constraint = self.rules["ra_constraints"][ra_type][str(id)]
        nb_bas = self.rules["ra_constraints"][ra_type][str(id)]["nb_courses"]

        tk.Label(self.frame, text=ra_type + ": " + str(id)).grid(row=r, column=0)
        add_con_button = tk.Button(self.frame, text='Add constraint',
                                   command=lambda entries=(ra_type, id): self.add_constraint(entries))
        add_con_button.grid(row=r, column=1)
        tk.Label(self.frame, text="Nb BAs: ", font="Times").grid(row=r + 1, column=0)

        tk.Label(self.frame, text=str(nb_bas),
                 font="Times").grid(row=r + 1, column=2)

        nb_courses_entry = tk.Entry(self.frame)
        nb_courses_entry.grid(row=r + 1, column=1)
        nb_courses_entry.insert(tk.END, nb_bas)
        tk.Button(self.frame, text="Save",
                  command=lambda entry=nb_courses_entry: self.set_nb_bas(ra_type, id, entry.get())).grid(row=r + 1, column=3)

        row = r + 2
        for i, con in enumerate(constraint["constraints"]):
            row = self.print_constraint(ra_type, id, i, con, row)


        return row

    def should_continue(self):
        if messagebox.askyesno("Continue", "Found a solution. Continue searching?"):
            return True
        else:
            return False

    def play(self):
        self.running = True
        self.root.after(10, self.loop)

    def loop(self):
        if self.running:
            self.step()
            # After 1 second, call scanning again (create a recursive loop)
            self.root.after(100, self.loop)

    def stop(self):
        self.running = False

    def step(self):
        if self.current_ba >= len(self.environment.all_bas):
            self.current_ba = 0
        ba = self.environment.all_bas[self.current_ba]
        ba.step()
        print("BA {} acted".format(ba.name))
        self.environment.perceive_cycle()
        self.violated_constraints = self.environment.print_info(self.time)
        if self.violated_constraints == 0:
            if not self.should_continue():
                exit(0)
            else:
                self.stop()
        if self.violated_constraints > 0 and (self.old_violated_constraints is None or
                                                  (self.old_violated_constraints is not None and self.violated_constraints < self.old_violated_constraints)):
            self.old_violated_constraints = self.violated_constraints
            if not self.should_continue():
                exit(0)
        self.current_ba += 1
        if self.current_ba == len(self.environment.all_bas):
            self.current_ba = 0
            self.time += 1

    def run_without_stopping(self):
        while True:
            for ba in self.environment.all_bas:
                ba.step()
                # rez = ba.test_deadlock()
                # if not rez:
                #     print("DEADLOCK")
                #     exit(0)
                print("BA {} acted".format(ba.name))
                self.environment.perceive_cycle()
                self.violated_constraints = self.environment.print_info(self.time)
                if self.violated_constraints > 0 and self.old_violated_constraints is not None and self.violated_constraints != self.old_violated_constraints:
                    self.old_violated_constraints = self.violated_constraints
                    if not self.should_continue():
                        exit(0)
            self.time += 1


# root = tk.Tk()
# app = Timetable(master=root)
# app.mainloop()