import os
import base64
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
def encode_img(img_path):
    img_file = open(img_path,"rb")
    return base64.b64encode(img_file.read()).decode("utf-8")
from groq import Groq

query = "is there something wrong"
model ="meta-llama/llama-4-scout-17b-16e-instruct"
def analyze_img(query,encoded_img,model):
    client=Groq()  
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text", 
                    "text": query
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{encoded_img}",
                    },
                },
            ],
        }]
    chat_completion = client.chat.completions.create(
        messages = messages,
        model = model
    )
    return chat_completion.choices[0].message.content
