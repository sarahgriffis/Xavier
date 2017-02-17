# coding: utf-8

#1. get key and board id
#go to sandbox to get board id https://developers.trello.com/sandbox

#2. get server side auth token
#Resource: authorize with https://developers.trello.com/authorize
#create server side authorized token with
#https://trello.com/1/authorize?key={key}&expiration=never&response_type=token&scope=read,write

#3.Add user with auth key to Trello board
import json
import requests #trello api calls
from datetime import datetime #DONE column tag
from pytz import timezone #DONE column tag
import argparse #command line arguments
from argparse import ArgumentParser
import pdb
from trello_card import TrelloCard
from trello_api import TrelloApi

TRELLO_API_ENDPOINT="https://api.trello.com/1/"
KEY=""
TOKEN=""
SLACK_WEBHOOK_DEPLOY_ALL='https://hooks.slack.com/services/{}'
SLACK_WEBHOOK_DEPLOY_PROD='https://hooks.slack.com/services/{}/{}'
REPOS={
       'storefront': 'https://github.com/{}',
       'admin': 'https://github.com/{}',
       'worker': 'https://github.com/{}',
       'coreapi': 'https://github.com/{}',
       'fbapi': 'https://github.com/{}',
       'slicelink': 'https://github.com/{}'
     }

def tag():
    return '{:%Y-%m-%d %H:%M:%S} EST'.format(datetime.now(timezone('US/Eastern')))

def create_attachments_json(card_array_json):
    attachments = []
    for card in card_array_json:
        t = TrelloCard(card)
        attachments.append(t.json_blob)
    return attachments

def card_text_title(service, env, time, commit, lc, branch, rollback_id, is_rollback):
    mini_commit = commit[0:07]
    commit_link = "*Commit:* " + "<" + REPOS[service] + "/commit/" + commit + "|" + mini_commit + ">  "

    if is_rollback:
        text = "Rolled back *" + service + "* on *" + env + "* at: " + time + " \n" + commit_link + " \n"
    else:
        branch_txt = "*Branch:* " + branch
        text = "Deployed *" + service + "* to *" + env + "* at: " + time + " \n" + commit_link + branch_txt + " \n"

    if (lc is not None) & (is_rollback == 1):
        return text + "*Live Config:* " + lc
    elif lc == None:
        return text
    else:
        return text + "*Live Config:* " + lc + " \n" + "*Rollback Candidate:* " + rollback_id

# search lists based on name
def search_lists_by_name(lists_json, text):
    return [item for item in lists_json if text in item["name"].lower()]

#move cards
def move_cards_by_date(time, old_list_id, source_column):
    #check all DONE columns timestamps
    lists = trello_api.get_lists()
    done_lists = search_lists_by_name(lists.json(), 'done')
    date = time[0:10]
    todays_column = search_lists_by_name(done_lists, date)

    #if date of time is same, append to column
    if len(todays_column) > 0:
        trello_api.move_all_cards(old_list_id, todays_column[0]["id"])

    #else create new list
    else:
        new_list = trello_api.create_new_list(date, source_column["pos"] + 1)
        new_list_id = new_list.json()["id"]
        trello_api.move_all_cards(old_list_id, new_list_id)

