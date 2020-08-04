# file:    sudoku.py
# author:  Colin Woodbury
# contact: colingw@gmail.com
# version: 03/07/2011 Python 3 friendly.
# about:   This is a sudoku solver. It also happens to be set up as a
#          solution for Project Euler 96, and as such can solve
#          multiple puzzles in a row provided the data file is
#          formatted properly.
#          WORKING VERSION

from copy import deepcopy
from math import sqrt
from time import time
import sys

class BadBoard(Exception):
    '''An Error for bad input.'''

class Board:
    '''This is the Sudoku board itself.'''
    dim = 3  # Make this variable.
    eulerSum = 0  # The Project Euler 96 solution.

    def __init__(self):
        self.rows = []
        self.cols = []
        self.squares = []
        # Set up the Areas.
        for x in range(0, Board.dim**2):
            self.rows.append(Area())
            self.cols.append(Area())
            self.squares.append(Area())
        currRow = 0
        currCol = 0
        currSquare = 0
        # Create and add boxes.
        for x in range(0, Board.dim**4):
            currBox = Box(Board.dim, self.rows[currRow], self.cols[currCol],
                          self.squares[currSquare])
            self.rows[currRow].add_box(currBox)
            self.cols[currCol].add_box(currBox)
            self.squares[currSquare].add_box(currBox)
            currCol += 1
            if currCol % (Board.dim**2) == 0:
                # Reached the end of the row. Jump back and down.
                currCol = 0
                currRow += 1
                currSquare -= 2
                if currRow % Board.dim == 0:
                    currSquare += Board.dim
            elif currCol % Board.dim == 0:
                currSquare += 1

    def read_board(self, filename):
        '''Reads board and sends solve() commands.'''
        with open(filename) as file:
            # Read the grid name, then read the board and solve it.
            start = time()
            line = file.readline()
            if not line:
                raise BadBoard('Empty file given.')
            while line:
                print(line.rstrip())  # Prints grid name.
                for x in range(Board.dim**2):
                    if not line:
                        raise BadBoard('Incomplete file given.')
                    line = file.readline().rstrip()  # Eat that '\n'
                    if not len(line) == 9:
                        raise BadBoard('Too many/too few chars in a line.')
                    digits = [int(char) for char in line]
                    self.rows[x].add_numbers(digits) #add nums to Board
                # Inspect the board.
                self.check_board_validity()
                # Solve the board.
                solved = self.solve()
                if solved: # Continue.
                    Board.eulerSum += self.get_euler_sum()
                    self.reset_all()
                    line = file.readline()
                else: # Failed to solve.
                    break
        end = time()
        print('Finished all in {0}'.format(end - start))
        print('Euler solution:', Board.eulerSum)

    def check_board_validity(self):
        '''Checks if a valid board was provided.'''
        def check_section(area):
            for section in area:
                nums = set()
                for box in section.boxes:
                    if box.num != 0:
                        if box.num in nums:
                            raise BadBoard('Board with repeats given.')
                        else:
                            nums.add(box.num)

        check_section(self.rows)
        check_section(self.cols)
        check_section(self.squares)

    def solve(self):
        '''Acts as a base for the solving operations.
        This separation is important if the guessing logic
        hits the recursive stage.
        '''
        success = self.solve_manager()
        self.print_board()
        return success

    def solve_manager(self):
        '''Manages the solving operations.'''
        success = self.solve_logic()
        if not success:
            # Perform guesses and solve.
            success, boardCopy = self.guess_work()
            # Copy the working board copy to 'self'
            self.copy_entries(boardCopy)
        return success

    def solve_logic(self):
        '''Runs the logic.'''
        updated = 0  # The amount of squares updated on a sweep.
        success = True
        while not self.check_solve():
            updated = 0
            for x in range(0, Board.dim**2):
                updates = []
                updates.extend(self.rows[x].update())
                updates.extend(self.cols[x].update())
                updates.extend(self.squares[x].update())
                updated += len(updates)
                while len(updates) > 0:
                    updates.extend(updates[0].update_wave())
                    del updates[0]
            if updated == 0:  # No updates were made this sweep!
                curr = self.rows[0].tertiary
                # Activate tertiary logic on all rows all columns!
                #print("--Activating tertiary logic...")
                for each in self.rows:
                    each.update3()
                for each in self.cols:
                    each.update3()
                if self.rows[0].tertiary == curr: #it didn't change
                    # We need to break out of the while here, and fail.
                    success = False
                    break
                else:
                    pass #print('---Cancelations made. Continuing.')
        return success

    def check_solve(self):
        '''Check all areas to see if they are solved.'''
        solved = True #assume success
        for x in range(0, Board.dim**2):
            if not self.rows[x].area_solved() or not \
            self.cols[x].area_solved() or not \
            self.squares[x].area_solved():
                solved = False
                break
        return solved

    def guess_work(self):
        '''Find a Box with only two remaining possible values.
        Pick one arbitrarily, then attempt to resolve the board.
        If that fails, rewind and pick the other value.
        '''
        #print('Beginning guess work...')
        success = False  # Assume failure.
        boardCopy = deepcopy(self)
        target = boardCopy.find_unsolved_box()
        guesses = list(target.possibles)
        for x in range(0, len(guesses)):
            #print('Guessing {0}...'.format(guesses[x]))
            target.set_num(guesses[x])
            success = boardCopy.solve_manager()
            if success:
                break
            else:
                #print('Guess of {0} failed! Try again.'.format(guesses[x]))
                # Recopy the board and try again.
                boardCopy = deepcopy(self)
                target = boardCopy.find_unsolved_box()
        return (success, boardCopy)

    def find_unsolved_box(self):
        '''Find an unsolved box.'''
        stop = False
        target = None
        for row in self.rows:
            for box in row.boxes:
                if box.num == 0:
                    target = box
                    stop = True
                    break
            if stop:
                break
        return target

    def copy_entries(self, board):
        '''Copies the entries from 'board' into 'self'.'''
        for x in range(0, Board.dim**2):
            self.rows[x] = board.rows[x]
            self.cols[x] = board.cols[x]
            self.squares[x] = board.squares[x]

    def print_board(self):
        '''Prints the entire board.'''
        for x in range(0, Board.dim**2):
            if x % Board.dim == 0:
                self.print_frame_line('===')
            else:
                self.print_frame_line()
            self.rows[x].print_area()
        self.print_frame_line('===')

    def print_frame_line(self, mark=' - '):
        '''Prints a frame line.'''
        for x in range(0, Board.dim**2):
            print('*', end='')
            print(mark, end='')
        print('*')

    def get_euler_sum(self):
        '''Gets the top three digits as a three digit number
        for the solution to Project Euler 96.
        '''
        hundreds = self.rows[0].boxes[0].num * 100
        tens = self.rows[0].boxes[1].num * 10
        ones = self.rows[0].boxes[2].num
        return hundreds + tens + ones

    def reset_all(self):
        '''Resets the Board to its original state.'''
        for each in self.rows:
            each.reset()
        for each in self.cols:
            each.reset()
        for each in self.squares:
            each.reset()

