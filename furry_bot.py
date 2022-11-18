import discord
import json
import requests
import re
import os
from discord.ext import commands, tasks

intents = discord.Intents.default()
intents.message_content = True

description = "Bot do Raposow!"
furry = commands.Bot(command_prefix="!", description=description, intents=intents)

@furry.event
async def on_ready():
    print(f"Logged in as {furry.user} (ID: {furry.user.id})")
    
    with open("raposow_channel_data.json", "r+") as f:
        data = json.load(f)

        if not data["notyfing_channel_id"]:
            for channel in furry.get_all_channels():
                if (channel.type == discord.ChannelType.text or channel.type == discord.ChannelType.news) and re.search("^.*v[ií]deo(s)?.*", channel.name.lower()):
                    data["notyfing_channel_id"] = channel.id
                    json.dump(data, f)
                    break

@furry.command()
async def oi(ctx):
    await ctx.send("Olá!")

@furry.command()
async def notifiqueAqui(ctx):
    return

@tasks.loop(seconds=30)
async def checkForShorts():
    with open("raposow_channel_data.json", "r+") as f:
        saved_data = json.load(f)

        channel_data = requests.get(f"https://yt.lemnoslife.com/channels?part=shorts&id={saved_data['channel_id']}")
        if channel_data.status_code != 200:
            print(f"Request to API returned code {channel_data.stauts_code}")
        else:
            latest_short_id = channel_data.json()["items"][0]["shorts"][0]["videoId"]
            if latest_short_id == saved_data["latest_short_id"]:
                print("No shorts posted since last notification.")
            else:
                saved_data["latest_short_id"] = latest_short_id
                json.dump(saved_data, f)

                discord_channel_id = saved_data["notyfing_channel_id"]
                discord_channel = furry.get_channel(discord_channel_id)

                msg = f"@everyone o Raposow ACABOU de postar um shorts novíssimo! Vai lá ver agora: {'https://www.youtube.com/shorts/' + latest_short_id}"
                discord_channel.send(msg)


token = os.getenv("FURRY_BOT_TOKEN")
if not token:
    print("Unable to get token from environment variables.")
    exit()

furry.run(token)
