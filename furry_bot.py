import discord
import json
import requests
import os
from discord.ext import commands, tasks

intents = discord.Intents.default()
intents.message_content = True

description = "Bot do Raposow!"
bot = commands.Bot(command_prefix="!", description=description, intents=intents)

API_KEY = os.getenv("YOUTUBE_API_KEY")
if not API_KEY:
    raise RuntimeError("Unable to get API_KEY from environment variables.")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

    with open("raposow_channel_data.json", "r") as f:
        data = json.load(f)

        if data["notifying_channel_id"] and (data["tasks_status"]["notification"] == 1):
            await checkForShorts.start()
        
        if data["suggestions_channel_id"] and (data["tasks_status"]["suggestions"] == 1):
            await suggestionReminder.start()


@bot.command()
async def oi(ctx):
    await ctx.send("Olá!")

@tasks.loop(seconds=40)
async def checkForShorts():
    with open("raposow_channel_data.json", "r") as f:
        saved_data = json.load(f)

        # Sending GET request to API
        channel_data = requests.get(f"https://www.googleapis.com/youtube/v3/search?key={API_KEY}&channelId={saved_data['channel_id']}&part=snippet,id&order=date&maxResults=5")
        if channel_data.status_code != 200:
            print(f"GET request returned code {channel_data.status_code}. Result: {channel_data.json()}")
        
        else:
            json_data = channel_data.json()
            if json_data["items"][0]["id"]["kind"] == "youtube#video":
                videoId = json_data["items"][0]["id"]["videoId"]

                is_shorts = requests.get(f"https://www.youtube.com/shorts/{videoId}", allow_redirects=False).status_code == 200
                if is_shorts:
                    if saved_data["latest_short_id"] != videoId:
                        print(f"Successfully sent GET request to API and found new shorts. ID: {videoId}")

                        saved_data["latest_short_id"] = videoId
                        with open("raposow_channel_data.json", "w") as f2:
                            json.dump(saved_data, f2)
                        
                        discord_channel_id = saved_data["notifying_channel_id"]
                        discord_channel = bot.get_channel(discord_channel_id)

                        msg = f"**Raposow ACABOU de postar um shorts! Corre lá pra ver:**\n*{'https://www.youtube.com/shorts/' + videoId}*\n\n||@everyone||"
                        await discord_channel.send(msg)


@tasks.loop(hours=24)
async def suggestionReminder():
    with open("raposow_channel_data.json", "r") as f:
        data = json.load(f)

        suggestion_channel_id = data["suggestions_channel_id"]
        suggestion_channel = bot.get_channel(suggestion_channel_id)

        await suggestion_channel.send("**@here UTILIZE O COMANDO:**   ,sugerir")

async def setChannelForTask(channel_json_key, task_f, task_name_data, ctx, response):
    if ctx.message.author.guild_permissions.administrator:
        with open("raposow_channel_data.json", "r") as f:
            data = json.load(f)
            data[channel_json_key] = ctx.channel.id
            data["tasks_status"][task_name_data] = 1
            
            with open("raposow_channel_data.json", "w") as f2:
                json.dump(data, f2)

        task_f.start()
        await ctx.send(response)

    else:
        await ctx.send("Você não tem permissão para usar esse comando!")

async def stopTask(task_f, task_name_data, ctx, responseSuccess, responseErr):
    with open("raposow_channel_data.json", "r") as f:
        data = json.load(f)

        if ctx.message.author.guild_permissions.administrator:
            if task_f.is_running() and (data["tasks_status"][task_name_data] == 1):
                task_f.stop()
                print(responseSuccess)
                data[task_name_data] = 0

                with open("raposow_channel_data.json", "w") as f2:
                    json.dump(data, f2)

                await ctx.send(responseSuccess)

            else:
                await ctx.send(responseErr)

@bot.command()
async def notifiqueAqui(ctx):
    await setChannelForTask("notifying_channel_id", checkForShorts, "notification", ctx, f"Notificando agora no canal \"{ctx.channel.name}\"")

@bot.command()
async def sugestoesAqui(ctx):
    await setChannelForTask("suggestions_channel_id", suggestionReminder, "suggestions", ctx, f"Sugestões no canal {ctx.channel.name}")

@bot.command()
async def stopNotify(ctx):
    await stopTask(checkForShorts, "notification", ctx, "Task notificacoes foi desligada", "Task notificaces nao esta ligada")

@bot.command()
async def stopSuggestion(ctx):
    await stopTask(suggestionReminder, "suggestions", ctx, "Task sugestoes foi desligada", "Task sugestoes não está ligada")

@bot.command()
async def checkData(ctx):
    if ctx.message.author.guild_permissions.administrator:
        with open("raposow_channel_data.json", "r") as f:
            data = json.load(f)
            await ctx.send(data)

token = os.getenv("FURRY_BOT_TOKEN")
if not token:
    raise RuntimeError("Unable to get token from environment variables.")

if __name__ == "__main__":
    bot.run(token)
