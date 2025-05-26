#!/usr/bin/env python3

import os
import asyncio
import curses
from datetime import datetime

TIMER_Y_COR = 1
TIMER_X_COR = 1
KEYCODE_Y_COR = 5
KEYCODE_X_COR = 1

MESSAGE = """This is a simple program to get familiar with the main capabilities 
of the Python AsyncIO module and the curses library.

It reads key pressing and displays time in the background.

The aim was to utilize all main asyncio mechanisms, 
so some parts of the code may look like over-engineering. 
"""


def curses_print(
    stdscr: curses.window, y: int, x: int, line: str, color_pair: int = 0
) -> None:
    """
    Print string on the screen at given coordinates
    Clears existing text line
    """
    stdscr.move(y, x)
    stdscr.clrtoeol()
    stdscr.addstr(y, x, line, curses.color_pair(color_pair))
    stdscr.refresh()


DateTimeQueue = asyncio.Queue[datetime]


async def timer_generator(timer_queue: DateTimeQueue) -> None:
    """
    Generates a new timestamp every second and sends it to the queue
    """
    while True:
        now = datetime.now()
        await timer_queue.put(now)
        await asyncio.sleep(1)


async def timer_echo(stdscr: curses.window, timer_queue: DateTimeQueue) -> None:
    """
    Simple async task infinitely printing current time
    """
    while True:
        now = await timer_queue.get()
        current_time = now.strftime("%H:%M:%S")
        timer_queue.task_done()
        curses_print(
            stdscr,
            TIMER_Y_COR,
            TIMER_X_COR,
            f"Current Time = {current_time}",
            color_pair=1,
        )


async def read_key(stdscr: curses.window) -> int:
    """
    Async function waiting for a key press and returning key code
    """
    k = curses.ERR
    while k == curses.ERR:
        await asyncio.sleep(0.01)  # async waiting
        k = stdscr.getch()  # This call is non-blocking with curses.halfdelay() mode
    return k


async def clear_key(stdscr: curses.window, countdown_seconds: float) -> None:
    """
    Clears pressed key after countdown seconds
    """
    await asyncio.sleep(countdown_seconds)
    curses_print(
        stdscr,
        KEYCODE_Y_COR,
        KEYCODE_X_COR,
        f"No key pressing detected in last {countdown_seconds} seconds",
    )


async def echo_key(stdscr: curses.window) -> None:
    """
    Async task catching key press and displaying key code
    The logic here is not quite usable for queue, so this part works without queue
    """
    clear_key_task = None
    while True:
        k = await read_key(stdscr)  # Async waiting for a pressed key
        if k == 27:
            break
        keystr = "Last key pressed: {}".format(k)
        curses_print(stdscr, KEYCODE_Y_COR, KEYCODE_X_COR, keystr)
        # Now we need to start the task cleaning key message after some delay
        if (
            clear_key_task is not None and not clear_key_task.done()
        ):  # If we have active task - cancelling it
            clear_key_task.cancel()
        clear_key_task = asyncio.create_task(
            clear_key(stdscr, countdown_seconds=2)
        )  # Starting the new task to reset clearing timer

    # Cancelling the active clearing task if needed
    if clear_key_task is not None and not clear_key_task.done():
        clear_key_task.cancel()
    stdscr.clear()
    stdscr.refresh()


def curses_init(stdscr: curses.window) -> None:
    """
    Initializes the curses library settings for the provided curses window.
    """
    # Set non-blocking mode for key reading
    curses.halfdelay(1)
    # curses.cbreak() - not working, don't know why
    # Do not echo keys back to the client.
    curses.noecho()
    # Turn off blinking cursor
    curses.curs_set(False)
    # Optional - Enable the keypad. This also decodes multi-byte key sequences
    stdscr.keypad(True)
    # Enable color if we can...
    if curses.has_colors():
        curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)


def curses_shutdown(stdscr: curses.window) -> None:
    """
    Safely shuts down the curses application and restores the
    terminal to its original state.
    """
    # Enabling buffering mode
    curses.nocbreak()
    # Turn echo back on.
    curses.echo()
    # Restore cursor blinking.
    curses.curs_set(True)
    # Turn off the keypad...
    stdscr.keypad(False)
    # Restore Terminal to original state.
    curses.endwin()


async def main(stdscr: curses.window) -> None:
    """
    Initializes a curses window, sets up a
    producer-consumer queue for handling timer events through asyncio, processes
    keyboard input, and cleans up before exiting.
    """
    curses_init(stdscr)

    # Creating producer-consumer queue for timer
    timer_queue: DateTimeQueue = asyncio.Queue(maxsize=100)
    timer_generator_task = asyncio.create_task(timer_generator(timer_queue))
    timer_echo_task = asyncio.create_task(timer_echo(stdscr, timer_queue))

    curses_print(stdscr, KEYCODE_Y_COR, KEYCODE_X_COR, f"No key pressing detected")

    await echo_key(stdscr)

    # Shutting down producer-consumer queue for timer
    timer_generator_task.cancel()
    await timer_queue.join()
    timer_echo_task.cancel()

    curses_shutdown(stdscr)


async def main_wrapper() -> None:
    os.environ.setdefault("ESCDELAY", "25")
    await curses.wrapper(main)


if __name__ == "__main__":
    asyncio.run(main_wrapper())
