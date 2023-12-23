import asyncio
import csv
from datetime import datetime, timedelta
import json
from keep_alive import keep_alive
import nextcord
from nextcord.ext import commands
import os
import pytz
import requests
import nextwave as wavelink


client = commands.Bot(command_prefix='$', intents=nextcord.Intents.all())
client.remove_command('help')


# On Ready
@client.event
async def on_ready():
  print('We have logged in as {0.user}'.format(client))
  client.loop.create_task(node_connect())
  await daily_loop()  # Birthday Check + VOTD

# Sets Up Music Bot
@client.event
async def on_wavelink_node_ready(node: wavelink.Node):
  print(f"Node {node.identifier} is ready!")

# Create Music Bot Node
async def node_connect():
  await client.wait_until_ready()
  await wavelink.NodePool.create_node(bot=client, host='lavalink.lexnet.cc', port=443, password='lexn3tl@val!nk', https=True)

# Music Bot Queue Function
@client.event
async def on_wavelink_track_end(player: wavelink.Player, track: wavelink.YouTubeTrack, reason):
  try:
    ctx = player.ctx
    vc: player = ctx.voice_client

  except nextcord.HTTPException:
    interaction = player.interaction
    vc: player = interaction.guild.voice_client

  if vc.loop:
    return await vc.play(track)

  if vc.queue.is_empty:
    return await vc.disconnect()

  next_song = vc.queue.get()
  await vc.play(next_song)
  try:
    await ctx.send(f"Now playing: {next_song.title}")
  except nextcord.HTTPException:
    await interaction.send(f"Now playing: {next_song.title}")

# Music Bot Play Command
@client.command(description = "Plays a song from YouTube.  Type $play <song> to use.")
async def play(ctx: commands.Context, *, search: wavelink.YouTubeTrack):
  if not ctx.voice_client:
    vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.send("Join a voice channel first!")
  else:
    vc: wavelink.Player = ctx.voice_client

  if vc.queue.is_empty and not vc.is_playing():
    await vc.play(search)
    await ctx.send(f"Now playing: {search.title}")

  else:
    await vc.queue.put_wait(search)
    await ctx.send(f"Added {search.title} to the queue.")

  vc.ctx = ctx
  try:
    if vc.loop: return
  except Exception:
    setattr(vc, "loop", False)

# Music Bot Pause Command
@client.command(description = "Pauses the current song.")
async def pause(ctx: commands.Context):
  if not ctx.voice_client:
    return await ctx.send("I'm not playing anything!")
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.send("Join a voice channel first!")
  else:
    vc: wavelink.Player = ctx.voice_client

  if not vc.is_playing():
    return await ctx.send("I'm not playing anything!")

  await vc.pause()
  await ctx.send("Music paused!")

# Music Bot Resume Command
@client.command(description = "Resumes the current song.")
async def resume(ctx: commands.Context):
  if not ctx.voice_client:
    return await ctx.send("I'm not playing anything!")
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.send("Join a voice channel first!")
  else:
    vc: wavelink.Player = ctx.voice_client

  if vc.is_playing():
    return await ctx.send("I'm already playing!")

  await vc.resume()
  await ctx.send("Music resumed!")

# Music Bot Skip Command
@client.command(description = "Skips the current song.")
async def skip(ctx: commands.Context):
  if not ctx.voice_client:
    return await ctx.send("I'm not playing anything!")
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.send("Join a voice channel first!")
  else:
    vc: wavelink.Player = ctx.voice_client

  if not vc.is_playing():
    return await ctx.send("I'm not playing anything!")

  await vc.stop()
  await ctx.send("Music skipped!")

  try:
    next_song = vc.queue.get()
    await vc.play(next_song)
    await ctx.send(content=f"Now Playing `{next_song}`")
  except Exception:
    return await ctx.send("The queue is empty!")

# Music Bot Disconnect Command
@client.command(description = "Disconnects the bot from the voice channel.")
async def disconnect(ctx: commands.Context):
  if not ctx.voice_client:
    return await ctx.send("I'm not playing anything!")
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.send("Join a voice channel first!")
  else:
    vc: wavelink.Player = ctx.voice_client

  await vc.disconnect()
  await ctx.send("Music stopped!")

# Music Bot Loop Command
@client.command(description = "BUGGED Loops the current song.")
async def loop(ctx: commands.Context):
  if not ctx.voice_client:
    return await ctx.send("I'm not playing anything!")
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.send("Join a voice channel first!")
  else:
    vc: wavelink.Player = ctx.voice_client

  if not vc.is_playing():
    return await ctx.send("I'm not playing anything!")

  try: 
    vc.loop ^= True
  except:
    setattr(vc, "loop", False)

  if vc.loop:
    return await ctx.send("Loop is now enabled!")
  else:
    return await ctx.send("Loop is now disabled!")

# Music Bot Queue Command
@client.command(description = "Shows the current queue.")
async def queue(ctx: commands.Context):
  if not ctx.voice_client:
    return await ctx.send("I'm not playing anything!")
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.send("Join a voice channel first!")
  else:
    vc: wavelink.Player = ctx.voice_client

  if vc.queue.is_empty:
    return await ctx.send("There are no songs in the queue")

  em = nextcord.Embed(title="Song Queue", description="", color=nextcord.Color.blurple())

  queue = vc.queue.copy()
  song_count = 0
  for song in queue:
    song_count += 1
    em.add_field(name=f"Song Number {song_count}", value=f"{song.title}", inline=False)

  await ctx.send(embed=em)

