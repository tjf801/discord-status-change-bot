import asyncio
import os
import discord
import datetime
import random
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

@client.event
async def on_ready():
	log(f'{client.user} has connected to Discord!')
	update_status.start()
	log(f"started task")

@tasks.loop(seconds=TIME_DIFF.seconds)
async def update_status():
	with open("./discord_statuses.txt", "r+", encoding='utf8') as f:
		line: str = random.choice(f.readlines())
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
	
	log(f"waiting {seconds_to_wait} seconds until first status change")
	
	await asyncio.sleep(seconds_to_wait)

client.run(TOKEN, bot=False)