import arxivscraper
import pandas as pd
import json
import os
from openai import OpenAI
import time

client = OpenAI()


def scrape_ai(start_date, end_date):
    folder = "ARXIV"
    if not os.path.exists(folder):
        # If the folder does not exist, create it
        os.makedirs(folder)

    scraper = arxivscraper.Scraper(category='cs', date_from=start_date, date_until=end_date,
                                   filters={'categories': ['cs.AI']})
    output = scraper.scrape()

    cols = ('id', 'title', 'abstract', 'doi', 'created', 'url', 'authors')
    df = pd.DataFrame(output, columns=cols)
    json_data = df.to_json(orient='records')
    formatted_json = json.loads(json_data)
    with open('ARXIV/arxiv_data.json', 'w') as file:
        json.dump(formatted_json, file, indent=4)


def upload_file(assistant_id):
    folder = 'ARXIV'
    file_ids=[]

    # Iterate through each file in the specified folder
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)

        # Check if it's a file and not a directory
        if os.path.isfile(file_path):
            # Upload the file
            response = client.files.create(
                file=open(file_path, "rb"),
                purpose="assistants"
            )

            # Extract the file ID from the response
            file_id = response.id

            if file_id:
                # Serve the file ID to the assistant_file endpoint
                assistant_file = client.beta.assistants.files.create(
                    assistant_id=assistant_id,
                    file_id=file_id
                )
                file_ids.append(file_id)
    return file_ids


def setup_assistant(client, assistant_name):
    # create a new agent
    assistant = client.beta.assistants.create(
        name=assistant_name,
        instructions=f"""
            You are an intelligent and helpful research assistant. Your name is {assistant_name}. You will work with the user to
             help them learn new updates on AI advancements from data within a json file. You will analyze the json file,
             find the most relevant papers to the user's learning request, and output a summary of the articles and their importance in one message. 
             Always output the links to the papers after your summarize them. 
            """,
        model="gpt-4-1106-preview",
        tools=[{"type": "retrieval"}, {"type": "code_interpreter"}]
    )
    # Create a new thread
    thread = client.beta.threads.create()
    return assistant.id, thread.id


def send_message(client, thread_id, task, file_ids):
    # Create a new thread message with the provided task
    thread_message = client.beta.threads.messages.create(
        thread_id,
        role="user",
        content=task,
        file_ids=file_ids
    )
    return thread_message


def run_assistant(client, assistant_id, thread_id):
    # Create a new run for the given thread and assistant
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    # Loop until the run status is either "completed" or "requires_action"
    while run.status == "in_progress" or run.status == "queued":
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )

        # At this point, the status is either "completed" or "requires_action"
        if run.status == "completed":
            return client.beta.threads.messages.list(
                thread_id=thread_id
            )


def save_session(assistant_id, thread_id, user_name_input, file_ids, file_path='arxiv_sessions.json'):
    # Check if file exists and load data, else initialize empty data
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
    else:
        data = {"sessions": {}}

    # Find the next session number
    next_session_number = str(len(data["sessions"]) + 1)

    # Add the new session
    data["sessions"][next_session_number] = {
        "Assistant ID": assistant_id,
        "Thread ID": thread_id,
        "User Name Input": user_name_input,
        "File IDs": file_ids
    }

    # Save data back to file
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)


def display_sessions(file_path='arxiv_sessions.json'):
    if not os.path.exists(file_path):
        print("No sessions available.")
        return

    with open(file_path, 'r') as file:
        data = json.load(file)

    print("Available Sessions:")
    for number, session in data["sessions"].items():
        print(f"Session {number}: {session['User Name Input']}")

def get_session_data(session_number, file_path='arxiv_sessions.json'):
    with open(file_path, 'r') as file:
        data = json.load(file)

    session = data["sessions"].get(session_number)
    if session:
        return session["Assistant ID"], session["Thread ID"], session["User Name Input"], session["File IDs"]
    else:
        print("Session not found.")
        return None, None


def collect_message_history(assistant_id, thread_id, user_name_input):
    messages = run_assistant(client, assistant_id, thread_id)
    message_dict = json.loads(messages.model_dump_json())

    with open(f'{user_name_input}_message_log.txt', 'w') as message_log:
        for message in reversed(message_dict['data']):
            # Extracting the text value from the message
            text_value = message['content'][0]['text']['value']

            # Adding a prefix to distinguish between user and assistant messages
            if message['role'] == 'assistant':
                prefix = f"{user_name_input}: "
            else:  # Assuming any other role is the user
                prefix = "You: "

            # Writing the prefixed message to the log
            message_log.write(prefix + text_value + '\n')

    return f"Messages saved to {user_name_input}_message_log.txt"


def main_loop():
    print("\n------------------------------ Welcome to Arxiv GPT! ------------------------------\n")
    user_choice = input("Type 'n' to make a new agent. Press 'Enter' to choose an existing "
                      "session. ")
    if user_choice == 'n':
        scrape_ai(start_date='2023-11-27', end_date='2023-11-27')
        user_name_input = input("Type a Name for this Assistant (usually today's date is best): ")
        IDS = setup_assistant(client, assistant_name=user_name_input)
        assistant_id = IDS[0]
        thread_id = IDS[1]
        file_ids = upload_file(assistant_id)
        save_session(assistant_id, thread_id, user_name_input, file_ids)
        print(f"Created Session with {user_name_input}, Assistant ID: {assistant_id} and Thread ID: {thread_id}\n"
              f"Please tell the assistant what specific subject you want to focus on.")
    else:
        display_sessions()
        chosen_session_number = input("Enter the session number to load: ")
        assistant_id, thread_id, user_name_input, file_ids = get_session_data(chosen_session_number)
        print(f"Started a new session with {user_name_input}, Assistant ID: {assistant_id} and Thread ID: {thread_id}")
    if assistant_id and thread_id:
        while True:
            user_message = input("You: ")
            if user_message.lower() in {'exit', 'exit.'}:
                print("Exiting the program.")
                print(collect_message_history(assistant_id, thread_id, user_name_input))
                break
            send_message(client, thread_id, user_message, file_ids)
            messages = run_assistant(client, assistant_id, thread_id)
            message_dict = json.loads(messages.model_dump_json())
            most_recent_message = message_dict['data'][0]
            assistant_message = most_recent_message['content'][0]['text']['value']
            print(f"{user_name_input}: {assistant_message}")

if __name__ == "__main__":
    main_loop()
