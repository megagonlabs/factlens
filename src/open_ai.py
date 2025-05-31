import os

import openai


class OpenAI:
    def __init__(self, openai_api_key, openai_organization=""):
        openai.api_key = openai_api_key
        if openai_organization:
            openai.organization = openai_organization

    def call(self, model_config):
        response = openai.ChatCompletion.create(
            **model_config
        )  
        return response