def move_cards_by_sprint(old_list_id, tag=None):
    lists = trello_api.get_lists()
    done_lists = search_lists_by_name(lists.json(), 'done')
    #find done list with min position (done_list_sprint_id)
    done_list_pos_id = min(float(d["pos"]) for d in done_lists)
    done_list_id = [x for x in done_lists if x["pos"] == done_list_pos_id][0]["id"]

    if tag == None:
        trello_api.move_all_cards(old_list_id, done_list_id)
    else:
        cards = trello_api.fetch_all_cards(old_list_id)

        for card in cards.json():
            if card['labels'][0]['name'] == tag:
                r = trello_api.edit_card(card['id'], {'idList': done_list_id})

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--board_id",             dest="BOARD_ID",             help="required Trello board id",    required=False)
    parser.add_argument("--source_column_name",   dest="SOURCE_COLUMN_NAME",   help="required source column name", required=False)
    parser.add_argument("--git_sha",              dest="GIT_SHA",              help="SHA of latest commit",        required=True)
    parser.add_argument("--git_branch",           dest="GIT_BRANCH",           help="git branch name",             required=False)
    parser.add_argument("--aws_launch_config_id", dest="AWS_LAUNCH_CONFIG_ID", help="AWS launch config id",        required=False)
    parser.add_argument("--aws_lc_rollback_id",   dest="AWS_LC_ROLLBACK_ID",   help="Last known good config",      required=False)
    parser.add_argument("--trello_smack",         dest="TRELLO_SMACK",         help="boolean for prod",            required=False, type=int, default=0)
    parser.add_argument("--service",              dest="SERVICE",              help="service",                     required=True)
    parser.add_argument("--environment",          dest="ENV",                  help="environment",                 required=True)
    parser.add_argument("--rollback",             dest="ROLLBACK",             help="boolean for rollback",        required=False, type=int, default=0)

    #service = ['admin', 'storefront', 'worker', 'coreapi', 'fbapi', 'slicelink', 'cron']
    #environment = ['production', 'staging']

    args = parser.parse_args()
    BOARD_ID = args.BOARD_ID
    SOURCE_COLUMN_NAME = args.SOURCE_COLUMN_NAME
    GIT_SHA = args.GIT_SHA
    GIT_BRANCH = args.GIT_BRANCH
    AWS_LAUNCH_CONFIG_ID = args.AWS_LAUNCH_CONFIG_ID
    AWS_LC_ROLLBACK_ID = args.AWS_LC_ROLLBACK_ID
    TRELLO_SMACK = args.TRELLO_SMACK
    SERVICE = args.SERVICE
    ENV = args.ENV
    ROLLBACK = args.ROLLBACK

    #rollback, service, environment, git_sha (LKG), live config)

    time = tag()
    trello_api = TrelloApi(trello_api_endpoint=TRELLO_API_ENDPOINT, key=KEY, token=TOKEN, board_id=BOARD_ID)

    if TRELLO_SMACK:
        source_column = trello_api.find_column(column_name=SOURCE_COLUMN_NAME)
        old_list_id = source_column["id"]
        cards = trello_api.fetch_all_cards(old_list_id)

        #mark card with time
        for card in cards.json():
            trello_api.create_comment(old_list_id, card["id"], 'deployed ' + time)

        if SERVICE == "storefront":
            move_cards_by_date(time, old_list_id, source_column)
            attachments = create_attachments_json(cards.json())
        elif SERVICE == "admin":
            move_cards_by_sprint(old_list_id)
            attachments = create_attachments_json(cards.json())
        elif (SERVICE == "coreapi") | (SERVICE == "fbapi") | (SERVICE == "slicelink"):
            move_cards_by_sprint(old_list_id, SERVICE)
            cards2 = [x for x in cards.json() if x['labels'][0]['name'] == SERVICE]
            attachments = create_attachments_json(cards2)

        card_text = {
            "text": card_text_title(SERVICE, ENV, time, GIT_SHA, AWS_LAUNCH_CONFIG_ID, GIT_BRANCH, AWS_LC_ROLLBACK_ID, ROLLBACK),
            "attachments": attachments,
            "mrkdwn": "true"
        }

    else:
        card_text = {
            "text": card_text_title(SERVICE, ENV, time, GIT_SHA, AWS_LAUNCH_CONFIG_ID, GIT_BRANCH, AWS_LC_ROLLBACK_ID, ROLLBACK),
            "mrkdwn": "true"
        }

    if ENV == 'production':
        requests.post(SLACK_WEBHOOK_DEPLOY_PROD, data = json.dumps(card_text))
        requests.post(SLACK_WEBHOOK_DEPLOY_ALL, data = json.dumps(card_text))
    else:
        requests.post(SLACK_WEBHOOK_DEPLOY_ALL, data = json.dumps(card_text))

#TODO: figure out how we want to detect environment vs trello_smack
#requests.post(SLACK_WEBHOOK_DEPLOY_PROD, data = json.dumps(card_text))
