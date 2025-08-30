import openai
import wikipedia
import re
import requests

class SerendipityEnginePro:
    def __init__(self, openai_api_key, serpapi_key, model="gpt-4", temperature=0.9, top_p=0.95):
        openai.api_key = openai_api_key
        self.serpapi_key = serpapi_key
        self.model = model
        self.temperature = temperature
        self.top_p = top_p

    def _call_gpt(self, prompt, system_prompt=None):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            top_p=self.top_p
        )
        return response["choices"][0]["message"]["content"].strip()

    def generate_random_concepts(self):
        prompt = (
            "Generate two semantically distant, unexpected, and original concepts from different fields. "
            "They must be clearly named and not obviously related. Output format:\nConcept 1: <...>\nConcept 2: <...>"
        )
        response = self._call_gpt(prompt)
        lines = response.splitlines()
        match1 = re.search(r"Concept 1:\s*(.*)", lines[0])
        match2 = re.search(r"Concept 2:\s*(.*)", lines[1])
        return match1.group(1).strip(), match2.group(1).strip()

    def enrich_with_wikipedia(self, concept):
        try:
            return wikipedia.summary(concept, sentences=2, auto_suggest=True)
        except Exception:
            return None

    def enrich_with_web(self, concept):
        try:
            url = "https://serpapi.com/search.json"
            params = {
                "q": concept,
                "api_key": self.serpapi_key,
                "num": 1
            }
            response = requests.get(url, params=params)
            data = response.json()

            if "organic_results" in data and data["organic_results"]:
                return data["organic_results"][0].get("snippet", None)
            return None
        except Exception:
            return None

    def get_best_context(self, concept):
        wiki_summary = self.enrich_with_wikipedia(concept)
        if wiki_summary:
            return wiki_summary
        web_summary = self.enrich_with_web(concept)
        return web_summary or "No contextual info available."

    def generate_fusion_idea(self, concept1, concept2, context1, context2):
        prompt = (
            f"Combine these two unrelated concepts to create a strange, innovative, or surprisingly useful idea.\n\n"
            f"Concept 1: {concept1}\nContext 1: {context1}\n\n"
            f"Concept 2: {concept2}\nContext 2: {context2}\n\n"
            f"Start with a 'What if...' question, then elaborate creatively."
        )
        return self._call_gpt(prompt, system_prompt="You are a visionary creative assistant.")

    def run(self):
        concept1, concept2 = self.generate_random_concepts()
        context1 = self.get_best_context(concept1)
        context2 = self.get_best_context(concept2)
        idea = self.generate_fusion_idea(concept1, concept2, context1, context2)

        return {
            "concepts": (concept1, concept2),
            "contexts": (context1, context2),
            "idea": idea
        }
