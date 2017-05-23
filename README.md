# MAS Timetable emergent organization

## System requirements

 - Python3.5
 - numpy
 - tkinter

## Tests
All the tests are located in the ```tests``` directory. 
* ```test0``` - contains the first default test from the homework, but only day 1
* ```test1``` - contains the first default test from the homework
* ```test2``` - contains the second default test from the homework
* ```test3``` - contains the first default test from the homework, but only day 1, and only 2 teachers and 2 student groups 
 and 3 time slots
* ```test4``` - same test as ```test3``` but with one cell unavailability (room 1, second time slot)
* ```test5``` - same test as ```test0``` but with 2 cell unavailabilities (room 1, second time slot and room 3, third time slot)
* ```test6``` - same test as ```test0``` but with one cell unavailability (room 1, second time slot)

Tests are described in json format. Indexes from rooms, time slots, days, teachers, student groups etc. start at 0.

## Run options
A list of all available options is given by running:

    $ python run.py -h

To run a particular test:

    $ python run.py --test=test0
    
To run with random exploration, i.e. if I know all the cells in the perimeter - choose randomly from the known cells. I haven't explored
all the cells from the perimeter - choose randomly one cell from the perimeter to explore next.
    
    $ python run.py --random_exploration=True
    
To run with heuristic exploration, i.e. assign more probability to states that are unreserved than those already reserved by others.
    
    $ python run.py --random_exploration=False
    
A tkinter window will be displayed in which the play button should be pressed for running the test.
 
## Display options

* ```play``` - runs the algorithm until a solution is found
* ```pause``` - stop the algorithm's execution
* ```step``` - only run one step of the algorithm
* ```quit``` - exit

When a solution is found that is suboptimal (not all constraints are relaxed) a popup is displayed asking is it should continue 
with the search or stop.

At each point of the run, the console shows for each step the position of the bas in the world, the messages they receive
annotated with ```[Message]``` and information of what they are doing annotated with ```[Info]```
Also, after each illustration of the current positions on the timetable, the violated constraints are also enumerated, in case they exist.

The board with all the BAs shows in the first row of each cell, the bas present in that cell at that moment with white color.
In the parenthesis there is information about whether they have a partner of not and whether they have a reservation of not. Ex:
T0_0 (t/f) - the first ba agent of the first teacher has found a partner, but doesn't have a reservation.
The second row from each cell, colored with blue shows the current reservation for that cell. Ex: T1_0/SG0_1 - cell is reserved
by the first ba of the second teacher and the second ba of the first student group. Note: all indexes start at 0.
If a reservation for a cell, i.e. the second row of the cell is colored in red it means that the cell is reserved but the 
reservation is not optimal, i.e. a constraint is violated.

After a solution is found the board is again drawn in the console, this time with green showing optimal reservation and red
showing reservations that violate constraints. Only the RAs are shown and they are transformed from 0 index to 1 index to give 
an illustration as close as possible to the one from the homework description.