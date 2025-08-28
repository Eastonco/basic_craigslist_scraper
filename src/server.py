import os
import subprocess
import dataclasses
import json

from fastapi import FastAPI, Form, Response, Request, HTTPException
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator

from pretty_print import printError, printInfo, printSuccess
from models import Config

app = FastAPI()

with open("./config/serverConfig.json") as json_file:
    server_config = json.load(json_file)


def get_config(config_path: str):
    try:
        with open(config_path) as json_file:
            config = Config(**json.load(json_file))
    except Exception as exc:
        printError(
            f'check config file - something is broken.{Exception=} {exc=}. Exiting...')
        raise exc
    return config


def write_config(config_path: str, config: Config):
    os.rename(config_path, f"{config_path}.backup")
    try:
        with open(config_path, 'w') as json_file:
            json.dump(dataclasses.asdict(config), json_file, indent=4)
    except Exception as exc:
        printError(
            f'check config file - something is broken.{Exception=} {exc=}. Exiting...')
        raise exc
    os.remove(f"{config_path}.backup")


def start_scraper(config_path: str):
    printInfo("Starting bot...")
    subprocess.Popen(
        ["python", "-m", "app", "--config", config_path])
    printSuccess("Bot started!")
    return "success"


def stop_scraper(config_path: str):
    printInfo("Stopping bot...")
    ps = subprocess.run(["ps", "-aux"], capture_output=True, text=True)
    if ps.returncode != 0:
        printError("Error getting process list")
        return
    lines = ps.stdout.splitlines()
    printInfo(lines)

    for line in lines:
        if config_path in line:
            pid = line.split()[1]
            subprocess.Popen(["kill", pid])
            printSuccess("Bot stopped!")
            return "success"

    return "failed"


def restart_scraper(config_path: str):
    stop = stop_scraper(config_path)
    return start_scraper(config_path) if stop == "success" else "did not restart because was not running"


def add_filter(config_path: str, filter: str):
    try:
        config = get_config(config_path)
    except Exception as exc:
        return f"failed to add filter, {exc=}"

    config.filters.append(filter)

    try:
        write_config(config_path, config)
    except Exception as exc:
        return f"failed to add filter, error writing back to config file. {exc=}"

    return restart_scraper(config_path)


def remove_filter(config_path: str, filter: str):
    try:
        config = get_config(config_path)
    except Exception as exc:
        return f"failed to open config file, cannot rm filter, {exc=}"

    config.filters.remove(filter)

    try:
        write_config(config_path, config)
    except Exception as exc:
        return f"failed to write to config, {exc=}"

    return restart_scraper(config_path)


def help():
    return """
    All commands are case insensitive. 

    bstart - start the bot
    bstop - stop the bot
    re - restart the bot

    h - print this help message

    f <filter> - add a filter to the bot
    rf <filter> - remove a filter from the bot
    lf - list all filters
    l <link> - add a link to the bot
    ll - list all links
    rl <index> - remove a link from the bot, use "ll" to see indexes

    ct - toggle combining texts into one message
    """


def add_link(config_path: str, link: str):
    try:
        config = get_config(config_path)
    except Exception as exc:
        return f"error opening config file. {exc=}"

    config.urls.append(link)

    try:
        write_config(config_path, config)
    except Exception as exc:
        return f"error writing back to config file. {exc=}"

    return restart_scraper(config_path)


def remove_link(config_path: str, link_index: int):
    try:
        config = get_config(config_path)
    except Exception as exc:
        return f"error opening config file. {exc=}"

    del config.urls[link_index]

    try:
        write_config(config_path, config)
    except Exception as exc:
        return f"error writing back to config file. {exc=}"

    return restart_scraper(config_path)


def list_links(config_path: str):
    try:
        config = get_config(config_path)
    except Exception as exc:
        return f"error opening config file. {exc=}"

    strings = [f"{i}: {link}" for i, link in enumerate(config.urls)]
    return "\n".join(strings)


def list_filters(config_path: str):
    try:
        config = get_config(config_path)
    except Exception as exc:
        return f"error opening config file. {exc=}"

    strings = [f"{i}: {filter}" for i, filter in enumerate(config.filters)]
    return "\n".join(strings)


def flip_combine_texts(config_path: str):
    try:
        config = get_config(config_path)
    except Exception as exc:
        return f"error opening config file. {exc=}"

    config.combine_texts = not config.combine_texts

    try:
        write_config(config_path, config)
    except Exception as exc:
        return f"error writing back to config file. {exc=}"

    return restart_scraper(config_path)


@app.post("/")
async def text(
    request: Request, From: str = Form(...), Body: str = Form(...)
):
    validator = RequestValidator(server_config["twilio_auth_token"])
    form = await request.form()
    if not validator.validate(
        str(request.url),
        form,
        request.headers.get("X-Twilio-Signature", "")
    ):
        raise HTTPException(
            status_code=400, detail="Error in Twilio Signature")

    response = MessagingResponse()

    printInfo(f"Received text from {From}: {Body}")

    config_path = server_config["phone_to_config"].get(From, "./config/config.json")
    cmd = [c.lower() for c in Body.split()]

    cmd_name = cmd[0] if cmd else "h"
    if cmd_name == "bstart":
        resp = start_scraper(config_path)
        response.message(resp)
    elif cmd_name == "bstop":
        resp = stop_scraper(config_path)
        response.message(resp)
    elif cmd_name == "re":
        resp = restart_scraper(config_path)
        response.message(resp)
    elif cmd_name == "h":
        resp = help()
        response.message(resp)
    elif cmd_name == "l":
        resp = add_link(config_path, ' '.join(cmd[1:]))
        response.message(resp)
    elif cmd_name == "rl":
        resp = remove_link(config_path, int(cmd[1]))
        response.message(resp)
    elif cmd_name == "ll":
        resp = list_links(config_path)
        response.message(resp)
    elif cmd_name == "f":
        resp = add_filter(config_path, ' '.join(cmd[1:]))
        response.message(resp)
    elif cmd_name == "rf":
        resp = remove_filter(config_path, ' '.join(cmd[1:]))
        response.message(resp)
    elif cmd_name == "lf":
        resp = list_filters(config_path)
        response.message(resp)
    elif cmd_name == "ct":
        resp = list_filters(config_path)
        response.message(resp)
    else:
        resp = help()
        response.message(resp)

    return Response(content=str(response), media_type="application/xml")
