import requests
import os
import openai
import json
from dotenv import load_dotenv

# 환경 변수를 로드합니다.
load_dotenv()
client = openai.OpenAI()
BASE_URL = "https://nomad-movies.nomadcoders.workers.dev"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def get_popular_movies():
    response = requests.get(f"{BASE_URL}/movies")
    if response.status_code == 200:
        return response.json()  # 영화 목록을 반환
    else:
        return {"error": "Failed to fetch popular movies"}

def get_movie_details(id):
    response = requests.get(f"{BASE_URL}/movies/{id}")
    if response.status_code == 200:
        return response.json()  # 영화 상세 정보를 반환
    else:
        return {"error": "Failed to fetch movie details"}

def get_movie_credits(id):
    response = requests.get(f"{BASE_URL}/movies/{id}/credits")
    if response.status_code == 200:
        return response.json()  # 출연진 및 제작진 정보를 반환
    else:
        return {"error": "Failed to fetch movie credits"}


tools = [
    {"type": "function", "function": {
        "name": "get_popular_movies",
        "description": "인기 영화 목록을 가져옵니다.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    }},
    {"type": "function", "function": {
        "name": "get_movie_details",
        "description": "특정 ID의 영화 상세 정보를 가져옵니다.",
        "parameters": {"type": "object", "properties": {
            "id": {"type": "integer", "description": "영화 ID"}
        }, "required": ["id"]},
    }},
    {"type": "function", "function": {
        "name": "get_movie_credits",
        "description": "특정 ID의 영화 출연진을 가져옵니다.",
        "parameters": {"type": "object", "properties": {
            "id": {"type": "integer", "description": "영화 ID"}
        }, "required": ["id"]},
    }},
]

three_functions = {
    "get_popular_movies": get_popular_movies,
    "get_movie_details": get_movie_details,
    "get_movie_credits": get_movie_credits,
}

def ask(question):
    messages = [{"role": "user", "content": question}]

    while True:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        msg = response.choices[0].message

        if msg.tool_calls: 
            messages.append(msg)
            for tool_call in msg.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                print(f"[함수 실행중] {func_name}({func_args})")
                result = three_functions[func_name](**func_args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })
        else:
            return msg.content 


print(ask("지금 인기 있는 영화가 무엇인지 알려줘"))
print(ask("movie ID 550에 해당하는 영화가 무엇인지 알려줘"))
print(ask("movie ID 550에 해당하는 영화에 누가 출연하는지 알려줘"))