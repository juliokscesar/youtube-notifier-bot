import discord
import json
import requests
import os
from discord.ext import commands, tasks

intents = discord.Intents.default()
intents.message_content = True

description = "Bot do Raposow!"
furry = commands.Bot(command_prefix="!", description=description, intents=intents)

@furry.event
async def on_ready():
    print(f"Logged in as {furry.user} (ID: {furry.user.id})")

    with open("raposow_channel_data.json", "r") as f:
        data = json.load(f)

        if data["notifying_channel_id"] and data["suggestions_channel_id"]:
            await initializeTasks()

@furry.command()
async def oi(ctx):
    await ctx.send("Olá!")

@tasks.loop(seconds=30)
async def checkForShorts():
    with open("raposow_channel_data.json", "r") as f:
        saved_data = json.load(f)

        # Sending GET request to API
        channel_data = requests.get(f"https://yt.lemnoslife.com/channels?part=shorts&id={saved_data['channel_id']}")
        if channel_data.status_code != 200:
            print(f"Request to API returned code {channel_data.stauts_code}")
        else:
            #  Getting short's id in index 0 of the data sent by the API
            latest_short_id = channel_data.json()["items"][0]["shorts"][0]["videoId"]

            if latest_short_id == saved_data["latest_short_id"]:
                print("No shorts posted since last notification.")
            else:
                saved_data["latest_short_id"] = latest_short_id
                
                print(f"Successfully sent GET code to API. Found new Shorts. ID: {latest_short_id}; Title: \"{channel_data.json()['items'][0]['shorts'][0]['title']}\"")

                with open("raposow_channel_data.json", "w") as f:
                    json.dump(saved_data, f)

                discord_channel_id = saved_data["notifying_channel_id"]
                discord_channel = furry.get_channel(discord_channel_id)

                msg = f"**Raposow ACABOU de postar um shorts! Corre lá pra ver:**\n*{'https://www.youtube.com/shorts/' + latest_short_id}*\n\n||@everyone||"
                await discord_channel.send(msg)

@tasks.loop(hours=24)
async def suggestionReminder():
    with open("raposow_channel_data.json", "r") as f:
        data = json.load(f)

        suggestion_channel_id = data["suggestions_channel_id"]
        suggestion_channel = furry.get_channel(suggestion_channel_id)

        await suggestion_channel.send("**@here UTILIZE O COMANDO:**   ,sugerir")

async def initializeTasks():
    suggestionReminder.start()
    checkForShorts.start()

    print("Successfully initialized notification and suggestion tasks")

async def setChannelForTask(channel_json_key, task_f, ctx, response):
    if ctx.message.author.guild_permissions.administrator:
        with open("raposow_channel_data.json", "r") as f:
            data = json.load(f)
            data[channel_json_key] = ctx.channel.id
            
            with open("raposow_channel_data.json", "w") as f:
                json.dump(data, f)

        task_f.start()
        await ctx.send(response)

    else:
        await ctx.send("Você não tem permissão para usar esse comando!")

@furry.command()
async def notifiqueAqui(ctx):
    await setChannelForTask("notifying_channel_id", checkForShorts, ctx, f"Notificando agora no canal \"{ctx.channel.name}\"")

@furry.command()
async def sugestoesAqui(ctx):
    await setChannelForTask("suggestions_channel_id", suggestionReminder, ctx, f"Sugestões no canal {ctx.channel.name}")


@furry.command()
async def checkData(ctx):
    if ctx.message.author.guild_permissions.administrator:
        with open("raposow_channel_data.json", "r") as f:
            data = json.load(f)
            await ctx.send(data)

token = os.getenv("FURRY_BOT_TOKEN")
if not token:
    raise RuntimeError("Unable to get token from environment variables.")

if __name__ == "__main__":
    furry.run(token)
