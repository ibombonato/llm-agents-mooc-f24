#%%
from typing import Dict, List
from autogen import ConversableAgent
import sys
import os
import math
import random
from dotenv import load_dotenv
import pandas as pd
import re

load_dotenv(override=True)


def clean_string(input_string):
    # Use regular expression to remove non-alphanumeric characters and whitespace
    cleaned_string = re.sub(r'[^A-Za-z0-9]', '', input_string)
    return cleaned_string

def prep_data():
    
    print('Preping data...')
        # Read the content of the .txt file
    with open('restaurant-data.txt', 'r', encoding='utf-8') as file:
        reviews = file.readlines()

    # Initialize lists to store restaurant names and reviews
    restaurants = []
    review_texts = []

    # Process each review line
    for line in reviews:
        line = line.strip()  # Trim whitespace
        if '.' in line:
            restaurant, review = line.split('.', 1)  # Split at the first occurrence of '.'
            restaurants.append(clean_string(restaurant.strip()))  # Append trimmed restaurant name
            review_texts.append(review.strip())      # Append trimmed review text

    # Create a DataFrame with the collected data
    df = pd.DataFrame({
        'restaurant': restaurants,
        'review': review_texts
    })
    
    print('Preping finished.')
    
    return df

def score_review(text):
    # Define the keywords for each score
    score_keywords = {
        1: ['awful', 'horrible', 'disgusting'],
        2: ['bad', 'unpleasant', 'offensive'],
        3: ['average', 'uninspiring', 'forgettable'],
        4: ['good', 'enjoyable', 'satisfying'],
        5: ['awesome', 'incredible', 'amazing']
    }

    # Check the text for the presence of each keyword and assign a score accordingly
    for score, keywords in reversed(score_keywords.items()):
        if any(keyword in text.lower() for keyword in keywords):
            return score
    
    return None  # Return None if no keywords are found

def fetch_restaurant_data(restaurant_name: str) -> Dict[str, List[str]]:
    """
    Fetching restaurant reviews. In a real-world scenario, 
    this would connect to an API or database.
    
    Args:
        restaurant_name (str): Name of the restaurant to fetch reviews for
    
    Returns:
        Dict[str, List[str]]: A dictionary with restaurant name and its reviews
    """
    print('Fetching DATA FOR:', restaurant_name)

    df = DATA
    
    filtered_reviews = df[df['restaurant'].str.contains(clean_string(restaurant_name), case=False)]
    
    return {restaurant_name: filtered_reviews['review'].tolist()}


def calculate_food_score(food_reviews: Dict[str, List[str]]) ->  List[int]:
    """
    Based on the food review, determine it's score
    
    Args:
         Dict[str, List[str]]: A dictionary with restaurant name and its reviews
    
    Returns:
        int: The score from 1 to 5
    """
    # Assuming the dictionary has only one restaurant
    #restaurant, reviews = next(iter(food_reviews.items()))
    
    # Calculate the score for each review
    scores = [score_review(review) for review in food_reviews]
    
    return scores

def calculate_service_score(service_reviews: Dict[str, List[str]]) -> List[int]:
    """
    Based on the service review, deternime it's score
    
    Args:
         Dict[str, List[str]]: A dictionary with restaurant name and its reviews
    
    Returns:
        int: The score from 1 to 5
    """
    # Assuming the dictionary has only one restaurant
    #restaurant, reviews = next(iter(service_reviews.items()))
    
    # Calculate the score for each review
    scores = [score_review(review) for review in service_reviews]
    
    return scores

def calculate_overall_score(restaurant_name: str, food_scores: List[int], service_scores: List[int]) -> Dict[str, float]:
    """
    Calculates a weighted geometric mean score for a restaurant given a list o food scores and service scores.
    
    Args:
        restaurant_name (str): Name of the restaurant
        food_scores (List[int]): List of food quality scores (1-5)
        service_scores (List[int]): List of customer service scores (1-5)
    
    Returns:
        Dict[str, float]: A dictionary with restaurant name and its overall score
    """
    if len(food_scores) != len(service_scores):
        raise ValueError("Food and service score lists must be of equal length")
    
    # Ensure scores are within valid range
    food_scores = [max(1, min(5, score)) for score in food_scores]
    service_scores = [max(1, min(5, score)) for score in service_scores]
    
    n = len(food_scores)
    
    # Calculate geometric mean with custom weighting
    weighted_scores = [
        math.sqrt((food_score**2 * customer_service_score)) * (1 / (n * math.sqrt(125))) * 10 
        for food_score, customer_service_score in zip(food_scores, service_scores)
    ]
    
    overall_score = sum(weighted_scores)
    
    # Ensure at least 3 decimal places
    return {restaurant_name: round(overall_score, 1)}

def get_data_fetch_agent_prompt(restaurant_query: str) -> str:
    """
    Generates a prompt for the data fetch agent to guide review collection.
    
    Args:
        restaurant_query (str): The restaurant to fetch reviews for
    
    Returns:
        str: A detailed prompt for the agent
    """
    return f"""
    You are a data fetch agent tasked with collecting restaurant reviews for {restaurant_query}.

    Your objectives are to:
    0. Extract the restaurant name
    1. Fetching reviews for the specified restaurant
    2. Dont make any assumptions, just return the reviews.    
    """

