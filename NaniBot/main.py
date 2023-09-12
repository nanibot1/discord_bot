import discord
from discord.ext import commands
import json
from keep_alive import keep_alive
import os
import requests

client = commands.Bot(command_prefix = '$', intents=discord.Intents.all())

def get_quote():
  response = requests.get("https://labs.bible.org/api/?passage=votd&type=json")
  json_data = json.loads(response.text)

  if len(json_data) == 1:
    quote = json_data[0]['bookname'] + ' ' + json_data[0]['chapter'] + ':' + json_data[0]['verse'] + ' - ' + json_data[0]['text']

  elif len(json_data) == 2:
    quote = json_data[0]['bookname'] + ' ' + json_data[0]['chapter'] + ':' + json_data[0]['verse'] + '-' + json_data[1]['verse'] + ' - ' + json_data[0]['text'] + ' ' + json_data[1]['text']
    
  else:
    quote = json_data[0]['bookname'] + ' ' + json_data[0]['chapter'] + ':' + json_data[0]['verse'] + '-' + json_data[len(json_data) - 1]['verse'] + ' - '
    verse = ""
    for i in range(len(json_data)):
      verse.append(json_data[i]['verse'])
      verse.append(' ')

    quote += verse

  return quote

@client.event
async def on_ready():
  print('We have logged in as {0.user}'.format(client))

@client.command()
async def hello(ctx):
  await ctx.send('Hello!')

@client.command()
async def votd(ctx):
  quote = get_quote()
  await ctx.send(quote)

keep_alive()
client.run('MTAzNjQ4MTc1Mjg1MzY0MzI5NA.GsM_cv.dFbNEejHrgESRmB7TuYB3Vdwb2o3SC7gYaYEKE')