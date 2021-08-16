import asyncio
import os
import discord
import datetime
import random
import re
import threading
from discord.ext import tasks
from dotenv import load_dotenv

load_dotenv()
TOKEN: str = os.getenv('DISCORD_TOKEN')
TIME_DIFF: datetime.timedelta = datetime.timedelta(hours=4)
OFFSET: datetime.timedelta = datetime.timedelta(hours=2)

client: discord.Client = discord.Client()

def log(*args: str, **kwargs):
	# literally just a print() but with a date and time marker
	print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]:", *args, **kwargs)

async def update_status_on_input():
	while True: await update_status(input("\r"), is_regex=True)

input_thread = threading.Thread(target=asyncio.run, args=(update_status_on_input(),))

@client.event
async def on_ready():
	log(f'{client.user} has connected to Discord!')
	await update_status()
	if not input_thread.is_alive(): input_thread.start()
	if not update_status.is_running():
		update_status.start()
		log(f"started task")

@tasks.loop(seconds=TIME_DIFF.seconds)
async def update_status(status: str = None, is_regex: bool = False):
	with open("./discord_statuses.txt", "r+", encoding='utf8') as f:
		if status is None: line: str = random.choice(f.readlines())
		else:
			if not is_regex:
				lines = list(filter(lambda x: status.lower() in x.lower(), f.readlines()))
			else:
				try: regex = re.compile(status)
				except re.error: return print(f"invalid regex expression '{status}'")
				lines = list(filter(lambda x: regex.search(x) is not None, f.readlines()))
			if len(lines) == 0: return print(f"status with '{status}' not found")
			line: str = random.choice(list(lines))
		await client.change_presence(activity=discord.Activity(type=4, state=line[:-1][:128], name="this isnt actually used"))
		log(f"set status to '{line[:-1][:128]}'")

@update_status.before_loop
async def delay_status_update():
	# waits until the next multiple of time_difference
	def get_time_to_wait_until(time_difference: datetime.timedelta) -> datetime.datetime:
		now: datetime.datetime = datetime.datetime.now()
		this_morning: datetime.datetime = now.replace(hour=0,minute=0,second=0,microsecond=0)
		
		i: datetime.datetime = this_morning + OFFSET
		while i < now:
			i += time_difference
		
		return i
	
	seconds_to_wait: int = (get_time_to_wait_until(TIME_DIFF)-datetime.datetime.now()).seconds
	
	log(f"waiting {seconds_to_wait} seconds until next status change")
	
	await asyncio.sleep(seconds_to_wait+1)

client.run(TOKEN, bot=False)