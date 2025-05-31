SUB_CLAIM_GENERATOR_PROMPT = '''
We aim to fact-check a textual claim. To make the fact-checking task simpler, we break down a claim into simpler, atomic sub-claims to fact-check as needed. Note that atomic sub-claims refer to unit claims within the original claim, that refer to a single concept that can be independently verified without having to refer to the original claim. Verification of the sub-claims should not require aggregation of facts or multi-hop reasoning over concepts. However, the sub-claim should have all the contextual information preserved from the original claim. 

Your task is to break down a claim into atomic sub-claims for fact checking only if needed. If the original claim itself is a unit claim, do not break it down.

For example:
{demonstrations}

Note how each sub claim contains atomic information to fact check and is brief, yet is contextualized with all the information needed from the original claim.

Now find the sub claims from the following claim.
claim: {claim}
sub_claims: <your output in form of a list> 
'''

DEMONSTRATIONS = [
    '''Claim: Mathias Herrmann acted in eleven movies from 1987 to 2020
Sub-claims: [“Mathias Herrmann acted in eleven movies from 1987 to 2020”]''',
'''Claim: L-arabinose is more common than D-arabinose with most research has been done on L-arabinose operon which is required for the breakdown of the five-carbon sugar L-arabinose in Escherichia coli.
Sub-claims: [“L-arabinose is more common than D-arabinose”, “Most research has been done on L-arabinose operon”,“L-arabinose operon is required for the breakdown of L-arabinose in Escherichia coli”, “L-arabinose is a five-carbon sugar”]''',
    '''Claim: Forest of the Dead was directed by three directors and was written by Steven Moffat.
Sub-claims:  [“Forest of the Dead was directed by three directors”, “Forest of the Dead was written by Steven Moffat”]''',
    '''Claim: Matthew Busche whose full name is Matthew Craig Busche rode for the RadioShack-Nissan from 2012 to 2016.
Sub-claims:  [“Matthew Busche's full name is Matthew Craig Busche”, “Matthew Busche rode for the RadioShack-Nissan from 2012 to 2016””]'''
]

COLLECTIVE_SUB_CLAIM_EVALUATION = '''
A factual claim can be broken down into atomic, yet contextualized sub-claims which makes it easier to fact check.
You will be provided a claim, and all the sub-claims which have been extracted from it. Your job is to evaluate these sub-claims on the following metric:

{metrics}

Your answer should either be \"low\", \"medium\" or \"high\" based on the metric provided. Please be objective and fair in your evaluation.

Claim: {claim}
Sub-Claims: {sub_claims}
'''

INDIVIDUAL_SUB_CLAIM_EVALUATION = '''
A factual claim can be broken down into atomic, yet contextualized sub-claims which makes it easier to fact check.
You will be provided a claim, and one of the sub-claims which have been extracted from it. Your job is to evaluate this sub-claim on the following metric:

{metrics}

Your answer should either be \"low\", \"medium\" or \"high\" based on the metric provided. Please be objective and fair in your evaluation.

Claim: {claim}
Sub-Claim: {sub_claims}
'''

ATOMICITY_EVALUATION = '''
A factual claim can be broken down into atomic, yet contextualized sub-claims which makes it easier to fact check.
You will be provided a claim, and one of the sub-claims which have been extracted from it. Your job is to evaluate this sub-claim on the following metric:

{metrics}

Please be objective and fair in your evaluation. Your response should strictly be a label either \"atomic\", \"non-atomic-1\" or \"non-atomic-2\" based on the instructions provided.

Claim: {claim}
Sub-Claim: {sub_claims}
'''

ENTITY_EXTRACTOR_PROMPT = '''
Given a fact-checking claim, return all the subjects and the objects present in it. 
In order to do this, find all relations present in the claim as (subject, relation, object) tuples. Then list all the subjects and objects.
Claim: {claim}

Your answer should be in form of a dictionary/JSON with keys \"subjects\" and \"objects\"
'''

VERIFIER_PROMPT = '''
Verify if the following claim is true or false based on the context provided.
Claim: {claim}
Context: {context}
'''