class Area:
    '''Some area, either a row, column, or dim by dim square
    that holds Boxes.
    '''
    primary = 0
    secondary = 0
    tertiary = 0
    starting = 0

    def __init__(self):
        self.boxes = []

    def reset(self):
        '''Returns the Area to its original state.'''
        self.wipe_boxes()
        Area.primary = 0
        Area.secondary = 0
        Area.tertiary = 0
        Area.starting = 0

    def wipe_boxes(self):
        '''Resets all the Boxes in this Area.'''
        for each in self.boxes:
            each.reset_box()

    def add_box(self, box):
        '''Saves a Box pointer.'''
        self.boxes.append(box)

    def update(self):
        '''Updates the possible numbers in the current Area.
        Returns pointers to the Boxes whose true numbers were solved.
        '''
        result = [] # List of Box pointers that updated.
        # Iterate through all boxes in the Area.
        for curr in self.boxes:
            if curr.num != 0: # DON'T check boxes that already have a number.
                continue
            # Compare with all other boxes in Area
            for other in self.boxes:
                if curr is not other and other.num in curr.possibles:
                    curr.possibles.remove(other.num)
            # Check how many possibles are left.
            if len(curr.possibles) == 1: # Can only be one number.
                curr.num = curr.possibles[0]
                curr.possibles = []
                result.append(curr)
                Area.primary += 1
                # Update this Area again.
                result.extend(self.update())
        # Additional logic!
        # Should this method call be here, or somewhere else?
        result.extend(self.update2())
        return result

    def get_possibles(self, list):
        '''Given a list of Boxes to check, return a list
        of the common possibles and how many times they appeard.
        '''
        dict = {}
        # Setup dictionary.
        # Make this a dictionary comprehension!
        for x in range(1, len(self.boxes)+1):
            dict[x] = 0
        #scan the Area for possibles
        for each in list:
            if each.num != 0: #skip if the number is already known
                continue
            else:
                # For each possible number that appears,
                # update the dictionary
                for num in each.possibles:
                    dict[num] += 1
        return dict

    def find_occurances(self, num, area):
        '''Given a number and an Area to seach, scans all the boxes for
        the numer of times that number shows up as a possible.
        '''
        count = 0
        for each in area:
            if num in each.possibles:
                count += 1
        return count

    def update2(self):
        '''For situations were a Box isn't reduced to only 1 possibility,
        but it contains the only appearance of a certain possible number
        within the whole area, this method solves the Box.
        THE DICTIONARY WORK COULD LIKELY BE DONE DIFFERENTLY.
        '''
        dict = {} #a dictionary of possibles
        keyList = []
        updated = []

        # Get the number of all possibles in the Area.
        dict = self.get_possibles(self.boxes)
        # Scan through dictionary, look for values of 1.
        for each in dict:
            if dict.get(each) == 1:
                keyList.append(each)
        # Search Area for Boxes that have the numbers
        # in keyList as possibles
        for key in keyList:
            for box in self.boxes:
                if box.num == 0 and key in box.possibles: # Found.
                    box.num = key
                    box.possibles = []
                    updated.append(box)
                    Area.secondary += 1
                    break
        return updated

    def update3(self):
        '''This employs the 'number laser' logic.
        Move through each row and column.
        Collect boxes in the same Row and Square that share possibles.
        With the list of possibles, search the rest of the Square
        for instances of each possible. If it is found again, it can't be
        a laser. A laser then propagates to other boxes, cacelling out
        possibles within the same row/col.
        '''
        updated = []
        size = len(self.boxes)
        root = int(sqrt(size))
        for x in range(0, size, root):
            dict = self.get_possibles(self.boxes[x:x+root])
            for each in dict:
                occur = dict.get(each)
                if occur == 2 or occur == 3: #potential laser
                    # Scan Square to see if number of squares containing
                    # 'each' as a possible is equal to 'occur'. If so, laser.
                    squareTotal = self.find_occurances(each,
                                                       self.boxes[x].\
                                                           square.boxes)
                    if occur == squareTotal: #laser!
                        currSquare = self.boxes[x].square
                        # Scan the whole row again and cancel out
                        # possibles equal to 'each'.
                        for box in self.boxes:
                            if box.square is not currSquare:
                                if each in box.possibles:
                                    box.possibles.remove(each)
                                    Area.tertiary += 1

    def area_solved(self):
        '''Checks if the numbers 1 to 9 are present in the Area.'''
        result = True
        items = {box.num for box in self.boxes}
        # Check the set for 1 to 9.
        for x in range(1, len(items)+1):
            if x not in items:
                result = False
                break
        return result

    def print_area(self):
        '''Prints this Area.'''
        for each in self.boxes:
            if each.num == 0:
                digit = ' '
            else:
                digit = each.num
            print('|', digit, end=' ')
        print('|')

    def add_numbers(self, items):
        '''Given a list of ints, sets the number
        of the boxes contained in this Area.
        '''
        for x in range(0, len(items)):
            self.boxes[x].num = items[x]
            if items[x] != 0:
                # The number is already solved.
                self.boxes[x].possibles = []
                Area.starting += 1

    def print_possibles(self):
        '''Prints the possibles of all Boxes in this Area.
        Used mainly for testing.
        '''
        for each in self.boxes:
            print("Num: {0} - Possibles: {1}".format(each.num, each.possibles))

class Box:
    '''This is a square on the Sudoku board.'''
    dim = None  # The dimension of the board. Why does a Box need to know this?

    def __init__(self, dim, row, col, square):
        if not Box.dim:
            Box.dim = dim
        self.num = 0  # The actual number in the box.
        self.possibles = [x for x in range(1, (Box.dim**2) + 1)]
        self.row = row
        self.col = col
        self.square = square

    def reset_box(self):
        '''Resets this Box to its original state.'''
        self.num = 0
        self.possibles = [x for x in range(1, (Box.dim**2) + 1)]

    def set_num(self, num):
        '''Sets the solved number and clears the possibles.'''
        self.num = num
        self.possibles = []

    def update_wave(self):
        '''Checks all Boxes in all areas this Box is in.'''
        updates = []
        areas = (self.row, self.col, self.square)
        for each in areas:
            updates.extend(each.update())
        return updates

# Go.
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Bad args.')
    else:
        board = Board()
        board.read_board(sys.argv[1])
