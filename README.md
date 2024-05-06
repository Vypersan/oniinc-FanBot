# Short description
 A fan made discord bot oriented around [ONIINC](https://twitter.com/oniincteam)

## Requirements:
- `discord.py[voice]`
- `spotipy 2.23.0` 
- `aiofiles`
- `colorama`

## Set up
1. Clone this repository
2. **Recommended**: create virtual environment and activate it
    - In the root directory, run `python -m venv venv`
    - While in root directory, you can run `call venv/Scripts/activate`
3. Pip install the required pip packages, using `pip install -r requirements.txt`
4. Put `config.json` file in `jsonfiles` folder.
    - Contact repository owner for this file
5. Ensure the database file (`database.db`) exists in root directory
    - Contact repository owner for this file

## How to run
The bot has two versions included in all of these files, namely the live version and the beta version. Both are ran through command prompt and certain arguments are used to switch in between them.

The bot also offers a custom logging module. The logging module prints errors and warning messages differently and also hides the initial startup text used by the library discord.py.

Run bot: `python Main.py`

## Arguments

### --live (run the live version of the bot)
Add `--live` to run the live version. Omitting this argument will run the bot in beta mode.

### --disablelog (disable custom logger)
You can disable the custom logger by adding `--disablelog` when running the bot.


