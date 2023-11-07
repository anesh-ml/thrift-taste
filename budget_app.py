
import os
import streamlit as st
from streamlit_chat import message
from langchain.llms.openai import OpenAI, AzureOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from datetime import datetime
import json
from dotenv import load_dotenv

def configure():
    load_dotenv()
configure()
os.environ['OPENAI_API_KEY']=str(os.getenv('api_key'))
# Create prompt template
def create_prompt_update(llm):
    prompt = """
    Please act as a robust and well-trained intent classifier that can identify "product item", "price", and "quantity". value of "product item" and "price should be in list by default.If all of the values are empty then return None.

    If an item is already present for that month, add "quantity" key and increment it by one.

    If any of the intent is not found, then make it empty string. Return the identified intents as dictionary and price should be integer.

    

    User's query: {question}

    Intent:
    """
    return PromptTemplate(template=prompt, input_variables=['question'])
def create_prompt_retrieve(llm):
    prompt = """
    Please act as an expenditure tracker. You should be able to answer questions related to my expenses and categorize product items accurately when the user asks for expenditure by categories. The user's expenditure for each month will be provided as a JSON object at the end of their query. If the user's query is not related to expenditure retrieval, please return 'None'.
    User's query: {question}

    """
    return PromptTemplate(template=prompt, input_variables=['question'])

def create_prompt_diet(llm):
    prompt = """
    Please serve as my diet coach. Deduce insights into my lifestyle and health condition based on my purchased items. Take into account the quantities when assessing my food choices. Concentrate on food items in the purchased items and assess my diet with the aim of reducing body fat. If the query is unrelated to diet, nutrients, or health, kindly respond with 'None.'

Evaluate the food items in the purchased items, providing constructive criticism and recommendations based on my food consumption.

When requested, furnish the average quantity of the specified nutrient.

It's important to note that my current weight is 200 pounds, and you should also estimate the potential weight change in a month based on my food consumption
    User's query: {question}

    Diet plan:
    """
    return PromptTemplate(template=prompt, input_variables=['question'])

llm=OpenAI(temperature=0)
# Create prompt template
prompt_template_update = create_prompt_update(llm)
prompt_template_retrieve = create_prompt_retrieve(llm)
prompt_template_diet = create_prompt_diet(llm)
# Create LLMChain
llm_chain_update = LLMChain(llm=llm, prompt=prompt_template_update)
llm_chain_retrieve = LLMChain(llm=llm, prompt=prompt_template_retrieve)
llm_chain_diet = LLMChain(llm=llm, prompt=prompt_template_diet)

# Opening JSON file
if not os.path.exists('expense.json'):
    data={'month':{}}
    with open('expense.json', 'w') as f:
        json.dump(data, f)
else:
    f = open('expense.json')
    data = json.load(f)

st.title("ThriftTaste")

def conversation_chat(query):
    query_=query+". JSON object: "+json.dumps(data)
    #print(query)
    question=[{'question':query_}]
    retrieval=llm_chain_retrieve.generate(question)
    question=[{'question':query}]
    intents = llm_chain_update.generate(question)
    is_empty=any(v for k,v in eval(intents.generations[0][0].text.strip()).items())
    #print(retrieval.generations[0][0].text)
    if "None" not in retrieval.generations[0][0].text.strip():
        out=retrieval.generations[0][0].text
    elif is_empty:
        out=intents.generations[0][0].text   
        #print(dict(intents.generations[0][0].text.split('\n')))
        out=eval(intents.generations[0][0].text.strip())
        
        currentMonth = datetime.now().strftime("%B")
        #print(data)
        if currentMonth not in data['month']:
                data['month'][currentMonth]={}
        if not isinstance(out['product_item'],list):
            out['product_item']=[out['product_item']]
            out['quantity']=[out['quantity']]
            out['price']=[out['price']]
       
        for i,prod in enumerate(out['product_item']):
            if prod not in data['month'][currentMonth]:
                
                data['month'][currentMonth][prod]={}
                data['month'][currentMonth][prod]['price']=out['price'][i]
                data['month'][currentMonth][prod]['quantity']=out['quantity'][i]
            else:
                
                data['month'][currentMonth][prod]['price']=data['month'][currentMonth][prod]['price']+out['price'][i]
                data['month'][currentMonth][prod]['quantity']=data['month'][currentMonth][prod]['quantity']+out['quantity'][i]
        with open('expense.json', 'w') as f:
            json.dump(data, f)
    else:
        currentMonth = datetime.now().strftime("%B")
        items=", ".join(list(data['month'][currentMonth].keys()))
        #print("purchased items",items)
        query_=query+ ". Here are my purchased items this month: "+items
        #print(query_)
        question=[{'question':query_}]
        diet_planner=llm_chain_diet.generate(question)
        #print("Diet answer",diet_planner)

        out=diet_planner.generations[0][0].text

    st.session_state['history'].append((query,out))
    return out

if 'history' not in st.session_state:
    st.session_state['history']=[]

if 'generated' not in st.session_state:
    st.session_state['generated'] = ["Hello ! I am ThriftTaste! You can \n**Add your expense to me** \n**Ask questions about your expense** \n**Health check based on your purchased food items**"]

if 'past' not in st.session_state:
    st.session_state['past'] = ["Hey ! 👋"]

#container for the chat history
response_container = st.container()
#container for the user's text input
container = st.container()

with container:
        
    user_input = st.text_input("Query:", placeholder="Ask me (:", key='input')
        
    if user_input:
        output = conversation_chat(user_input)
        
        st.session_state['past'].append(user_input)
        st.session_state['generated'].append(output)

if st.session_state['generated']:
    with response_container:
        for i in range(len(st.session_state['generated'])):
            message(st.session_state["past"][i], is_user=True, key=str(i) + '_user', avatar_style="big-smile")
            message(st.session_state["generated"][i], key=str(i), avatar_style='Robot')



    