import datetime
import re
import requests
from jira import JIRA
import holidays_jp
import jira.client

# Jira server url
server_url = "Your_Jira_server_url"
# jira test user AuthToken
auth_token = "Your_Jira_Access_Token"
# my teams Channel webhook Url
# create channel -> click on connector -> configure incoming webhook url -> copy/paste url here for the specific channel
my_teams_channel_webhook = 'Your_Teams_channel_webhook'
list_assignee_data = []
assignee_name_list = []
issue_url_list = []

jira = JIRA(
    server=server_url,
    options={"headers": {"Authorization": "Basic auth_token"}})


def add_url_message_field(issue_url_list):
    body = []
    body.clear()
    for i in range(len(issue_url_list) - 1):
        y = {
            "type": "TextBlock",
            "text": f" [{issue_url_list[i]}]({issue_url_list[i]})"
        }
        body.append(y)

    return body


def notify_on_teams(issue_url_list, assi):
    print(issue_url_list)
    url = my_teams_channel_webhook
    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "type": "AdaptiveCard",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": f"Hi <at>{assi}</at>"
                        },
                        {
                            "type": "TextBlock",
                            "text": "Please update your tickets"
                        }
                    ],
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "version": "1.2",
                    "msteams": {
                        "entities": [
                            {
                                "type": "mention",
                                "text": f"<at>{assi}</at>",
                                "mentioned": {
                                    "id": f"{assi}",
                                    "name": f"{assi}"
                                }
                            }
                        ]
                    }
                }

            }]
    }
    attachments = payload['attachments']
    for attach in attachments:
        content = attach['content']
        body = content['body']
        add_text_url = add_url_message_field(issue_url_list)
        for add_text in add_text_url:
            body.append(add_text)
    headers = {"Content-Type": "application/json"}
    r = requests.post(url, headers=headers, json=payload)


# get jira issue which have fix version and not updated for 2 days
def get_issue_assignee_based_onProject():
    today_date = datetime.date.today().strftime('%Y-%m-%d')
    for issue in jira.search_issues('project = AIPB AND updated < -2d'.format(today_date)):
        version_list = issue.fields.fixVersions
        for version in version_list:
            if version is not None and str(issue.fields.status) != 'Closed':
                assignee = issue.fields.assignee
                list_assignee_data.append(assignee)


def get_issue_assignee_based_onIOSProject():
    today_date = datetime.date.today().strftime('%Y-%m-%d')
    for issue in jira.search_issues('project = IIPB AND updated < -2d'.format(today_date)):
        version_list = issue.fields.fixVersions
        for version in version_list:
            if version is not None and str(issue.fields.status) != 'Closed':
                assignee = issue.fields.assignee
                list_assignee_data.append(assignee)


def filter_assignee_issues_based_on_status():
    for assignee_data in list_assignee_data:
        assignee_name_list.append(assignee_data)
    # filter duplicate values
    mylist = assignee_name_list
    mylist = list(dict.fromkeys(mylist))
    for assi in mylist:
        issue_url_list.clear()
        assignee_name = assi.name
        assignee_display_name = assi.displayName
        regex = re.compile('[@_!#$%^&*()<>?/\|}{~:]')
        if regex.search(assignee_name) is None:
            for issue in jira.search_issues(f'assignee = {str(assignee_name)} AND Updated < -2d'):
                version_list = issue.fields.fixVersions
                for version in version_list:
                    if version is not None and str(issue.fields.status) != 'Closed' and str(
                            issue.fields.status) != 'Resolved':
                        issue_url = server_url + '/browse/' + str(issue.key)
                        issue_url_list.append(issue_url)
            if len(issue_url_list) != 0:
                notify_on_teams(issue_url_list, assignee_display_name)
        else:
            print("User is not defined")


# Japan holidays calendar and notification time set
def get_japan_holiday():
    holidays = holidays_jp.CountryHolidays.between('JP', 2022, 2030)
    today_date = datetime.date.today().strftime('%Y-%m-%d')
    today_time = datetime.datetime.now().strftime("%H:%M")
    if today_date not in holidays: # and today_time == '10:00':
        get_issue_assignee_based_onProject()
        get_issue_assignee_based_onIOSProject()
        filter_assignee_issues_based_on_status()

    else:
        print("Please Comment the Specified time and date")


get_japan_holiday()
