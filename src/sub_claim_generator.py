import json
import os
import random

import pandas as pd
from config import MODEL_NAME
from prompts import DEMONSTRATIONS, SUB_CLAIM_GENERATOR_PROMPT
from tqdm import tqdm

from src.open_ai import OpenAI

class SubClaimGenerator:
    '''
    Decompose claim into sub-claims
    '''
    def __init__(self):
        self.model_name = MODEL_NAME
        self.model = OpenAI(os.environ['OPENAI_API_KEY'], os.environ['OPENAI_ORGANIZATION'])
    
    def set_data(self, path):
        self.data = pd.read_csv(path)

    def set_output_file(self, path):
        self.output_file = path

    def shuffle_demonstrations(self):
        '''
        Shuffle demonstrations by picking 3 of the 4 expert-curated decompositions and then shuffle. 
        This reduces bias during prompting.
        '''
        demonstrations = random.sample(DEMONSTRATIONS, 3)
        random.shuffle(demonstrations)
        return "\n\n".join(demonstrations)

    def generate_sub_claims(self):
        '''
        Decompose sub-claims using few-shot prompting method. 
        '''
        sub_claims = []
        data = self.data

        for _, row in tqdm(data.iterrows(), total=len(data)):
            claim = row['claim']
            demonstrations = self.shuffle_demonstrations()
            
            user_prompt = SUB_CLAIM_GENERATOR_PROMPT.format(demonstrations=demonstrations, claim=claim)  

            model_config = {
                "model": MODEL_NAME,
                "messages": [
                    {
                        "role": "system",
                        "content": "Your answer should be strictly be in form of a comma separated list. In JSON format with key \"sub_claims\""
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                "temperature": 0,
                "response_format": {
                    "type": "json_object"
                }
            }
            response = self.model.call(model_config)
            content = response.choices[0]["message"]["content"]
            content = json.loads(content)
            content = content["sub_claims"]
            sub_claims.append(content)

        data['sub_claims'] = sub_claims
        data.to_csv(self.output_file, index=False)

def main():
    sub_claim_generator = SubClaimGenerator()
    sub_claim_generator.set_data(path = 'data/coverbench_dataset.csv')
    sub_claim_generator.set_output_file('data/sub_claims.csv') # set output file
    sub_claim_generator.generate_sub_claims()

if __name__ == '__main__':
    if not MODEL_NAME:
        raise Exception("MODEL_NAME not set. Please set MODEL_NAME in config.py")
    main()