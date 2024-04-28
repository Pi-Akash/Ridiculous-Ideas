import streamlit as st
import os
import requests as r
import json
from typing import Generator
from groq import Groq

def read_groq_key():
    with open("groq_api_key.json", "r") as json_file:
        key = json.load(json_file)
    return key

def perform_request():
    """
    Function sends to request to the free API to get a new idea.
    """
    response = r.get("https://itsthisforthat.com/api.php?text")
    st.session_state.idea = response.text
    return response.text

def add_to_chat_history(message, user = True):
    if user == True:
        st.session_state.chat_history.append({"role" : "user", "content" : message})
    else:
        st.session_state.chat_history.append({"role" : "assistant", "content" : message})

def prompt_message_to_screen(message, user = True):
    # prompt the message to screen
    if user and message != None:
        with st.chat_message(name = "user", avatar = "😃"):
            st.markdown(message)
            add_to_chat_history(message = message, user = True)
    else:
        with st.chat_message(name = "assistant", avatar = "🤖"):
            response_generator = generate_response(message)
            full_response = st.write_stream(response_generator)
            add_to_chat_history(full_response, user = False)
            
def generate_response(chat_completeion) -> Generator[str, None, None]:
    #print(chat_completeion)
    for chunk in chat_completeion:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
    
def initiate_chat_sequence(client, message, first_message = True):
    # call the function to add conversation to history
    if first_message:
        first_message = "Hey there! I have this interesting idea: _{}_, that I would like to discuss with you.".format(st.session_state.idea)
        add_to_chat_history(message = first_message)
        # now call function to prompt message to screen    
        #prompt_message_to_screen(message = first_message, user = True)
    else:
        add_to_chat_history(message = message)
        prompt_message_to_screen(message = message, user = True)
        
    # now we will try to get response from groq
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {
                    "role": m["role"],
                    "content": m["content"]
                } for m in st.session_state.chat_history
            ],
            temperature=1,
            max_tokens=8192,
            top_p=1,
            stream=True,
            stop=None,
        )
        prompt_message_to_screen(completion, user = False)
    except Exception as e:
        print(e)

def main():
    
    # initialize groq client
    groq_client = Groq(api_key = st.secrets["GROQ_API_KEY"])
    
    # if idea is not at start of the app, then it should be empty.
    if "idea" not in st.session_state:
        st.session_state.idea = ""
        
    # if chat history not in session, then it should be empty
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "user_prompt" not in st.session_state:
        st.session_state.user_prompt = ""
    
    st.set_page_config(
        page_title = "Ridiculous Conversations",
        page_icon = "🤖",
        layout = "wide"
    )
    
    #https://itsthisforthat.com/api.php
    st.header(":grey[Ridiculous Conversations with] 🤖", divider = "orange")
    
    st.sidebar.header("Hi, There!! 👋")
    # Button to generate new ideas
    random_idea_button = st.sidebar.button("Click to generate a random idea")
    
    # if button is clicked
    if random_idea_button:
        # generate a new idea
        perform_request()
        
    # a text input if user wants to change or modify the idea
    user_idea = st.sidebar.text_area(label = "**Continue or Modify the current idea...**", value = st.session_state.idea)
    st.session_state.idea = user_idea
    # a button to get the conversation started
    converse_button = st.sidebar.button("This looks interesting, Lets talk!")
    
    # Download Conversation
    complete_chat_history = str(st.session_state.chat_history)
    st.sidebar.download_button("Download Conversation", type = "primary", data = complete_chat_history, file_name = "chat_history.txt")
        
    # Display chat messages from history on app rerun
    for message in st.session_state.chat_history:
        avatar = '🤖' if message["role"] == "assistant" else '😃'
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])
    
    # if the conversation button clicked initiate chat sequence
    if converse_button and st.session_state.idea:
        initiate_chat_sequence(groq_client, message = "", first_message = True)
    
    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "assistant":
        # text input for further questions
        st.session_state.user_prompt = st.chat_input(placeholder = "Enter your messages here...")
        if st.session_state.user_prompt:
            initiate_chat_sequence(groq_client, message = st.session_state.user_prompt, first_message = False)
        
if __name__ == "__main__":
    main()