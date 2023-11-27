from langchain.agents import (
    AgentOutputParser,
)
from langchain.prompts import BaseChatPromptTemplate
from langchain.tools import BaseTool
from langchain import SQLDatabase
from langchain.schema import AgentAction, AgentFinish, SystemMessage
from typing import List, Union
import re


# Set up a prompt template
class CustomPromptTemplate(BaseChatPromptTemplate):
    # The template to use
    template: str
    # The list of tools available
    tools: List[BaseTool]

    def format_messages(self, **kwargs) -> str:
        # Get the intermediate steps (AgentAction, Observation tuples)
        # Format them in a particular way
        history_text = ""

        if "history" in kwargs:
            history_messages = kwargs.pop("history")
            for history_message in history_messages:
                history_text += f"{history_message.type}: {history_message.content}\n"
            kwargs["history"] = history_text
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "
        # Set the agent_scratchpad variable to that value
        kwargs["agent_scratchpad"] = thoughts
        # Create a tools variable from the list of tools provided
        kwargs["tools"] = "\n\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        # Create a list of tool names for the tools provided
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])
        formatted = self.template.format(**kwargs)
        return [SystemMessage(content=formatted)]


class CustomOutputParser(AgentOutputParser):

    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        # Check if agent should finish
            # if "Observation:" in llm_output:
                # observation_text = llm_output.split("Observation:")[-1].strip().split("Final Answer")[0]
        if "Final Answer:" in llm_output:
            final_answer_text = llm_output.split("Final Answer:")[-1].strip() 
            output_name_regex = "(<output_name>)\w+(</output_name>)"
            options_regex = "(<list>).+(</list>)"
            output_name_match = re.search(output_name_regex, final_answer_text, re.DOTALL)
            options_match = re.search(options_regex, final_answer_text, re.DOTALL)
            
            if output_name_match:
                output_first_match = output_name_match.group(0)
                output_table_name = output_first_match.split("<output_name>")[1].split("</output_name>")[0]
                # final_answer_text = final_answer_text.replace(output_first_match, '')
            else:
                output_table_name = None
                
            if options_match:
                options_first_match = options_match.group(0)
                options_text = options_first_match.split("<list>")[1].split("</list>")[0]
                options = options_text.split(",")
                # final_answer_text = final_answer_text.replace(options_first_match, '')
            else:
                options = []
            
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={
                    "output": final_answer_text, 
                    "output_table_name": output_table_name,
                    "options_text": options
                },
                log=llm_output,
            )
        
        # Parse out the action and action input
        regex = r"Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            raise ValueError(f"Could not parse LLM output: `{llm_output}`")
        action = match.group(1).strip()
        action_input = match.group(2)
        print(action_input, " action input")
        # Return the action and action input
        return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)
    

class CustomSQLDatabase(SQLDatabase):
    def run(
        self,
        command: str,
        fetch = "all",
    ) -> str:
        """Execute a SQL command and return a string representing the results.

        If the statement returns rows, a string of the results is returned.
        If the statement returns no rows, an empty string is returned.
        """
        result = self._execute(command, fetch)
        # Convert columns values to string to avoid issues with sqlalchemy
        # truncating text
        from collections import defaultdict
        values = defaultdict(list)
        for r in result:
            for key, value in r.items():
                values[key].append(value)
        values_dict = dict(values)
        for x in [list, "list"]:
            if x in values_dict.keys():
                values_dict.pop(x)

        if not values_dict:
            return ""
        else:
            return "DF: " + str(values_dict)