from openai import OpenAI
import gradio as gr
import time

def get_assistant(client):
    assistants = client.beta.assistants.list(
        order="desc",
        limit="20",
    )

    for assistant in assistants.data:
        if assistant.name == "Talent Recruiter":
            return assistant


    assistant = client.beta.assistants.create(
        instructions="As a Recruiter, your responsibilities include reviewing resumes, extracting relevant information, and identifying the top 5 candidates that closely align with the job description. Additionally, you will be tasked with generating core interview questions for these candidates and creating an evaluation template for the interview process.",
        name="Talent Recruiter",
        model="gpt-4-turbo-preview",
    )

    return assistant


def on_submit(api_key, job, resumes):
    client = OpenAI(api_key=api_key)
    assistant = get_assistant()

    files = [client.files.create(file=open(resume, "rb"), purpose="assistants") for resume in resumes]

    
    print('Files', files)
    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": job
            },
            {
                "role": "user",
                "content": "Please find the resumes attached below. I need to find the top 5 candidates that closely align with the job description."
            },
            {
                "role": "user",
                "content": "List of candidates",
                "file_ids": [file.id for file in files]
            }
        ]
    )


    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )


    while True:
        time.sleep(5)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        print('Status', run.status)
        if run.status == "completed" or run.status == "failed" or run.status == "cancelled" or run.status == "expired":
            break
    
    # Clean up files
    [client.files.delete(file.id) for file in files]

    messages = client.beta.threads.messages.list(thread.id)
    # get first message
    content =  messages.data[0].content
    print('Content', content)

    message = content[0].text.value
    return message
  
    

inputs = [
    gr.Textbox(label="OpenAI API Key", type="password"),
    gr.Textbox(label="Enter Job Description", lines=5),
    gr.File(label="Select Resumes", file_count="multiple")
]

outputs = [
    gr.Markdown("Resume Matched")
]

ui = gr.Interface(
    fn=on_submit,
    inputs=inputs,
    outputs=outputs,
)

ui.launch()