#!/usr/bin/env python3

import random, asyncio


async def main():
    async def print_num(n: int) -> None:
        print(f"Starting async task {n}")
        interval = random.uniform(1, 2)
        # time.sleep(interval) - syncronis sleep - wrong way. All asyncs will have to wait
        await asyncio.sleep(interval)  # Async sleep - returns to the event loop
        return n

    tasks = [print_num(i) for i in range(5)]

    for task in asyncio.as_completed(tasks, timeout=10):
        # get the next result
        result = await task
        print(f"Task {result} finished")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
