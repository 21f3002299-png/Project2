# receive_request.py
import os
import json
import subprocess

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import httpx

# load environment variables
load_dotenv()

AIPIPE_TOKEN = os.getenv("AIPIPE_TOKEN")
AIPIPE_URL = "https://aipipe.org/openrouter/v1/chat/completions"
SECRET_KEY = os.getenv("SECRET_KEY")  

app = FastAPI()

def process_request(data: dict):
    
    print("Processing request for:", data.get("email"))

    email = data.get("email")
    secret = data.get("secret")
    quiz_url = data.get("url")

    # prompt sent to LLM to generate solver script
    prompt_for_llm = f"""You are an intelligent code generator. Write a python program with httpx 
    to read the given url 1.find the quiz given in that page that may invlove data sourcing, preparation, analysis, and visualization .
    2.generate the appropriate answer using LLM API (like AIPIPE) with the following token: {AIPIPE_TOKEN}
    3.then POST the answer back to the submission endpoint found on that page.
    
    Note:Make sure to include all necessary headers and handle any required JSON formatting for both the LLM request and the submission. 
    The script should be fully functional and ready to run.
    Scritly do not generate any preamble or boilerplate sentence in you respose,just the code.
"""

   
    llm_response = httpx.post(
        AIPIPE_URL,
        headers={
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "authorization": f"Bearer {AIPIPE_TOKEN}",
            "content-type": "application/json",
        },
        json={
            "model": "openai/gpt-4.1-nano",  # or the model you want
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that generates python scripts.",
                },
                {"role": "user", "content": prompt_for_llm},
            ],
        },
    )

    answer_script = llm_response.json()

    # use subprocess to run the generated script
    generated = answer_script["choices"][0]["message"]["content"]

    with open("generated_script.py", "w", encoding="utf-8") as f:
        f.write(generated)

    completed = subprocess.run(
        ["python3", "generated_script.py"],
        capture_output=True,
        text=True,
    )
    stdout = completed.stdout
    stderr = completed.stderr

    print("Finished processing for:", data.get("email"))
    print("STDOUT:", stdout)
    print("STDERR:", stderr)


@app.post("/receive_request")
async def receive_request(request: Request, background_tasks: BackgroundTasks):
    # try to read JSON; if it fails, return 400
    try:
        data = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"message": "Invalid JSON"},
        )

    if not isinstance(data, dict):
        return JSONResponse(
            status_code=400,
            content={"message": "Invalid JSON"},
        )

    email = data.get("email")
    secret = data.get("secret")
    url = data.get("url")


    if not email or not secret or not url:
        return JSONResponse(
            status_code=400,
            content={"message": "Invalid JSON"},
        )

   
    if secret != API_TOKEN:  # API_TOKEN is the token we have stored on our side
        return JSONResponse(
            status_code=403,
            content={"message": "Forbidden"},
        )

   
    background_tasks.add_task(process_request, data)
    return JSONResponse(
        status_code=200,
        content={"message": "Request accepted"},
    )



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