# Music Bot Volume Command
@client.command(description = "Changes the volume of the current song.")
async def volume(ctx: commands.Context, volume: int):
  if not ctx.voice_client:
    return await ctx.send("I'm not playing anything!")
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.send("Join a voice channel first!")
  else:
    vc: wavelink.Player = ctx.voice_client

  if volume > 100:
    return await ctx.send("The volume can not be over 100%.")
  elif volume < 0:
    return await ctx.send("The volume can not be under 0%.")
  else:
    await ctx.send(f"Setting the volume to {volume}%")
  return await vc.set_volume(volume)

# Music Bot Now Playing Command
@client.command(description = "Shows the current song playing.")
async def nowplaying(ctx: commands.Context):
  if not ctx.voice_client:
    return await ctx.send("I'm not playing anything!")
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.send("Join a voice channel first!")
  else:
    vc: wavelink.Player = ctx.voice_client

  if not vc.is_playing():
    return await ctx.send("I'm not playing anything!")

  em = nextcord.Embed(title=f"Now Playing {vc.track.title}", description=f"Artist: {vc.track.author}")
  em.add_field(name="Duration", value=f"{str(timedelta(seconds=vc.track.length))}")
  em.add_field(name="Extra Info", value=f"Song URL: [Click Here]({str(vc.track.uri)})")
  return await ctx.send(embed=em)


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


@client.command(description = "Gives you the option to input your birthday into the automated birthday system!")
async def birthday(ctx):
  try:
    await ctx.author.send(
      '**User Setup - Birthday**\n\nPlease provide your birth month and day\n\n**Example Usage: 08/28 (MM/DD)**\n_You have 30 seconds to reply_'
    )
    msg = await client.wait_for('message', check=lambda x: x.author == ctx.author and x.channel == ctx.author.dm_channel, timeout=10)
    birthdate = datetime.strptime(msg.content, "%m/%d")
    await ctx.author.send('Your birthday has been set to: ' + "**" + birthdate.strftime("%B %d") + "**")
    if (birthdate.month >= 1 or birthdate.month <= 9) and birthdate.day >= 10:
      birthdate = "0" + str(birthdate.month) + "/" + str(birthdate.day)
    elif (birthdate.day >= 1 or birthdate.month <= 9) and birthdate.month >= 10:
      birthdate = str(birthdate.month) + "/" + "0" + str(birthdate.day)
    elif (birthdate.month >= 1 or birthdate.month <= 9) and (birthdate.day >= 1 or birthdate.month <= 9):
      birthdate = "0" + str(birthdate.month) + "/" + "0" + str(birthdate.day)
    else:
      birthdate = str(birthdate.month) + "/" + str(birthdate.day)

    with open('birthdays.csv', 'r') as birthdays:
      csv_reader = csv.reader(birthdays)
      birthday_list = list(csv_reader)
      already_exist = False
      for i in range(len(birthday_list)):
        if birthday_list[i][0] == str(ctx.author.id):
          birthday_list[i][1] = birthdate
          already_exist = True

      if already_exist == True:
        writer = csv.writer(open('birthdays.csv', 'w'))
        writer.writerows(birthday_list) 

      else:
        with open('birthdays.csv', 'w') as birthdays:
          csv.writer(birthdays).writerows(birthday_list) 
          csv.writer(birthdays).writerow([ctx.author.id, birthdate])

  except ValueError:
    await ctx.author.send('Invalid format. Please try again.')
  except TimeoutError:
    await ctx.author.send('Time has run out')


async def daily_loop():
  while True:
    today = datetime.now(pytz.timezone('US/Pacific'))
    then = today.replace(hour=0, minute=0, second=0,
                       microsecond=0) + timedelta(days=1)
    wait_time = (then - today).total_seconds()
    await asyncio.sleep(wait_time)

    # VOTD
    votd_channel = client.get_channel(1152057576679292978)
    await votd_channel.send(get_quote())

    # Birthday Check
    if (today.month >= 1 or today.month <= 9) and today.day >= 10:
      today = "0" + str(today.month) + "/" + str(today.day)
    elif (today.day >= 1 or today.month <= 9) and today.month >= 10:
      today = str(today.month) + "/" + "0" + str(today.day)
    elif (today.month >= 1 or today.month <= 9) and (today.day >= 1 or today.month <= 9):
      today = "0" + str(today.month) + "/" + "0" + str(today.day)
    else:
      today = str(today.month) + "/" + str(today.day)
    with open('birthdays.csv') as birthdays:
      csv_reader = csv.reader(birthdays)
      for index, birthday in enumerate(csv_reader):
        if today == str(birthday[1]):
          await client.get_channel(1036517362989535292).send(f"Happy Birthday <@{birthday[0]}>!")

@client.command()
async def test(ctx):
  await client.get_channel(1036517362989535292).send(f"Happy Birthday <@{322338993972969472}>!")


# Program on

keep_alive()
client.run(os.getenv('TOKEN'))
