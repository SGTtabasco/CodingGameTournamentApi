from fastapi import FastAPI
from prisma import Prisma, register
from prisma.models import User
import discord
import asyncio
import os
import assets.shared as shared

app = FastAPI()
client = discord.Client(intents=discord.Intents.all())
shared.client = client

import assets.routes as routes


@client.event
async def on_ready():
    print(f'DISCORD: We have logged in as {client.user}')


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith('!sync'):
        sp = message.content.split(' ')
        if len(sp) != 2:
            await message.channel.send('Invalid command. Usage: !sync <token>')
            return
        token = sp[1]
        await message.channel.send(f'Validating token {token}...')
        user = await User.prisma().find_unique(where={"discord_sync_token": token})
        if user is None:
            await message.channel.send('The token is invalid. Please generate a new token and try again.')
            return
        user = await User.prisma().update(where={"token": user.token}, data={"discord_id": str(message.author.id),
                                                                             "discord_sync_token": None})
        await message.channel.send('Discord account linked successfully!')
    elif message.content.startswith('!'):
        await message.channel.send('Invalid command. Usage: !sync <token>')


@app.on_event("startup")
async def startup():
    print('Database connection started...')
    db = Prisma()
    await db.connect()
    register(db)
    print('Database connection established...')
    print('Starting Discord bot...')
    # noinspection PyAsyncCall
    asyncio.create_task(client.start(os.getenv('DISCORD_BOT_TOKEN')))
    print('Discord bot started...')
    print('Connecting to Challonge...')



@app.on_event("shutdown")
async def shutdown():
    db = Prisma()
    await db.disconnect()
    print('Database connection closed')
    await client.close()
    print('Discord bot closed')


@app.get("/")
async def root():
    return {"status": "ok", "code": 200, "message": "Coding Game Tournament API up and running!"}


app.include_router(routes.router)
