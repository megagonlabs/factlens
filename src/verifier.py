import os
from prompts import VERIFIER_PROMPT
from config import MODEL_NAME
from src.open_ai import OpenAI

class Verifier:
    '''
    Verify if claim is true or false based on the context provided
    '''
    def __init__(self):
        self.model_name = MODEL_NAME
        self.model = OpenAI(os.environ['OPENAI_API_KEY'], os.environ['OPENAI_ORGANIZATION'])

    def verify_claim(self, claim, context):
        user_prompt = VERIFIER_PROMPT.format(claim=claim, context=context)  

        model_config = {
            "model": MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": "Your answer should only be a label: \'true\', or \'false\'"
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "temperature": 0,
        }
        response = self.model.call(model_config)
        content = response.choices[0]["message"]["content"]
        return content.strip.lower()