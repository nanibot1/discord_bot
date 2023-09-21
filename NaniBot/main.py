import asyncio
import csv
from datetime import date, datetime, timedelta
import nextcord
from nextcord.ext import commands, tasks
import json
from keep_alive import keep_alive
import os
import pytz
import requests


class ExistingBirthday(Exception):
  "Birthday already exists!"
  pass


client = commands.Bot(command_prefix='$', intents=nextcord.Intents.all())
client.remove_command('help')


# On Ready
@client.event
async def on_ready():
  print('We have logged in as {0.user}'.format(client))
  await daily_loop()  # Birthday Check + VOTD


# New Member Join Event
@client.event
async def on_member_join(member):
  welcome_channel = client.get_channel(1018981433315962884)
  member_count_channel = client.get_channel(1152275945089155234)

  to_send = f'Welcome {member.mention} to {member.guild.name}' + "'s Discord Server!"
  await welcome_channel.send(to_send)
  await member_count_channel.edit(
    name=f'🗣✝ ┊ Members: {member.guild.member_count}')


# Member Leave Event
@client.event
async def on_member_remove(member):
  member_count_channel = client.get_channel(1152275945089155234)
  await member_count_channel.edit(
    name=f'🗣✝ ┊ Members: {member.guild.member_count}')


# Reaction Role Add
@client.event
async def on_raw_reaction_add(payload):
  message_id = payload.message_id
  if message_id == 1152571459240214621:
    guild_id = payload.guild_id
    guild = nextcord.utils.find(lambda g: g.id == guild_id, client.guilds)
    print(payload.emoji.name)

    if payload.emoji.name == '♂️':
      role = nextcord.utils.get(guild.roles, id=1018238476182880387)
    elif payload.emoji.name == '♀️':
      role = nextcord.utils.get(guild.roles, id=1018238346570498178)
    elif payload.emoji.name == '🇳':
      role = nextcord.utils.get(guild.roles, id=1152559150501478541)
    elif payload.emoji.name == '🅿️':
      role = nextcord.utils.get(guild.roles, id=1152559282198433833)
    elif payload.emoji.name == '🇨':
      role = nextcord.utils.get(guild.roles, id=1152559346681651321)
    elif payload.emoji.name == '🇲':
      role = nextcord.utils.get(guild.roles, id=1152559406718914610)
    elif payload.emoji.name == '🇸':
      role = nextcord.utils.get(guild.roles, id=1152559449999945830)
    else:
      role = nextcord.utils.get(guild.roles, name=payload.emoji.name)

    if role is not None:
      member = nextcord.utils.find(lambda m: m.id == payload.user_id,
                                   guild.members)
      if member is not None:
        await member.add_roles(role)


emojis = ['♂️', '♀️', '🇳', '🅿️', '🇨', '🇲', '🇸']


# Reaction Role Remove
@client.event
async def on_raw_reaction_remove(payload):
  message_id = payload.message_id
  if message_id == 1152571459240214621:
    guild_id = payload.guild_id
    guild = nextcord.utils.find(lambda g: g.id == guild_id, client.guilds)

    if payload.emoji.name == '♂️':
      role = nextcord.utils.get(guild.roles, id=1018238476182880387)
    elif payload.emoji.name == '♀️':
      role = nextcord.utils.get(guild.roles, id=1018238346570498178)
    elif payload.emoji.name == '🇳':
      role = nextcord.utils.get(guild.roles, id=1152559150501478541)
    elif payload.emoji.name == '🅿️':
      role = nextcord.utils.get(guild.roles, id=1152559282198433833)
    elif payload.emoji.name == '🇨':
      role = nextcord.utils.get(guild.roles, id=1152559346681651321)
    elif payload.emoji.name == '🇲':
      role = nextcord.utils.get(guild.roles, id=1152559406718914610)
    elif payload.emoji.name == '🇸':
      role = nextcord.utils.get(guild.roles, id=1152559449999945830)
    else:
      role = nextcord.utils.get(guild.roles, name=payload.emoji.name)

    if role is not None:
      member = nextcord.utils.find(lambda m: m.id == payload.user_id,
                                   guild.members)
      if member is not None:
        await member.remove_roles(role)


# Commands


# Help Command
@client.command(description="Gives the list of commands for NaniBot")
async def help(ctx):
  embed = nextcord.Embed(
    title="Commands",
    description="List of commands for using the bot, NaniBot!")
  for command in client.walk_commands():
    description = command.description
    if not description or description is None or description == "":
      description = 'No description provided'
    embed.add_field(
      name=
      f"${command.name}{command.signature if command.signature is not None else ''}",
      value=description)
  await ctx.send(embed=embed)


@client.command(description="Gives the website for our church!")
async def website(ctx):
  await ctx.send("https://sd.church/")


