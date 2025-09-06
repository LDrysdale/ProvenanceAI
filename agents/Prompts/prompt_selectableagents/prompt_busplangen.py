businessplan_generator_prompt = """

Given the following business idea, create a well-structured lean business plan.
Include these sections (with headings):

1. Problem  
2. Solution  
3. Potential Target Audiences  
4. Revenue Model  
5. Distribution Strategy  
6. Competitive Advantage  
7. MVP Plan  
8. Next Steps (actionable tasks for this week)

For each section, provide concise and clear content (2-4 sentences each) that 
captures the essence of the idea and outlines a practical approach to implementation.

After the business plan, include a section titled:
"🧠 Questions for You"
List 3–5 clarifying, reflective questions that the user should consider to improve or refine their idea.

Make the tone friendly but professional.

Business Idea:
if no idea provided, respond with "No idea provided. Please provide a business idea and 
make sure the business plan generator tool is selected."


"""