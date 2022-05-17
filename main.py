import discord
from discord.ext import commands
from config import settings
import emoji
from src.finance_reporter import FininceReporter
client = commands.Bot(command_prefix=settings['prefix'])
finreporter = FininceReporter(client=client)
client.add_cog(finreporter)


@client.event
async def on_ready():
	try:
		# print bot information
		print(client.user.name)
		print(client.user.id)
		print('Discord.py Version: {}'.format(discord.__version__))
		
	except Exception as e:
		print(e)

@client.command(pass_contest = True)
async def очистка(ctx,amount=10):
	await ctx.channel.purge(limit=amount)


@client.event
async def on_message(message):
	if message.author != client.user:
		if message.content.lower().startswith("привет") or message.content.lower().startswith("здаро") or message.content.lower().startswith("ghbd"):
			await message.channel.send(f'Привет, {message.author} '+emoji.emojize('\U0001F603'),reference=message)

			
	await client.process_commands(message=message)
	


client.run(settings['token'])
