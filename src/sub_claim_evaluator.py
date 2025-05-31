import ast
import os
import pandas as pd
from prompts import (ATOMICITY_EVALUATION, COLLECTIVE_SUB_CLAIM_EVALUATION,
                     INDIVIDUAL_SUB_CLAIM_EVALUATION)

from config import MODEL_NAME
from src.open_ai import OpenAI
from tqdm import tqdm

class SubClaimEvaluator:
    '''
    Evaluate decomposed sub-claims using LLMs
    '''
    def __init__(self):
        self.model_name = MODEL_NAME
        self.model = OpenAI(os.environ['OPENAI_API_KEY'], os.environ['OPENAI_ORGANIZATION'])
        self.subclaim_level_metrics = [
            "atomicity",
            "sufficiency",
            "fabrication",
            "readability",
        ]
        self.claim_level_metrics = [
            "redundancy",
            "coverage",
        ]
        self.metrics = {
            "atomicity": "if the sub-claim is atomic i.e. it is simple and centers around only one subject and one object, and the verification does not require aggregation of facts or multihop reasoning over concepts. Label the sub-claim as either \"atomic\" which denotes one subject and one object, or \"non-atomic-1\" which denotes one subject, multiple objects, or \"non-atomic-2\" which denotes multiple subjects",
            "sufficiency": "Evaluate the sufficiency of the subclaim in comparison to the original claim. Sufficiency is defined as the ability to be fact-checked without requiring additional contextual information and without ambiguity. If the subclaim is significantly less sufficient than the original claim, meaning it is much more ambiguous or lacks essential context—rate it as \"low.\" If the subclaim is slightly less sufficient, rate it as \"medium\". If the subclaim matches the original claim in sufficiency, with no missing context or added ambiguity, rate it as \"high\"",
            "redundancy": "if the sub-claims contain redundant or repeated information among them, i.e. multiple semantically equivalent sub-claims. Your answer should indicate whether the sub-claims have \"low\", \"medium\" or \"high\" redundancy.",
            "coverage": "if the set of sub-claims cover all the facts and information made in the original claim. Your answer should indicate whether the sub-claims have \"low\", \"medium\" or \"high\" coverage.",
            "fabrication": "if the sub-claim shows a degree of fabrication  with respect to the original claim i.e. how much new information is added which was not present in the original claim. Note this is not to be judged according to the factuality of the original claims or subclaims. Your answer should indicate whether the sub-claim has \"low\", \"medium\" or \"high\" fabrication.",
            "readability": "if the sub-claim is readable to an end user. Your answer should indicate whether the sub-claim has \"low\", \"medium\" or \"high\" readability.",
        }
    
    def set_data(self, path):
        self.data = pd.read_csv(path)

    def set_output_file(self, path):
        self.output_file = path

    def evaluate_sub_claims(self):
        '''
        Evaluate sub-claims using LLMs. 
        '''
        def evaluate(claim, sub_claim, metrics, prompt_template):
            user_prompt = prompt_template.format(metrics = metrics, claim = claim, sub_claims = sub_claim)
            model_config = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a fair evaluator. No additional commentary whatsoever."
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                "temperature": 0,
                # "response_format": { "type": "json_object" }
            }
            response = self.model.call(model_config)
            content = response.choices[0]["message"]["content"]
            return content.strip().lower()
        
        data = self.data
        llm_evaluation_scores = []
        for _, row in tqdm(data.iterrows(), total=len(data)):
            scores = {}
            claim = row['claim']
            sub_claims = ast.literal_eval(row['sub_claims'])

            for m in self.claim_level_metrics:
                scores[m] = evaluate(claim, sub_claims, self.metrics[m], COLLECTIVE_SUB_CLAIM_EVALUATION)

            for m in self.subclaim_level_metrics:
                score = 0
                fine_grained_scores = []
                prompt_template = ATOMICITY_EVALUATION if m == "atomicity" else INDIVIDUAL_SUB_CLAIM_EVALUATION
                for sub_claim in sub_claims:
                    sub_claim_score = evaluate(claim, sub_claim, self.metrics[m], prompt_template)
                    fine_grained_scores.append(sub_claim_score)
                    if m == "atomicity":
                        score += 3 if sub_claim_score == "atomic" else 2 if sub_claim_score == "non-atomic-1" else 1
                    else:
                        score += 3 if sub_claim_score == "high" else 2 if sub_claim_score == "medium" else 1
                try:
                    scores[m] = score/len(sub_claims)
                    scores['{}_fine_grained'.format(m)] = fine_grained_scores
                except:
                    scores[m] = 0
            llm_evaluation_scores.append(scores)

        data['llm_evaluation_scores'] = llm_evaluation_scores
        data.to_csv(self.output_file, index=False)

def main():
    sub_claim_evaluator = SubClaimEvaluator()
    sub_claim_evaluator.set_data('data/sub_claims.csv') # set data
    sub_claim_evaluator.set_output_file('data/llm_evaluation.csv') # set output file
    sub_claim_evaluator.evaluate_sub_claims()

if __name__ == '__main__':
    if not MODEL_NAME:
        raise Exception("MODEL_NAME not set. Please set MODEL_NAME in config.py")
    main()