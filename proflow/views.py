from .files import return_files
from .explain import explain_task, detail_task
from .todos import generate_todos
import requests
import flask
import proflow
from slack_sdk import WebClient
import os
from .codegen import generate_code
from .gitutils import get_branch_name, upload_files_to_github
import asyncio
from .title import generate_title
from dotenv import load_dotenv
load_dotenv()

LINEAR_KEY = os.environ['LINEAR_KEY']
SLACK_TOKEN = os.environ['SLACK TOKEN']

slack_channel_id = None


@proflow.app.route('/github', methods=['POST'])
def handle_github():
    print(flask.request.json)
    return


def ask_linear(query):
    url = 'https://api.linear.app/graphql'
    query = {'query': query}
    headers = {
        'Content-Type': 'application/json',
        'Authorization': LINEAR_KEY,
    }
    response = requests.post(url, json=query, headers=headers).json()
    return response


@proflow.app.route('/', methods=['POST'])
def handle_linear_webhook():
    data = flask.request.json
    if data["action"] != "create":
        return {"assigned": False, "slack": False}

    ticket_creator = data["data"]["creatorId"]
    emails_for_slack = []

    # grab all users and current assignments from linear
    all_issues = ask_linear("{ issues { nodes { assignee { id } } } }")
    all_people = ask_linear("{ users { nodes { id } } }")

    # populate assignees
    assignees = {}
    nodes = all_people['data']['users']['nodes']
    for node in nodes:
        assignees[node['id']] = 0

    # count how many issues are currently assigned to each assignee
    nodes = all_issues['data']['issues']['nodes']
    for node in nodes:
        if "assignee" in node and node['assignee'] is not None:
            assignees[node['assignee']['id']] += 1

    # get most free person
    most_free_id = min(assignees, key=assignees.get)
    most_free_user = ask_linear(
        '{ user(id: "' + most_free_id + '") { email } }')
    emails_for_slack.append(most_free_user['data']['user']['email'])

    # get ticket creator's email
    ticket_creator_user = ask_linear(
        '{ user(id: "' + ticket_creator + '") { email } }')
    emails_for_slack.append(ticket_creator_user['data']['user']['email'])

    # assign ticket to most free user
    ticket_id = data["data"]["id"]
    ask_linear('mutation { issueUpdate(id: "' + ticket_id +
               '", input: { assigneeId: "' + most_free_id + '" }) { success issue { id } } }')

    # get todos from other file
    # get pr link from other file

    asyncio.run(codegenStuff(data["data"]["title"] + ". " + data["data"].get("description", "n/a"), data, emails_for_slack))

    # todos = explain_task(data["data"]["title"])
    # files = return_files(todos, verbose=True)
    # generate_todos(todos, files)

    return {"assigned": True, "slack": True}


async def codegenStuff(ticket, data, emails_for_slack):
    task = explain_task(ticket)
    title = generate_title(task['text'])
    files = return_files(task['text'], verbose=True)
    if task['codeGen']:
        details = detail_task(task['text'], files)
        todos = await generate_code(details, files)
    else:
        details = generate_todos(task['text'], files)
    branch = get_branch_name(task['text'])
    upload_files_to_github(title, task, branch, todos)
    pr_link = f"https://github.com/{os.environ['GITHUB_ORG']}/{os.environ['GITHUB_REPO']}/pulls"
    setup_slack(data, emails_for_slack, details, pr_link, files)
  

def setup_slack(data, emails_for_slack, todos, pr_link, files):
    global slack_channel_id

    # make slack chat
    user_ids = []

    # files = "<" + "|This message *is* a link>, ".join(files)

    file_link = f"https://github.com/{os.environ['GITHUB_ORG']}/{os.environ['GITHUB_REPO']}/blob/{os.environ['GITHUB_BRANCH']}/"
    
    file_str = ""
    for file in files:
        file_str += f"<{file_link + file}|{file}>, "
    file_str = file_str[:-2]

    client = WebClient(
        token="")

    def add_user_id(email):
        response = client.users_lookupByEmail(email=email)
        if not response['ok']:
            print(response['error'])
            return
        client_id = response['user']['id']
        user_ids.append(client_id)

    for email in emails_for_slack:
        add_user_id(email)

    resp = client.conversations_list()["channels"]
    existing_channels = [channel["name"] for channel in resp]

    channel_name = ("proflow-" + data["data"]["team"]
                    ["key"] + "-tickets").lower()
    
    if channel_name in existing_channels and not slack_channel_id:
        slack_channel_id = resp[existing_channels.index(channel_name)]["id"]
    
    # create convo
    if channel_name not in existing_channels:

        response = client.conversations_create(
            name=channel_name,
            is_private=False,
        )

        slack_channel_id = response['channel']['id']

        if not response['ok']:
            print(response['error'])
            return {"assigned": True, "slack": False}

        # invite users
        response = client.conversations_invite(users=user_ids, channel=slack_channel_id)

    # send message to chat

    # fields needed: assignee, task owner, title, description, TODOs, files, PR
    response = client.chat_postMessage(
        channel=slack_channel_id,
        text=f"""
*Assignee*: <@{user_ids[0]}|cal>
*PM*: <@{user_ids[1]}|cal>

*Title*: {data["data"]["title"]}
*Description*: {data["data"].get("description", "n/a")}

Here is a list of suggested todos:
{todos}

These are relevant files: {file_str}
Here is a draft pull request: {pr_link}

Happy hacking!
    """)

    return


# {'action': 'update',
#  'createdAt': '2023-06-02T21:06:48.718Z',
#  'data':
#     {
#         'id': '0f66305c-20e7-4d95-82cb-6fdb345603f6',
#         'createdAt': '2023-06-02T17:54:15.637Z',
#         'updatedAt': '2023-06-02T21:06:48.718Z',
#         'number': 11,
#         'title': 'whats asdasdasasdd',
#         'priority': 0,
#         'boardOrder': 0,
#         'sortOrder': -14629,
#         'teamId': 'c16f76f7-33a1-49a5-b38e-95dd97f480f7',
#         'previousIdentifiers': [],
#         'creatorId': '12bfc6ff-cce9-44c5-8a85-ee8f35547e66',
#         'stateId': '587545a2-0687-464d-af7f-8faf87f1a894',
#         'priorityLabel': 'No priority', 'subscriberIds': ['12bfc6ff-cce9-44c5-8a85-ee8f35547e66'], 'labelIds': [],
#         'state':
#             {'id': '587545a2-0687-464d-af7f-8faf87f1a894', 'color': '#e2e2e2', 'name': 'Todo', 'type': 'unstarted'},
#         'team': {'id': 'c16f76f7-33a1-49a5-b38e-95dd97f480f7', 'key': 'PRO', 'name': 'Proflow'},
#         'labels': [],
#         'description': 'test description @sagek1 ',
#         'descriptionData': '{"type":"doc","content":[{"type":"paragraph","content":[{"text":"test description ","type":"text"},{"type":"suggestion_userMentions","attrs":{"id":"12bfc6ff-cce9-44c5-8a85-ee8f35547e66","label":"sagek1"}},{"text":" ","type":"text"}]}]}'
#         },
# 'updatedFrom':
#     {'updatedAt': '2023-06-02T21:06:34.819Z', 'title': 'whats asdasdasd'},
# 'url': 'https://linear.app/proflow/issue/PRO-11/whats-asdasdasasdd',
# 'type': 'Issue', 'organizationId': '6f68d1c2-1e3e-427c-bb3b-52a6fdd7b4bb', 'webhookTimestamp': 1685740008998
# }
