#!/usr/local/bin/python3
#
# natural_selection.py
# Patate
"""
Problems:
    - two things can't be at the same place
"""
import math
import random

def normalize_vector(vec, fillvalue=1):
    new_vec = []
    for val in vec:
        if val > 0:
            new_vec.append(fillvalue)
        elif val == 0:
            new_vec.append(0)
        elif val < 0:
            new_vec.append(-fillvalue)

    return new_vec

class GridObj:
    @property
    def x(self):
        return self.coords[0]

    @property 
    def y(self):
        return self.coords[1]

class Patate(GridObj):
    def __init__(self, coords, speed=1):
        self.coords = coords
        self.speed  = speed

        self.eaten_count = 0

    def find_nearest_candy(self, board):
        min_distance = 999
        nearest_candy = None

        for candy in board.candies:
            distance = math.sqrt((self.x - candy.x)**2 + (self.y - candy.y)**2)
            if distance < min_distance:
                min_distance = distance
                nearest_candy = candy

        return nearest_candy

    def next_step(self, board):
        nearest_candy = self.find_nearest_candy(board)
        print("nearest candy:", nearest_candy.coords)

        vec_to_candy  = [nearest_candy.x - self.x, nearest_candy.y - self.y]
        print("Vec to candy:", vec_to_candy)
        norm_vec      = normalize_vector(vec_to_candy, fillvalue=self.speed)
        print("Normed:", norm_vec)

        if norm_vec[0] > vec_to_candy[0] and norm_vec[1] > vec_to_candy[1]:
            return vec_to_candy

        return norm_vec

    def can_eat(self, board):
        for candy in board.candies:
            if candy.coords == self.coords:
                return candy

        return False


class Candy(GridObj):
    def __init__(self, coords):
        self.coords = coords

class Board:

    def __init__(self, size, init_potatoes_nb=5, init_candies_nb=10):
        """
        Board object, hold squares and pawns
        """

        self.size = size

        self.grid = []
        self.potatoes = []
        self.candies  = []

        self.init_potatoes_nb = init_potatoes_nb
        self.init_candies_nb  = init_candies_nb

        self.init_grid()

    def init_grid(self):

        self.grid = []

        for y in range(self.size[1]):
            line = []
            for x in range(self.size[0]):
                line.append(None)

            self.grid.append(line)

    def add_potato(self, x, y):
        potato = Patate([x, y])
        self.grid[y][x] = potato
        self.potatoes.append(potato)

    def add_candy(self, x, y):
        candy = Candy([x, y])
        self.grid[y][x] = candy
        self.candies.append(candy)

    def del_candy(self, candy):
        #self.grid[candy.y][candy.x] = None
        self.candies.remove(candy)

    def del_potato(self, potato):
        self.grid[potato.y][potato.x] = None
        self.potatoes.remove(potato)

    def move_potato(self, potato, new_pos):

        print("next Pos:", new_pos)
        self.grid[potato.y][potato.x] = None
        self.grid[new_pos[1]][new_pos[0]] = potato
        potato.coords = new_pos

    def first_gen(self):
        self.init_grid()

        # Create a list of all possible places on the map
        possible_places = []
        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                possible_places.append([i,j])

        random.shuffle(possible_places)

        # Put 10 candies at random places
        for _ in range(self.init_candies_nb):
            candy_loc = possible_places.pop()
            self.add_candy(*candy_loc)

        for _ in range(self.init_potatoes_nb):
            potato_loc = possible_places.pop()
            self.add_potato(*potato_loc)

    def next_gen(self):
        self.init_grid()
        # Create a list of all possible places on the map
        possible_places = []
        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                possible_places.append([i,j])

        random.shuffle(possible_places)

        # Put 10 candies at random places
        for _ in range(self.init_candies_nb):
            candy_loc = possible_places.pop()
            self.add_candy(*candy_loc)

        for potato in self.potatoes:
            # Delete dead potatoes
            if potato.eaten_count == 0:
                self.del_potato(potato)

            # Spawn new potatoes
            elif potato.eaten_count > 1:
                potato_loc = possible_places.pop()
                self.add_potato(*potato_loc)

            # Reset eaten count
            potato.eaten_count = 0


    def __repr__(self):
        box_size = 4
        border   = 1
        # First line = x coords
        msg = "\t" 
        for xcoord in range(len(self.grid[0])):
            msg += str(xcoord).center(box_size)

        msg += "\n"
        
        # Line 2 : border up
        msg += "\t" + "#"*(self.size[0]*box_size + border*2)
        msg += "\n"
        for row_ix, row in enumerate(self.grid):
            msg += "{}\t".format(row_ix)+"#"*border
            for val in row:
                if val is None:
                    printed = " "
                elif type(val) == Patate:
                    printed = "P"
                elif type(val) == Candy:
                    printed = "O"
                else:
                    print(type(val))
                    sys.exit(0)
                msg += " {} #".format(printed)


            msg += "#"*border
            msg += "\n"

        msg += "\t" + "#"*(self.size[0]*box_size + border*2)

        return msg


def natural_selection(board, nb_gen=10):

    board.first_gen()
    for gen_ix in range(nb_gen):
        stop_gen = False
        while not stop_gen:
            print(board)
            for potato in board.potatoes:
                # Find next step and move potato 
                next_step = potato.next_step(board)
                potato_pos = [
                    potato.coords[0] + next_step[0],
                    potato.coords[1] + next_step[1]
                             ]
                board.move_potato(potato, potato_pos)

                # Potatoes can eat
                eatable = potato.can_eat(board)
                if eatable:
                    potato.eaten_count += 1
                    print(potato.eaten_count)
                    board.del_candy(eatable)

            # No candies left
            if len(board.candies) == 0:
                stop_gen = True

            print(board.potatoes[0].coords)
            input('...')

        board.next_gen()
        print("Gen {}, {} potatoes alive".format(gen_ix, len(board.potatoes)))


board = Board((10,10), init_potatoes_nb=2)
natural_selection(board)
