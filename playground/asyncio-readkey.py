#!/usr/bin/env python3

import asyncio
import curses
from datetime import datetime

timer_y, timer_x = 0, 0
key_y, key_x = 10, 0


def curses_print(
    stdscr: curses.window, y: int, x: int, line: str, color_pair: int = 0
) -> None:
    """
    Prints string on the screen at given coordinates
    """
    stdscr.move(y, x)
    stdscr.clrtoeol()
    stdscr.addstr(y, x, line, curses.color_pair(color_pair))
    stdscr.refresh()


async def timer_echo(stdscr: curses.window) -> None:
    """
    Simple async task infinitely printing current time
    """
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        curses_print(
            stdscr, timer_y, timer_x, f"Current Time = {current_time}", color_pair=1
        )
        await asyncio.sleep(1)


async def read_key(stdscr: curses.window) -> int:
    """
    Async function waiting for a key press and returning key code
    """
    k = curses.ERR
    while k == curses.ERR:
        await asyncio.sleep(0.01)  # async waiting
        k = stdscr.getch()  # This call is non-blocking with curses.halfdelay() mode
    return k


async def clear_key(stdscr: curses.window, countdown: float) -> None:
    """
    Clears pressed key after countdown seconds
    """
    await asyncio.sleep(countdown)
    curses_print(
        stdscr, key_y, key_x, f"No key pressing detected in last {countdown} seconds"
    )


async def echo_key(stdscr: curses.window) -> None:
    """
    Async task catching key press and displaying key code
    """
    key_reset_task = None
    while True:
        k = await read_key(stdscr)
        keystr = "Last key pressed: {}".format(k)
        curses_print(stdscr, key_y, key_x, keystr)
        if k == ord("q"):
            break
        if key_reset_task is not None:
            if not key_reset_task.done():
                key_reset_task.cancel()
        key_reset_task = asyncio.create_task(clear_key(stdscr, 1))

    stdscr.clear()
    stdscr.refresh()
    if key_reset_task is not None:
        if not key_reset_task.done():
            key_reset_task.cancel()


def curses_init(stdscr: curses.window) -> None:
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
    curses_init(stdscr)

    timer_task = asyncio.create_task(timer_echo(stdscr))
    curses_print(stdscr, key_y, key_x, f"No key pressing detected")
    await echo_key(stdscr)
    timer_task.cancel()

    curses_shutdown(stdscr)


async def main_wrapper() -> None:
    await curses.wrapper(main)


if __name__ == "__main__":
    asyncio.run(main_wrapper())