# Rules Command
@client.command(description="Gives the rules of the Discord server")
async def rules(ctx):
  await ctx.message.author.send(
    ":scroll: **Rules** :scroll:\n0. Golden Rule: Just because something isn't against the rules doesn't mean its acceptable, nor does it mean that you will not be dealt with accordingly. As a rule of thumb: if you wouldn't do it in front of your Grandma, don't do it here. Do not be the reason that we have to add/edit rules.\n1A. Respect everyone: Any harassment or discrimination towards anyone based on race, gender orientation, ethnicity, sexual orientation, gender orientation, etc. will not be permitted. Zero tolerance towards things related to hate groups, terrorism, and slurs.\n1B. Respect everyone: Respect all members as a person. There is absolutely no tolerance for harassment even if it is not listed clearly in Rule 1A.\n2. No spams in general: Do not spam. Let's not clutter the chats :).\n3. Stay appropriate: This should be obvious, especially in a Christian server like this one, but no explicit NSFW content, such as pornographic imagery and graphic details of NSFW acts, is allowed, _please_. Seeing NSFW content should always be a choice, and placing it in other channels will be met with immediate action.\n4. Don't Share Personal Information: Any distribution of personal information without consent is prohibited.\n5. No Mass Ping Spamming: If you want to ping everyone, just do it _once_.\n6. No Spoilers (TV shows, Movies, etc.) Without Spoiler Tag: DO NOT RUIN THINGS FOR OTHERS _PLEASE_\n7. Roles and Names: Don't forget to choose your roles (gender, region, etc.) and change your Discord names to your_actual_ names!\n8. Heinous Content:  Any content that crash discord or disrupt users systems, graphic images/videos or unmarked links to graphic images/videos, the promotion of potentially predatory people/events/programs will result in a ban. No exceptions."
  )


# votd helper
def get_quote():
  response = requests.get("https://labs.bible.org/api/?passage=votd&type=json")
  json_data = json.loads(response.text)

  if len(json_data) == 1:
    quote = json_data[0]['bookname'] + ' ' + json_data[0][
      'chapter'] + ':' + json_data[0]['verse'] + ' - ' + json_data[0]['text']

  elif len(json_data) == 2:
    quote = json_data[0]['bookname'] + ' ' + json_data[0][
      'chapter'] + ':' + json_data[0]['verse'] + '-' + json_data[1][
        'verse'] + ' - ' + json_data[0]['text'] + ' ' + json_data[1]['text']

  else:
    quote = json_data[0]['bookname'] + ' ' + json_data[0][
      'chapter'] + ':' + json_data[0]['verse'] + '-' + json_data[
        len(json_data) - 1]['verse'] + ' - '
    verse = ""
    for i in range(len(json_data)):
      verse += json_data[i]['text']
      verse += ' '

    quote += verse

  return quote


# Verse of the Day Command
@client.command(description="Gives the Verse of the Day (from Bible.org)")
async def votd(ctx):
  quote = get_quote()
  await ctx.send(quote)


@client.command(
  description=
  "Gives you the option to input your birthday into the automated birthday system!"
)
async def birthday(ctx):
  try:
    await ctx.author.send(
      '**User Setup - Birthday**\n\nPlease provide your birth month and day\n\n**Example Usage: 08/28 (MM/DD)**\n_You have 30 seconds to reply_'
    )
    msg = await client.wait_for('message', check=lambda x: x.author == ctx.author and x.channel == ctx.author.dm_channel, timeout=10)
    birthdate = datetime.strptime(msg.content, "%m/%d")
    await ctx.author.send('Your birthday has been set to: ' + "**" +
                          birthdate.strftime("%B %d") + "**")
    if birthdate.month >= 1 or birthdate.month <= 9:
      birthdate = "0" + str(birthdate.month) + "/" + str(birthdate.day)
    else:
      birthdate = str(birthdate.month) + "/" + str(birthdate.day)
    with open('birthdays.csv', 'a') as birthdays:
      csv.writer(birthdays).writerow([ctx.author.id, birthdate])

  except ValueError:
    await ctx.author.send('Invalid format. Please try again.')
  except TimeoutError:
    await ctx.author.send('Time has run out')
  except ExistingBirthday:
    await ctx.author.send('Birthday already exists!')


async def daily_loop():
  while True:
    now = datetime.now(pytz.timezone('US/Pacific'))
    then = now.replace(hour=0, minute=0, second=0,
                       microsecond=0) + timedelta(days=1)
    wait_time = (then - now).total_seconds()
    await asyncio.sleep(wait_time)

    # VOTD
    votd_channel = client.get_channel(1152057576679292978)
    await votd_channel.send(get_quote())

    # Birthday Check
    today_month = now.month
    today_day = now.day
    if today_month >= 1 or today_month <= 9:
      birthdate = "0" + str(today_month) + "/" + str(today_day)
    else:
      birthdate = str(today_month) + "/" + str(today_day)
    with open('birthdays.csv') as birthdays:
      csv_reader = csv.reader(birthdays)
      for index, birthday in enumerate(csv_reader):
        if birthdate == birthday[1]:
          await client.get_channel(1036517362989535292).send(
            f"Happy Birthday <@{birthday[0]}>!")


# Program on

keep_alive()
client.run(os.getenv('TOKEN'))
