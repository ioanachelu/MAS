import tkinter as tk
from read_input import read_test
from environment import Environment

class Timetable(tk.Frame):
    def __init__(self, args, master=None):
        super().__init__(master)
        self.args = args
        self.root = master
        self.pack()
        self.setup()
        if self.rules["stop"]:
            self.create_widgets()
        else:
            self.run_without_stopping()

    def setup(self):
        self.rules = read_test(self.args.test)
        self.environment = Environment(self.rules)

        self.time = 0
        self.environment.print_info(self.time)
        self.current_ba = 0

    def create_widgets(self):
        self.step_button = tk.Button(self)
        self.step_button["text"] = "Step"
        self.step_button["command"] = self.step
        self.step_button.pack(side="top")

        self.quit_button = tk.Button(self, text="QUIT", fg="red",
                              command=self.root.destroy)
        self.quit_button.pack(side="bottom")

    def step(self):

        ba = self.environment.all_bas[self.current_ba]
        ba.step()
        print("BA {} acted".format(ba.name))
        self.environment.perceive_cycle()
        self.environment.print_info(self.time)
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
                self.environment.print_info(self.time)
            self.time += 1


# root = tk.Tk()
# app = Timetable(master=root)
# app.mainloop()