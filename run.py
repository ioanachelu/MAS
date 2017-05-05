import argparse
from read_input import read_test
from environment import Environment


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
    args = get_arguments()
    rules = read_test(args.test)
    environment = Environment(rules)
    environment.step()