#!/usr/bin/env python3
# coding=utf-8
# ライフゲームをCPUで動作させるためのプログラムです．

# イベント駆動アプリを作成することができるライブラリ
import numpy
import curses
from curses import wrapper
import sys
import time

row2str = lambda row: ''.join(['O' if c != 0 else ' ' for c in row])
cell_value = lambda world, height, width, y, x: world[y % height, x % width]
death_cell_next_state = lambda num_live: 1 if num_live == 3 else 0
life_cell_next_state = lambda num_live: 1 if num_live == 2 or num_live == 3 else 0
cell_next_state = lambda current_value, num_live: death_cell_next_state(num_live) if current_value == 0 else life_cell_next_state(num_live)
num_live_counter = lambda world, height, width, y, x: (   cell_value(world, height, width, y - 1, x - 1) + cell_value(world, height, width, y - 1, x)
                                                        + cell_value(world, height, width, y - 1, x + 1) + cell_value(world, height, width, y, x - 1)
                                                        + cell_value(world, height, width, y, x + 1)     + cell_value(world, height, width, y + 1, x - 1)
                                                        + cell_value(world, height, width, y + 1, x)     + cell_value(world, height, width, y + 1, x + 1) )

def print_world(stdscr, world, generation, elapsed):
    height, width = world.shape
    for y in range(height):
        row = world[y]
        stdscr.addstr(y, 0, row2str(row))
    stdscr.addstr(height, 0, "Generation: %06d, Elapsed: %.6f[sec]" % (generation, elapsed / generation))
    stdscr.refresh()

def set_next_cell_value(world, next_world, height, width, y, x):
    current_value = cell_value(world, height, width, y, x)
    next_value = current_value
    #　隣接セルで生存しているセル数を確認する
    num_live = num_live_counter(world, height, width, y, x)
    next_world[y][x] = cell_next_state(current_value, num_live)
    

def calc_next_world(world, next_wolrd):
    height, width = world.shape
    for y in range(height):
        for x in range(width):
            set_next_cell_value(world, next_wolrd, height, width, y, x)

def lifegame(stdscr, height, width):
    # 初期世界の生成
    # numpy.random.seed(seed=32)
    world = numpy.random.randint(2, size=(height, width), dtype=numpy.int32)

    # 次の世界の生成
    next_world = numpy.empty((height, width), dtype=numpy.int32)

    # 世界の更新を行いつつ表示を行う
    elapsed = 0.0
    generation = 0
    while generation < 200 :
        generation += 1
        print_world(stdscr, world, generation, elapsed)
        start_time = time.time()
        calc_next_world(world, next_world)
        end_time = time.time()
        elapsed += end_time - start_time
        world, next_world = next_world, world
    with open('cpu_result.txt', 'w') as f:
        print("Height:%d, Width:%d" % (height, width), file=f)
        print("Number of trials: %d" % generation, file=f)
        print("mean_time: %f" % (elapsed / generation), file=f)

def main(stdscr):
    stdscr.clear()
    stdscr.nodelay(True)
    scr_height, scr_width = stdscr.getmaxyx()
    lifegame(stdscr, scr_height - 1, scr_width)

if __name__ == '__main__':
    curses.wrapper(main)