def main(user_query: str):
    """
    Main function to set up and run the restaurant review analysis system.
    
    Args:
        user_query (str): The restaurant to analyze
    """
    # Entrypoint agent system message
    entrypoint_agent_system_message = """
    You are a supervisor agent for a restaurant review analysis system and you should coordinate the process of analyse their historical data and provide the score of it.
    Your task is to, given a user query about a restaurant:
    1. Fetch the reviews for the restaurant.
    2. Return all reviews for the selected restaurant
    3. Score each of the reviews for the food and the service
    4. Use food and service review score, to get the overall score of the restaurant
    5. Return the overall score off the restaurant
    6. Reply with the restaurant and the score rounded to 3 decimal case when you are done.
    Example: Los Pollos: 9.900
    """

    # LLM configuration (using GPT-4o-mini)
    llm_config = {
        "config_list": [
            {
                "model": "gpt-4o-mini", 
                "api_key": os.environ.get("OPENAI_API_KEY")
            }
        ]
    }

    # Entrypoint agent
    entrypoint_agent = ConversableAgent(
        "entrypoint_agent", 
        system_message=entrypoint_agent_system_message, 
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

       
    #DATA AGENT
    data_fetch_agent = ConversableAgent(
        "data_fetch_agent",
        system_message=get_data_fetch_agent_prompt(user_query),
        llm_config=llm_config,
        human_input_mode="NEVER",
    )
    
    data_fetch_agent.register_for_llm(
        name="fetch_restaurant_data", 
        description="Fetches the reviews for a specific restaurant."
    )(fetch_restaurant_data)
    
       
    entrypoint_agent.register_for_execution(
        name="fetch_restaurant_data"
    )(fetch_restaurant_data)
    
    #ANALYST AGENT
    analysis_agent = ConversableAgent(
        "analysis_agent",
        system_message="""
        You are an analysis agent responsible for:
        1. Break the reviews into `food` and `service` part for each review.
        1.1. Each review has keyword adjectives that correspond to the food and the service.
        1.2. Valid keyword adjectives are:
            -Score: 1, adjectives: awful horrible disgusting.
            -Score: 2, adjectives: bad unpleasant offensive.
            -Score: 3, adjectives: average uninspiring forgettable.
            -Score: 4, adjectives: good enjoyable satisfying.
            -Score: 5, adjectives: awesome incredible amazing.
        1.3. Extract only one off the valid keyword adjectives for each review for the `food` and the `service` splitted by a space ` `.
        - Example: The food at McDonald's was average and uninspiring, but the customer service was unpleasant. The uninspiring menu options were served quickly, but the staff seemed disinterested and unhelpful.
        - `food`: average
        - `service`: unpleasant
        2. Make sure that each review have one food part and one service part.
        2.1. Score each review with his own adjectives
        2.2. Review every score and make sure the grade is right
        3. Use each `food` entry to calculate the food score using the extracted adjetive for the review
        3.1. Use each `service` entry to calculate the service score using the extracted adjetive for the review
        4. Dont make any assumptions. 
        5. NEVER EVER calculate the overall or average score, just each score each one.
        5.1. If you made any error, you will be fired. So, review you analysis before give the results.
        6. If you have 30 reviews, you should return a list with 30 food and 30 service scores.
        7. Return a list with the all the individual food score and all service score.
        """,
        llm_config=llm_config,
        #is_termination_msg=lambda msg: "TERMINATE" in msg["content"],
        human_input_mode="NEVER",
    )
    
    analysis_agent.register_for_llm(
        name="calculate_food_score", 
        description="Calculate the score for the food segment part of the text for each review."
    )(calculate_food_score)
    
    entrypoint_agent.register_for_execution(
        name="calculate_food_score"
    )(calculate_food_score)
    
    
    analysis_agent.register_for_llm(
        name="calculate_service_score", 
        description="Calculate the score for the service segment part of the text for each review."
    )(calculate_service_score)
    
    entrypoint_agent.register_for_execution(
        name="calculate_service_score"
    )(calculate_service_score)
    
    
    #SCORER AGENT
    scorer_agent = ConversableAgent(
        "scorer_agent",
        system_message="""
        You are an scorer agent responsible for calculate the overall score of a restaurant based on a list of scores of food and service scores, using only the value that you received to calculate and return the overall score.
        Dont make any assumptions about the score based on the reviews, use only the received scores.
        For the sake of knowledge, here is the score for each adjective:
            - awful horrible disgusting = 1
            - bad unpleasant offensive = 2
            - average uninspiring forgettable = 3
            - good enjoyable satisfying = 4
            - awesome incredible amazing = 5
        Reply with TERMINATE the restaurant name and the score when you are sure that you are done.
        """,
        llm_config=llm_config,
        is_termination_msg=lambda msg: "TERMINATE" in msg["content"],
        max_consecutive_auto_reply=1,
        human_input_mode="NEVER",
    )
    
    scorer_agent.register_for_llm(
        name="calculate_overall_score", 
        description="Calculate the overall score of the restaurant, based on the list of food and service scores."
    )(calculate_overall_score)
    
    entrypoint_agent.register_for_execution(
        name="calculate_overall_score"
    )(calculate_overall_score)

    # Initiate conversation
    result = entrypoint_agent.initiate_chats([
        {
            "recipient": data_fetch_agent,
            "message": f"Fetch reviews for {user_query}",
            "max_turns": 2,
            "silent": False,
            "summary_method": "last_msg"
        },
        {
            "recipient": analysis_agent,
            "message": "Break the restaurant reviews into food reviews and service reviews and provide a food and service score for each review. Give me a list with each score for the food and the service. You dont need to calculate the overall score.",
            "max_turns": 3
        },
        {
            "recipient": scorer_agent,
            "message": "Analyze the collected review scores for food and service and provide the overall score for the restaurant",
            "max_turns": 3
        }
    ])

    #print("RESULT: ", result)
    #return result

DATA = prep_data()

#%%
# Main execution block
if __name__ == "__main__":
    assert len(sys.argv) > 1, "Please ensure you include a query for some restaurant when executing main."
    main(sys.argv[1])
# %%
