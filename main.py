import discord
from discord.ext import commands
#from config import settings
import emoji
from src.finance_reporter import FininceReporter
from loguru import logger
from pyvirtualdisplay import Display
import yaml
import argparse

if __name__ == '__main__':
	
	parser = argparse.ArgumentParser(description='Run bot application')
	parser.add_argument('--cfg', dest='cgf_file',type = str,
                    default='config.yaml',
                    help='config file to run application')
	args = parser.parse_args()
	with open(args.cgf_file, "r") as stream:
		try:
			settings = yaml.safe_load(stream)
		except yaml.YAMLError as exc:
			print(exc)
	client = commands.Bot(command_prefix=settings['prefix'])
	finreporter = FininceReporter(client=client)
	client.add_cog(finreporter)
	display = Display(visible=0,size=(800, 600))
	display.start()


	@client.event
	async def on_ready():
		try:
			# print bot information
			logger.info(client.user.name)
			logger.info(client.user.id)
			logger.info(f'Discord.py Version: {discord.__version__}')
			
		except Exception as e:
			logger.info(e)

	@client.command(pass_contest = True)
	async def clear(ctx,amount=1):
		await ctx.channel.purge(limit=amount)

	@client.event
	async def on_message(message):
		if message.author != client.user:
			if message.content.lower().startswith("привет") or message.content.lower().startswith("здаро") or message.content.lower().startswith("ghbd"):
				await message.channel.send(f'Привет, {message.author} '+emoji.emojize('\U0001F603'),reference=message)		
		await client.process_commands(message=message)
	
	client.run(settings['token'])
