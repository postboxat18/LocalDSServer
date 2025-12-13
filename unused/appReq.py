import json
import sys
from datetime import datetime

import requests

url = "http://localhost:8000/v1/chat/completions"

headers = {
    "Content-Type": "application/json",
}


def log_exception(e, func_name, logfile):
    exc_type, exc_obj, tb = sys.exc_info()
    lineno = tb.tb_lineno
    error_message = f"\nIn {func_name} LINE.NO-{lineno} : {exc_obj}"
    with open(logfile, 'a', encoding='utf-8') as fp:
        fp.writelines(error_message)


def process_logger(process, logfile):
    with open(logfile, 'a', encoding='utf-8') as fp:
        fp.writelines(f'\n{datetime.now()} {process}')


def vllmAPI(context, task, logfile, max_token):
    try:
        input_prompt = f"Context : {context} \n\n task : {task}\n Answer:"

        payload = {
            "messages": [
                {"role": "system",
                 "content": "Give me answer for users questions."},
                {"role": "user", "content": input_prompt},
            ],
            # "model": "meta-llama/Meta-Llama-3-8B-Instruct",
            "model": "meta-llama/Llama-3.1-8B-Instruct",
            # "model": "meta-llama/Llama-3.2-3B-Instruct",
            "stream": False,
            "max_tokens": max_token,
            "stop": None,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "temperature": 0,
            "top_p": 0.95
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        result = response.json()
        if str(response.status_code) != "200":
            process_logger(f"{result}", logfile)
        # print(result)
        content = result['choices'][0]['message']['content']
        return content
    except Exception as e:
        log_exception(e, "vllmAPI", logfile)


context = """ Aravinth Chinnasamy
Software Developer
I am a passionate Software Developer with expertise in Flutter, Android and Python. I specialize in
building mobile applications and backend solutions, with experience in data science and working with
cutting-edge technologies.
aravinthc18@gmail.com 8973396270
Erode, India postboxat18.blogspot.com/
linkedin.com/in/aravinth-c-806049204 github.com/postboxat18
stackoverflow.com/users/16990450/aravinth-c medium.com/@aravinthc18
WORK EXPERIENCE
Software Developer
Adamsbridge Services Private Limited , Coimbatore
05/2024 - Present,
Data Science Projects: Worked on AI models using vLLM , TOC and LLaMA , focusing on scalability and performance. Tools Used: Python, PyTorch, TensorFlow, Jupyter
Notebooks. Patient Portal in Flutter : Developed UI and functionalities
for a seamless user experience. Tools Used: Android Studio, Xcode, Figma. Employee Portal (HRMS) in Flutter: Implemented state
management and integrated backend features. Links : iOS , Android . Tools Used: Android Studio, Xcode, Figma. Flutter Bootstrap : Built a responsive web page using
Flutter and Bootstrap. Link : GitHub . Tools Used : Android
Studio.
Software Developer
Aosta India Private Limited , Coimbatore
09/2021 - 05/2024,
Real Serv in Flutter : Implemented UI and integrated
functionality. Tools Used : Android Studio, Xcode, Figma. BB Clinical Research in Flutter : Developed a clinical
research app. Links : iOS , Android . Tools Used : Android
Studio, Xcode, Figma. Adamsbridge Tickets in Flutter : Built a ticketing system
application. Links : iOS , Android .Tools Used : Android
Studio, Xcode, Figma. BackBone DoctorDesk in Android : Developed the
DoctorDesk mobile app for healthcare. Link : Android . Tools
Used : Android Studio, Jitsi. DialogFlow Project : Developed an AI-powered dialog
system for user interaction. Link : GitHub . Tools Used :
Firebase, Pycharm, DialogFlow. Selenium Automation : Designed an automation framework
for web testing. Link : GitHub . Tools Used : Pycharm, Postman.
CERTIFICATES
Docker for Absolute Beginner and Labs
Experienced in Docker containerization, using Docker Compose and
Docker Hub for efficient deployment and management of multi- container applications. Certified in Docker basics and practice labs.
SKILLS
Dart Python Java Kotlin Git
Postman Firebase Figma Adobe Xd GCS
DialogFlow Jira Docker PuTTY
Jupyter Notebook Google Colab Vllm
Flutter BLoc
PERSONAL PROJECTS
flutter_listfilter
Developed a package to generate filter chips based on a list containing values, utilizing model classes. Link: flutter_listfilter flutter_material_calendar
Created a package enabling the addition of events in a monthly
calendar within Flutter applications. Link: flutter_material_calendar
custom_scroll_date_range_picker
Designed a package allowing users to select date ranges by
scrolling and choosing two dates. Link: custom_scroll_date_range_picker.
EDUCATIONS
Bachelor of Engineering(CSE)
Velalar College of Engineering and
Technology , Thindal,Erode
09/2017 - 05/2021,
DEV COMMUNITY
Stack OverFlow
Medium
pub.dev
LANGUAGES
Tamil English
Projects
Projects"""
task = "From the given context get resume main content."
content = vllmAPI(context, task, "log.txt", 4096)
print(content)
