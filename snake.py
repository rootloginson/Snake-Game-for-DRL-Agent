import pygame
import random
from enum import Enum
import numpy as np


DISPLAY_WIDTH = 600
DISPLAY_HEIGHT = 600
DISPLAY_DIMENSIONS = (DISPLAY_WIDTH, DISPLAY_HEIGHT)
BLOCK_SIZE = 20
GAME_AREA_PERCENTAGE = 90


class Directions(Enum):
    LEFT = 1
    RIGHT = 2
    UP = 3
    DOWN = 4


class GameDisplay:
    def __init__(self, w, h):
        self.w = w
        self.h = h


class GameArea(GameDisplay):
    def __init__(self, w, h, block_size, game_area_percentage):
        super().__init__(w, h)
        self.block_size = block_size
        self.game_area_percentage = game_area_percentage
        game_area_pos, number_of_blocks = self._calculate_game_area()
        self.game_area_width_pos, self.game_area_height_pos = game_area_pos
        # number of blocks in x and y axis in game box
        self.x_max_block, self.y_max_block = number_of_blocks
        # game box boundary positions
        self.x_start, self.x_end = self.game_area_width_pos
        self.y_start, self.y_end = self.game_area_height_pos
        self.box_w = self.x_end - self.x_start
        self.box_h = self.y_end - self.y_start
        self.draw_game_box()

    def _calculate_game_area(self):
        g_thickness_w = (self.w // 100) * (100-self.game_area_percentage) / 2
        g_thickness_h = (self.h // 100) * (100-self.game_area_percentage) / 2
        w_pos = (0+g_thickness_w, self.w-g_thickness_w)
        h_pos =(0+g_thickness_h, self.w-g_thickness_h)
        no_of_block_w = (w_pos[1] - w_pos[0]) // self.block_size
        no_of_block_h = (h_pos[1] - h_pos[0]) // self.block_size
        game_w_pos = (w_pos[0], w_pos[0] + no_of_block_w * self.block_size)
        game_h_pos = (h_pos[0], h_pos[0] + no_of_block_h * self.block_size)
        return [game_w_pos, game_h_pos], [no_of_block_w, no_of_block_h]

    def get_positions(self):
        return self.game_area_width_pos, self.game_area_height_pos

    def fractional_position(self, val_x, val_y):
        # returns the closest block position
        if val_x > 0.9:
            val_x = 0.9
        if val_y > 0.9:
            val_y = 0.9
        x = self.x_start + round(self.x_max_block * val_x) * self.block_size
        y = self.y_start + round(self.y_max_block * val_y) * self.block_size
        return x, y

    def random_block_position(self):
        x = self.x_start + random.randint(0, self.x_max_block-1) * self.block_size
        y = self.y_start + random.randint(0, self.y_max_block-1) * self.block_size
        return x, y

    def draw_game_box(self):
        pygame.draw.aaline(screen, (0,255,0), (self.x_start, self.y_start), (self.x_end, self.y_start))
        pygame.draw.aaline(screen, (0,255,0), (self.x_start, self.y_start), (self.x_start, self.y_end))
        pygame.draw.aaline(screen, (0,255,0), (self.x_end, self.y_start), (self.x_end, self.y_end))
        pygame.draw.aaline(screen, (0,255,0), (self.x_start, self.y_end), (self.x_end, self.y_end))


class RLReward:
    def __init__(self, game_over, eat_food, no_result):
        self.game_over = game_over
        self.eat_food = eat_food
        self.no_result = no_result


class Controls:
    @classmethod
    def get_user_input(cls, event):
        if event.type == pygame.QUIT:
            pygame.quit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                return Directions.RIGHT
            elif event.key == pygame.K_LEFT:
                return Directions.LEFT
            elif event.key == pygame.K_UP:
                return Directions.UP
            elif event.key == pygame.K_DOWN:
                return Directions.DOWN
            else:
                print("Not a direction input.")
                print("Not a quit input")
            return None


class Snake():
    def __init__(self, game_area_instance, reward_instance):
        self.ga = game_area_instance
        self.reward = reward_instance
        init_head = ga.fractional_position(1/3, 1/2)
        self.snake = [
                [init_head[0], init_head[1]],
                [init_head[0] - BLOCK_SIZE, init_head[1]],
                [init_head[0] - BLOCK_SIZE*2, init_head[1]]
                ]
        self.food = [
                *ga.fractional_position(np.random.uniform(1/3,1),
                                       np.random.uniform(1/2,1))
                ]
        self.tail = None
        self.snake_direction = Directions.RIGHT
        self.score = 0
        self.snake_unallowed_moves = {
                            Directions.RIGHT: Directions.LEFT,
                            Directions.LEFT: Directions.RIGHT,
                            Directions.UP: Directions.DOWN,
                            Directions.DOWN: Directions.UP
                            }

    def update_snake_position(self, user_command):
        x = self.snake[0][0]
        y = self.snake[0][1]
        if user_command is None:
            pass
        elif self.snake_unallowed_moves[user_command] == self.snake_direction:
            pass
        elif user_command in Directions:
            self.snake_direction = user_command
        else:
            print("Unexpected user command")
        if self.snake_direction == Directions.RIGHT:
            x += BLOCK_SIZE
        elif self.snake_direction == Directions.LEFT:
            x += -BLOCK_SIZE
        elif self.snake_direction == Directions.DOWN:
            y += BLOCK_SIZE
        elif self.snake_direction == Directions.UP:
            y += -BLOCK_SIZE
        else:
            print("snake location update error")
        self.snake.insert(0, [x,y])
        self.tail = self.snake.pop()

    def did_it_collide(self):
        head = self.snake[0]
        game_over = True
        # check if head of snake hits its own body
        if head in self.snake[1:]:
            return game_over, self.reward.game_over
        # check if head of snake hits wall
        if head[0] < ga.x_start or head[0] > ga.x_end-BLOCK_SIZE:
            return game_over, self.reward.game_over
        if head[1] < ga.y_start or head[1] > ga.y_end-BLOCK_SIZE:
            return game_over, self.reward.game_over
        return False, self.reward.no_result

    def is_foot_eaten(self):
        game_state = False
        if self.snake[0] == self.food:
            self.place_new_food()
            self.score += self.reward.eat_food
            # if self.score%30 == 0 and self.score != 0:
            self.snake.append(self.tail)
            return game_state, self.reward.eat_food
        return game_state, self.reward.no_result

    def place_new_food(self):
        food_coordinate = [*self.ga.random_block_position()]
        while food_coordinate in self.snake:
            food_coordinate = [*self.ga.random_block_position()]
        self.food = food_coordinate

    def play_step(self):
        user_command = None
        for event in pygame.event.get():
            user_command = Controls.get_user_input(event)
        self.update_snake_position(user_command)
        game_state, reward = self.did_it_collide()
        if game_state:
            return game_state, reward
        if not game_state:
            game_state, reward = self.is_foot_eaten()
        food = self.food[:]
        screen.fill((0,0,0))
        self.ga.draw_game_box()
        for part in self.snake:
            pygame.draw.rect(
                            screen, (255,255,255),
                            pygame.Rect(part[0], part[1], BLOCK_SIZE, BLOCK_SIZE)
                            )
        pygame.draw.rect(
                        screen, (255,0,0),
                        pygame.Rect(food[0], food[1], BLOCK_SIZE, BLOCK_SIZE)
                        )
        pygame.draw.circle(screen, (0,255,0), (self.snake[0]), 3)
        text = font.render("Score: " + str(self.score), True, (255,255,255))
        screen.blit(text, [0,0])
        pygame.display.flip()
        clock.tick(10)
        return game_state, reward


if __name__ == '__main__':
    # initialize pygame
    pygame.init()
    screen = pygame.display.set_mode(DISPLAY_DIMENSIONS)
    # a = pygame.font.get_fonts().sort() gives the font names
    font = pygame.font.SysFont('timesnewroman', 24)
    clock = pygame.time.Clock()

    # Game area positions
    ga = GameArea(*DISPLAY_DIMENSIONS, BLOCK_SIZE, GAME_AREA_PERCENTAGE)

    reward = RLReward(game_over=-10, eat_food=10, no_result=0)
    snake = Snake(ga, reward)
    while True:
        game_state, reward = snake.play_step()
        if game_state:
            break
    print(f"Total score: {snake.score}")
    pygame.quit()
