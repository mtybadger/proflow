# TEST FILE
from todos import generate_todos
from codegen import generate_code
from explain import explain_task, detail_task
from files import return_files
from gitutils import get_branch_name, upload_files_to_github
from dotenv import load_dotenv
import asyncio
from title import generate_title
load_dotenv() 

async def main():
    ticket = "Change all the colors in the primary Tailwind color scheme to purple colors"
    task = explain_task(ticket)
    title = generate_title(task['text'])
    print(task['text'])
    files = return_files(task['text'], verbose=True)
    if task['codeGen']:
        detail = detail_task(task['text'], files)
        todos = await generate_code(detail, files)
    else:   
        todos = generate_todos(task['text'], files)
    branch = get_branch_name(task['text'])
    upload_files_to_github(title, task, branch, todos)

if __name__ == "__main__":
  asyncio.run(main())