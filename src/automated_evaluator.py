import os
import pandas as pd
import ast
import json
from src.prompts import ENTITY_EXTRACTOR_PROMPT
from src.open_ai import OpenAI
import jaro
import itertools
from bert_score import BERTScorer
import warnings
from tqdm import tqdm
warnings.filterwarnings("ignore")

class AutomatedEvaluator():
    def __init__(self):
        self.model = OpenAI(os.environ['OPENAI_API_KEY'], os.environ['OPENAI_ORGANIZATION'])
        self.scorer = BERTScorer(model_type="bert-base-uncased") 

    def set_data(self, path):
        self.data = pd.read_csv(path)

    def set_output_file(self, path):
        self.output_file = path


    def get_entities(self, claim, sub_claims):
        '''
        Get entities (subjects, objects) for a claim/sub-claim
        '''
        def get_entities_helper(c):
            '''
            Extract list of subjects and objects from a claim using LLM
            '''
            user_prompt = ENTITY_EXTRACTOR_PROMPT.format(claim=c)
            model_config = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": "Your answer should be strictly be in form of a dictionary with keys: subjects and objects"
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                "temperature": 0,
                "response_format": {"type": "json_object"}
            }
            response = self.model.call(model_config)
            content = response.choices[0]["message"]["content"]
            content = json.loads(content)
            return content
        entities = {}
        entities[claim] = get_entities_helper(claim)
        for sub_claim in sub_claims:
            entities[sub_claim] = get_entities_helper(sub_claim)
        return entities
        
    def evaluate_sub_claims(self):
        claim_entities = []
        sub_claim_entities = []
        automated_scores = []
        data = self.data

        for _, row in tqdm(data.iterrows(), total=len(data)):
            claim = row['claim']
            sub_claims = ast.literal_eval(row['sub_claims'])

            automated_score, claim_entity, sub_claim_entity = self.evaluate(
                claim=claim, sub_claims=sub_claims
            )
            automated_scores.append(automated_score)
            claim_entities.append(claim_entity)
            sub_claim_entities.append(sub_claim_entity)
        
        data['automated_scores'] = automated_scores
        data['claim_entities'] = claim_entities
        data['sub_claim_entities'] = sub_claim_entities
        data.to_csv(self.output_file, index=False)

    def entity_match(self, x, y):
        '''
        Perform fuzzy matching to check if two entities are similar
        '''
        a = x.lower().strip()
        b = y.lower().strip()
        return jaro.jaro_winkler_metric(a, b)
    
    def calculate_atomicity(self, s_i, o_i):
        '''
        Calculate atomicity based on number of subjects and objects in the claim. 
        '''
        if len(s_i) == 1 and len(o_i) == 1:
            return "atomic"
        elif len(s_i) == 1 and len(o_i) > 1:
            return "non-atomic-1"
        else: 
            return "non-atomic-2"

    def calculate_fabrication(self, S, O, s_i, o_i):
        '''
        Calculate fabrication based on subjects and objects that appear in the sub claim 
        i.e. s_i and o_i but not in the list of subjects & objects in the original claim S and O
        '''
        num_fabrications = 0
        E = S+O
        for s in s_i:
            s_exists = False
            for e in E:
                if self.entity_match(s, e) > 0.75: #threshold
                    s_exists = True
                    break
            if s_exists == False:
                num_fabrications += 1
        
        for o in o_i:
            o_exists = False
            for e in E:
                if self.entity_match(o, e) > 0.75: #threshold
                    o_exists = True
                    break
            if o_exists == False:
                num_fabrications += 1
        
        if num_fabrications <= 0.25*(len(S) + len(O)):
            return "low"
        elif num_fabrications <= 0.75*(len(S) + len(O)):
            return "medium"
        else:
            return "high"
    
    def calculate_coverage(self, S, O, sub_claims, entities):
        '''
        Check if the union of entities from the sub-claims i.e. Union(s_i) and Union(o_i) 
        matches with the union of entities from the original claim i.e. S and O
        '''
        e = []
        for sub_claim in sub_claims:
            s_i = entities[sub_claim]["subjects"]
            e.extend(s_i)
            o_i = entities[sub_claim]["objects"]
            e.extend(o_i)

        e = list(set(e))
        E = S+O
        non_coverage = 0
        for e_i in E:
            is_covered = False
            for e_j in e:
                if self.entity_match(e_i, e_j) > 0.6: # threshold
                    is_covered = True
                    break
            if is_covered == False:
                non_coverage += 1
        
        if non_coverage <= 0.25*(len(S) + len(O)):
            return "high"
        elif non_coverage <= 0.75*(len(S) + len(O)):
            return "medium"
        else:
            return "low"
        
    def calculate_redundancy(self, S, O, sub_claims, entities):
        '''
        Check if there exists a pairing of sub-claims s_i, s_j which have a high BERT Score. 
        If so, it is likely the sub-claims are redundant.
        '''
        pairings = list(itertools.combinations(sub_claims, 2))
        F1_scores = [self.scorer.score([a], [b])[2].item() for a, b in pairings]

        num_redundant = 0
        for f1 in F1_scores:
            if f1 > 0.85:
                num_redundant += 1
        
        if num_redundant <= 0.25*len(sub_claims):
            return "low"
        elif num_redundant <= 0.75*len(sub_claims):
            return "medium"
        else:
            return "high"

    def compound_atomicity(self, atomicity):
        '''
        Average atomicity for an instance
        '''
        if len(atomicity) == 0:
            return 1
        score = 0
        for a in atomicity:
            score += 3 if a == "atomic" else 2 if a == "non-atomic-1" else 1
        return score/len(atomicity)

    def compound_metric(self, metric):
        '''
        Average metric score for an instance
        '''
        if len(metric) == 0:
            return 1
        score = 0
        for a in metric:
            score += 1 if a == "low" else 2 if a == "medium" else 3
        return score/len(metric)

    def evaluate(self, claim, sub_claims):
        entities = self.get_entities(claim, sub_claims)
        claim_entity = {}
        sub_claim_entity = []

        S = entities[claim]["subjects"]
        O = entities[claim]["objects"]
        claim_entity["subjects"] = S
        claim_entity["objects"] = O

        atomicity_fine_grained = []
        inflation_fine_grained = []

        for sub_claim in sub_claims:
            s_i = entities[sub_claim]["subjects"]
            o_i = entities[sub_claim]["objects"]
            sub_claim_entity.append({
                "subjects": s_i,
                "objects": o_i 
            })
            atomicity_fine_grained.append(self.calculate_atomicity(s_i, o_i))
            inflation_fine_grained.append(self.calculate_fabrication(S, O, s_i, o_i))
            
        coverage = self.calculate_coverage(S, O, sub_claims, entities)
        redundancy = self.calculate_redundancy(S, O, sub_claims, entities)

        return {
            "atomicity": self.compound_atomicity(atomicity_fine_grained),
            "atomicity_fine_grained": atomicity_fine_grained,
            "fabrication": self.compound_metric(inflation_fine_grained),
            "fabrication_fine_grained": inflation_fine_grained,
            "coverage": coverage,
            "redundancy": redundancy
        }, claim_entity, sub_claim_entity

def main():
    sub_claim_evaluator = AutomatedEvaluator()
    sub_claim_evaluator.set_data('data/sub_claims.csv') # set data
    sub_claim_evaluator.set_output_file('data/automated_evaluation.csv') # set output file
    sub_claim_evaluator.evaluate_sub_claims()

if __name__ == '__main__':
    main()