import discord
from discord.ext import commands
from discord.ext.commands.context import Context

from random import randint
import json
import requests


intents = discord.Intents.all()
intents.presences = False


client = commands.Bot(
    command_prefix="$",
    help_command=None,
    intents=intents
)

# constants used inside commands
COINS = ["Heads", "Tails"]
NUMBERS_AS_EMOJIES = {1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣", 6: "6️⃣", 7: "7️⃣", 8: "8️⃣", 9: "9️⃣", 10: "🔟"}
NUMBER_EMOJIES = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
STOP_EMOJI = "🛑"

@client.event
async def on_ready():
    print("Logged In.")


@client.command(
    name="Ping",
    aliases=["p", "ping"],
    description="Send Pong for testing",
    help="ping"
)
async def ping(ctx: Context):
    await ctx.channel.send(f"Pong! an {ctx.author.mention}")



@client.command(
    name="Coinflip",
    aliases=["coinflip", "cf"],
    description="Tosses a coin and returns result",
    help="coinflip"
)
async def coinflip(ctx: Context):
    r = randint(0, 1)
    await ctx.channel.send(COINS[r])


def get_incredients(cocktail):
    i = 1
    ingredients = []
    while cocktail["strIngredient" + str(i)] != None:
        measure = cocktail["strMeasure" + str(i)] if cocktail["strMeasure" + str(i)] != None else ""
        ingredients.append((measure, cocktail["strIngredient" + str(i)]))
        i += 1
    return ingredients

@client.command(
    name="Get Cocktail",
    aliases=["get_cocktail"]
)
async def get_cocktail(ctx: Context, drink_search):
    try:
        url = "https://www.thecocktaildb.com/api/json/v1/1/search.php?s=" + drink_search
        response = requests.get(url)
        drinks = response.json()["drinks"]
        cocktail = drinks[0]
        ingredients = get_incredients(cocktail)

        embed = discord.Embed(
            title=cocktail["strDrink"],
            description=cocktail["strInstructionsDE"],
            color=0xFF0000
        )
        embed.add_field(
            name="Menge",
            value="\n".join(ing[0] for ing in ingredients)
        )
        embed.add_field(
            name="Zutaten",
            value="\n".join(ing[1] for ing in ingredients),
            inline=True
        )
        embed.set_thumbnail(url=cocktail["strDrinkThumb"])
        await ctx.channel.send(embed=embed)
    except:
        await ctx.channel.send(f"Sorry, but I cannot find a result for your request, {ctx.author.mention}", mention_author=True)


@client.command(
    name="Survey",
    aliases=["survey", "s"]
)
async def create_survey(ctx: Context, question, *args):
    if len(args) > 10 or len(args) == 0:
        await ctx.channel.send("Keep number of options between 1 and 10")
        return

    # set up survey embed
    embed = discord.Embed(
        title="Umfrage",
        description=question,
        color=0xFF0000
    )
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)

    # add options
    for num, opt in enumerate(args):
        embed.add_field(name=NUMBERS_AS_EMOJIES[num + 1], value=opt, inline=False)

    survey = await ctx.channel.send(embed=embed)

    # add option and stop emoji to message
    for opt_num in enumerate(args):
        await survey.add_reaction(NUMBERS_AS_EMOJIES[opt_num[0] + 1])

    await survey.add_reaction(STOP_EMOJI)

def reaction_count_order(reactions):
    # assert that reactions is sorted downwards so counts is also sorted downwards
    counts = [react.count for react in reactions]
    partitions = []
    i = 0
    for c in counts:
        partition = []
        while reactions[i].count == c:
            reactions[i].count -= 1 # HERE REMOVE BOT REACTION
            partition.append(reactions[i])
            if i != len(reactions)-1:
                i += 1
            else:
                break
            partitions.append(partition)
        return partitions

@client.event
async def on_raw_reaction_add(payload):
    channel = client.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    emoji = payload.emoji.name

    if emoji == "🛑" and len(message.embeds) == 1 and payload.member.name == message.embeds[0].author.name:
        reactions = [react for react in message.reactions if react.emoji in NUMBER_EMOJIES]
        reactions.sort(reverse=True, key=lambda react: react.count)
        reaction_partitions = reaction_count_order(reactions)
        winner_count = str(reaction_partitions[0][0].count)
        if len(reaction_partitions[0]) == 1:
            await channel.send("Gewonnen hat: " + reaction_partitions[0][0].emoji + " mit " + winner_count + " Stimmen.")
        else:
            winners = ", ".join([react.emoji for react in reaction_partitions[0]])
            await channel.send("Gewonnen haben: " + winners + " mit " + winner_count + " Stimmen.")

# run bot fetching token from separate json file
with open("servantBot_token.json", "r") as servantBot_token:
    token = json.load(servantBot_token)["token"]
    client.run(token)