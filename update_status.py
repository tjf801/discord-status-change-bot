import asyncio
import os
import discord
import datetime
import json
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

async def parse_command(raw_command_text: str):
	assert raw_command_text[0] == '!'
	
	command, args, text = re.match("!([a-zA-Z]+)?(\{.*\})? ?(.*)\n", raw_command_text).groups()
	
	default_args = {"name": text, "start": datetime.datetime.now()}
	command_args = {**default_args, **(eval(args) if args is not None else {})}
	
	activity = None
	
	if command=="playing":
		activity = discord.Game(**command_args)
		log(f"set status to Playing '{text}'")
	
	elif command=="streaming":
		activity = discord.Streaming(**command_args)
		log(f"set status to Streaming '{text}' at {command_args['url']}")
	
	elif command=="listening":
		activity = discord.Activity(type=discord.ActivityType.listening, **command_args)
		log(f"set status to Listening to '{text}'")
	
	elif command=="watching":
		activity = discord.Activity(type=discord.ActivityType.watching, **command_args)
		log(f"set status to Watching '{text}'")
	
	elif command=="competing":
		activity = discord.Activity(type=discord.ActivityType.competing, **command_args)
		log(f"set status to Competing in '{text}'")
	
	elif command=='py':
		custom_args = {"state": eval(text), **command_args, "name": "not used"}
		activity = discord.Activity(type=discord.ActivityType.custom, **custom_args)
		log(f"set status to '{custom_args['state'][:128]}'")
	
	elif command is None:
		custom_args = {"state": default_args['name'], **command_args, "name": "not used"}
		activity = discord.Activity(type=discord.ActivityType.custom, **custom_args)
		log(f"set status to '{custom_args['state'][:128]}'")
	
	else: raise NameError(f"\033[31munknown command \033[36m{command}\033[00m")
	
	await client.change_presence(activity=activity, afk=True)

@tasks.loop(seconds=TIME_DIFF.seconds)
async def update_status(status: str = None, is_regex: bool = False):
	with open("./discord_statuses.txt", "r+", encoding='utf8') as f:
		if status is None: line: str = random.choice(f.readlines())
		else:
			if not is_regex:
				lines = list(filter(lambda x: status.lower() in x.lower(), f.readlines()))
			else:
				try: regex = re.compile(status)
				except re.error: return print(f"\033[31minvalid regex expression '\033[36m{status}\033[31m'\033[00m")
				lines = list(filter(lambda x: regex.search(x) is not None, f.readlines()))
			if len(lines) == 0: return print(f"\033[31mstatus with '\033[36m{status}\033[31m' not found\033[00m")
			line: str = random.choice(list(lines))
		
		if line[0] == '!': await parse_command(line)
		else:
			#NOTE: why the FUCK does discord.py need `name` to be a non-empty string specifically
			#AGHHHHHHHHH i hate this api
			await client.change_presence(activity=discord.Activity(type=discord.ActivityType.custom, state=line[:-1][:128], name="this is not used"), afk=True)
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