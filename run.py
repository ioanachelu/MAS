import argparse

from timetable_gui import Timetable
import sys
import tkinter as tk
import os

def get_arguments():
    """Parse all the arguments provided from the CLI.

    Returns:
      A list of parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Emergent Timetable")
    parser.add_argument("--test", type=str, default="test1",
                        help="Name of the test to be ran")
    return parser.parse_args()


if __name__ == '__main__':
    # os.remove('output.txt')
    # orig_stdout = sys.stdout
    # f = open('out.txt', 'w')
    # sys.stdout = f

    args = get_arguments()

    root = tk.Tk()
    # root.geometry("500x500")
    app = Timetable(args, root=root)
    app.pack(side="top", fill="both", expand=True)
    app.mainloop()