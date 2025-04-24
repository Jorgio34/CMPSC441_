import random

class Room:
    def __init__(self, description, has_monster=False, has_trap=False, has_treasure=False):
        self.description = description
        self.has_monster = has_monster
        self.has_trap = has_trap
        self.has_treasure = has_treasure
        self.exits = {"north": None, "south": None, "east": None, "west": None}

    def set_exit(self, direction, room):
        self.exits[direction] = room

    def __str__(self):
        return f"{self.description} {'(Monster)' if self.has_monster else ''} {'(Trap)' if self.has_trap else ''} {'(Treasure)' if self.has_treasure else ''}"

class DungeonMasterAgent:
    def __init__(self, size=5):
        self.dungeon = self.create_dungeon(size)
        self.player_position = (0, 0)  # starting at the top-left corner

    def create_dungeon(self, size):
        dungeon = {}
        for row in range(size):
            for col in range(size):
                description = f"Room at ({row},{col})"
                has_monster = random.choice([True, False])
                has_trap = random.choice([True, False])
                has_treasure = random.choice([True, False])
                room = Room(description, has_monster, has_trap, has_treasure)
                dungeon[(row, col)] = room
        # Connect rooms (basic grid setup)
        for row in range(size):
            for col in range(size):
                if row < size - 1:
                    dungeon[(row, col)].set_exit("south", dungeon[(row + 1, col)])
                if col < size - 1:
                    dungeon[(row, col)].set_exit("east", dungeon[(row, col + 1)])
        return dungeon

    def move_player(self, direction):
        current_room = self.dungeon[self.player_position]
        next_room = current_room.exits.get(direction)
        if next_room:
            self.player_position = (self.player_position[0] + (1 if direction == "south" else 0),
                                    self.player_position[1] + (1 if direction == "east" else 0))
            print(f"Moved to {next_room}")
            return next_room
        else:
            print("Can't move in that direction.")
            return current_room

    def show_room(self):
        current_room = self.dungeon[self.player_position]
        print(f"You are in: {current_room}")
        if current_room.has_monster:
            print("A monster is lurking!")
        if current_room.has_trap:
            print("Beware of a trap!")
        if current_room.has_treasure:
            print("You see some treasure!")
