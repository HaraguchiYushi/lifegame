import pycuda.gpuarray as gpuarray
import pycuda.driver as cuda
import pycuda.autoinit
import numpy
import time
import curses
from curses import wrapper
import itertools
import os

from pycuda.compiler import SourceModule

## CUDAカーネルを定義
mod = SourceModule("""
__global__ void world_update_gpu(const int* world, int* next_world, int width, int height) {
    int x = threadIdx.x + blockIdx.x * blockDim.x;
    int y = threadIdx.y + blockIdx.y * blockDim.y;
    if (x >= width) {
        return;
    }
    if (y >= height) {
        return;
    }
    const int index = y * width + x;
    int current_value = world[index];
    int next_value;
    int num_live = 0;
    num_live += world[( (y - 1) % height ) * width + ( (x - 1) % width )];
    num_live += world[( (y - 1) % height ) * width + ( (x    ) % width )];
    num_live += world[( (y - 1) % height ) * width + ( (x + 1) % width )];
    num_live += world[( (y    ) % height ) * width + ( (x - 1) % width )];
    num_live += world[( (y    ) % height ) * width + ( (x + 1) % width )];
    num_live += world[( (y + 1) % height ) * width + ( (x - 1) % width )];
    num_live += world[( (y + 1) % height ) * width + ( (x    ) % width )];
    num_live += world[( (y + 1) % height ) * width + ( (x + 1) % width )];
    if(current_value == 0) {
        if(num_live == 3) {
            next_value = 1;
        } else {
            next_value = 0;
        }
    } else {
        if(num_live <= 1) {
            next_value = 0;
        } else if(num_live >= 4) {
            next_value = 0;
        } else {
            next_value = 1;
        }
    }
    next_world[index] = next_value;
}
""")

BLOCKSIZE = 32
GPU_NITER = 10

MAT_SIZE_X = 100
MAT_SIZE_Y = 100

row2str = lambda row: ''.join(['O' if c != 0 else ' ' for c in row])

def print_world(stdscr, world, generation, elapsed):
    height, width = world.shape
    for y in range(height):
        row = world[y]
        stdscr.addstr(y, 0, row2str(row))
    stdscr.addstr(height, 0, "Generation: %06d, Elapsed: %.6f[sec]" % (generation, elapsed / generation))
    stdscr.refresh()

def exe_lifegame(world, next_world, stdscr, height, width):
    # cudaを利用するための初期設定
    start = cuda.Event()
    end = cuda.Event()
    world_update_gpu = mod.get_function("world_update_gpu")
    block = (BLOCKSIZE, BLOCKSIZE, 1)
    grid = ((width + block[0] - 1) // block[0], (height + block[1] - 1) // block[1])

    elapsed = 0.0
    generation = 0
    while generation < 200 :
        generation += 1
        start.record()
        for i in range(GPU_NITER):
            world_update_gpu(cuda.In(world), cuda.Out(next_world), numpy.int32(width), numpy.int32(height), block = block, grid = grid)
        end.record()
        end.synchronize()
        cuda.Context.synchronize()
        elapsed += (start.time_till(end) * 1e-3 / GPU_NITER)
        # 画面の表示
        print_world(stdscr, world, generation, elapsed)
        world, next_world = next_world, world
    with open('gpu_result.txt', 'w') as f:
        print("Height:%d, Width:%d" % (height, width), file=f)
        print("Number of trials: %d" % generation, file=f)
        print("mean_time: %f" % (elapsed / generation), file=f)

def lifegame(stdscr, height, width):
    # 初期世界の生成
    # numpy.random.seed(seed=32)
    world = numpy.random.randint(2, size=(height, width), dtype=numpy.int32)

    # 次の世界の生成
    next_world = numpy.empty((height, width), dtype=numpy.int32)

    # 世界の更新を行いつつ表示を行う
    exe_lifegame(world, next_world, stdscr, height, width)

def main(stdscr):
    stdscr.clear()
    stdscr.nodelay(True)
    scr_height, scr_width = stdscr.getmaxyx()
    lifegame(stdscr, scr_height - 1, scr_width)

if __name__ == '__main__':
    curses.wrapper(main)