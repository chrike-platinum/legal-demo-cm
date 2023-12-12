import streamlit as st
from llama_index import VectorStoreIndex, ServiceContext, Document
from llama_index.llms import OpenAI
import openai
from llama_index.tools.function_tool import FunctionTool
from llama_hub.tools.bing_search import BingSearchToolSpec
from llama_hub.tools.tavily_research import TavilyToolSpec
from llama_index.llms import OpenAI,AzureOpenAI

import os
OPENAI_API_KEY= st.secrets['openai-api-key']
os.environ['OPENAI_API_KEY']=OPENAI_API_KEY
from llama_index.agent import OpenAIAssistantAgent

tavily_tool = TavilyToolSpec(
    api_key=st.secrets['tavily-api-key']
)


def retrieve_relevant_law(case_context):
    """
    This function returns the relevant law articles given a case context
    :param case_context: context of the legal case
    :type case_context: str
    :return: relevant law(articles)
    :rtype: str
    """
    #gpt_llm_law = OpenAI(temperature=0, model="gpt-3.5-turbo-1106")
    gpt_llm_law = AzureOpenAI(
    temperature=0.1,
    model="gpt-35-turbo",
    deployment_name=st.secrets["azure-deployment-name"],
    api_key=st.secrets['azure-api-key'],
    azure_endpoint=st.secrets['azure_endpoint'],
    api_version="2023-08-01-preview",
    )
    
    return gpt_llm_law.complete("Given the case below provide all relevant EU law articles on the matter. Be specific and and quote the law verbatim. case: {}".format(case_context))

retrieve_relevant_law_tool= FunctionTool.from_defaults(fn=retrieve_relevant_law,description='This tool retrieves the relevant law articles based on the case context')

tools=tavily_tool.to_tool_list()+[retrieve_relevant_law_tool] #bing_tool_spec.to_tool_list()+

system_template="""you are a legal system specialized in trademark and patent cases. You will get a case from the lawyer you are helping. 
                    Never compress information between runs. Provide ALL information to the user.
                    You will first find the relevant law articles on the matter by using the retrieve_relevant_law tool.
                    Next, You must search for additional caselaw or doctrine for the case using the search tool. This means that you need to search for recent similar legal cases.
                    Make sure you generalize the legal concepts for your and specify in your query ALWAYS that you are looking for caselaw or doctrine.
                    Next, Think and analyse the additional info.
                    After all this you will create a final answer based on all that input together with your knowledge of legal articles and applicable law. 
                    Structure your answer as follows:
                    Research:
                    -Relevant law articles and quote the law articles verbatim
                    -Relevant recent caselaw or doctrine (include all urls of found information)
                    -List all arguments to support this case
                    Finally:
                    Let's say I'm the lawyer of this case, how can I build my case? Make a very detailed argumentation.
                    
                    ALWAYS INCLUDE ALL SOURCES AND/URLS of all found information.
                    KEEP IN MIND: there are no copyright restrictions on law or legal information.
                    Make your answer very elaborate, very specific and always give all your used sources and law articles.
                    """

agentAssistant = OpenAIAssistantAgent.from_new(
    name="legal assistant",
    instructions=system_template,
    tools=tools,
    verbose=True
    #openai_tools=[{"type": "code_interpreter"}],
    #instructions_prefix="Please address the user as Jane Doe. The user has a premium account.",
)



st.set_page_config(page_title="Prepare your legal case", page_icon="🦙", layout="centered", initial_sidebar_state="auto", menu_items=None)
st.image("logo.png")
st.title("AI case assistant")


         
if "messages" not in st.session_state.keys(): # Initialize the chat messages history
    st.session_state.messages = [
        {"role": "assistant", "content": "Please present your case to me"}
    ]

print(st.session_state.keys())
if "agentAssistant" not in st.session_state.keys(): # Initialize the chat engine
        print('agent created')
        st.session_state.agentAssistant = agentAssistant

with st.expander("System instructions:"):
    system_prompt=st.text_area("System Message",value=system_template,key="system_prompt",height=600)


if prompt := st.chat_input("Your case description",): # Prompt for user input and save to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages: # Display the prior chat messages
    with st.chat_message(message["role"]):
        st.write(message["content"])

# If last message is not from assistant, generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            st.session_state.agentAssistant.assistant.instructions=system_prompt
            st.session_state.agentAssistant._instructions_prefix=system_prompt

            response = st.session_state.agentAssistant.chat(prompt)
            st.write(response.response)
            message = {"role": "assistant", "content": response.response}
            st.session_state.messages.append(message) # Add response to message history
