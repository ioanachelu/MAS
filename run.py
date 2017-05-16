import argparse

from timetable_gui import Timetable
import sys
import tkinter as tk

def get_arguments():
    """Parse all the arguments provided from the CLI.

    Returns:
      A list of parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Emergent Timetable")
    parser.add_argument("--test", type=str, default="test4",
                        help="Name of the test to be ran")
    return parser.parse_args()


if __name__ == '__main__':
    # orig_stdout = sys.stdout
    # f = open('out.txt', 'w')
    # sys.stdout = f

    args = get_arguments()

    root = tk.Tk()
    app = Timetable(args, master=root)
    app.mainloop()