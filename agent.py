from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
import os 
from dotenv import load_dotenv
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from pydantic import BaseModel
from tools import collect_flight_info,collect_passenger_info,get_airport_code, search_flights
from datetime import date
from system_prompt import system_message

today = date.today()

class DomesticFlightSearch(BaseModel):
    origin_airport: str
    destination_airport: str
    departure_date: str  # YYYY-MM-DD
    return_date: str = None  # optional
    passengers: int
    cabin_class: str = "ECONOMY"
    direct_only: bool = False
    include_checked_bag: bool = False
    include_carry_on: bool = True

#loading llm
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing in the .env file")


llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY")
)
#end of loading llm


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            system_message
          ,
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{query}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
        # ("assistant", "Output: {output}")  # Guide the agent to produce an output

    ]
)

tools = [collect_flight_info,collect_passenger_info,get_airport_code, search_flights]

memory = ConversationBufferMemory(
    memory_key="chat_history", return_messages=True
)

agent = create_tool_calling_agent(
    llm=llm,
    prompt=prompt,
    tools=tools,
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True,
    # output_key="output"
)

async def run_agent(query):
    print(f"Type of query: {type(query)}")  # Should be <class 'str'>
    response = agent_executor.invoke({"query": query,})
    print(response)
    if "output" in response:
        return response["output"]
    else:
        raise ValueError("Agent response does not contain 'output'")    