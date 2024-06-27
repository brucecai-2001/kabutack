PLAN = """
## User Request
{user_request}

**Tools Available**:
{tools_desc}

**Instructions**:
1. Based on the user request and tools you have available, write a plan to achieve the user request.
2. Go over the users request step by step and ensure each step is represented as a clear subtask in your plan.

Output a list of jsons in the following format
```json
{{
    "plan": 
        [
            {{
                "instructions": str # what you should do in this task associated with a tool
            }}
        ]
}}
```
"""


CODE = """
**Role**: You are a software programmer.

**Task**: As a programmer, you are required to complete the function. Use a Chain-of-Thought approach to break down the problem, create pseudocode, and then write the code in Python language. Ensure that your code is efficient, readable, and well-commented. Return the requested information from the function you create. Call the function based on the query.

**User Request and Plan**:
{user_request}

**Documentation**:
This is the documentation for the functions you have access to. You may call any of these functions to help you complete the task.

{docs}

**Instructions**:
1. **Understand and Clarify**: Make sure you understand the task.
2. **Algorithm/Method Selection**: Decide on the most efficient way.
3. **Pseudocode Creation**: Write down the steps you will follow in pseudocode.
4. **Code Generation**: Translate your pseudocode into executable Python code. Ensure you use correct arguments, remember coordinates are always returned normalized. All images are in RGB format, red is (255, 0, 0) and blue is (0, 0, 255).
5. **Execution**: call the generated function in the end and print a message indicates the task is done with result if any, be care with the resuit unit.


**Input Code Snippet**:
```python
# Your code here
```
"""