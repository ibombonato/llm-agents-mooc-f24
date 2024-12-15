#%%
from typing import Dict, List
from autogen import ConversableAgent
import sys
import os
import math
import random
from dotenv import load_dotenv
import pandas as pd

load_dotenv(override=True)

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
            restaurants.append(restaurant.strip())  # Append trimmed restaurant name
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
    for score, keywords in score_keywords.items():
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
    
    filtered_reviews = df[df['restaurant'].str.contains(restaurant_name, case=False)]
    
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
    restaurant, reviews = next(iter(reviews_dict.items()))
    
    # Calculate the score for each review
    scores = [score_review(review) for review in reviews]
    
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
    restaurant, reviews = next(iter(reviews_dict.items()))
    
    # Calculate the score for each review
    scores = [score_review(review) for review in reviews]
    
    return scores

def calculate_overall_score(restaurant_name: str, food_scores: List[int], customer_service_scores: List[int]) -> Dict[str, float]:
    """
    Calculates a weighted geometric mean score for a restaurant given a list o food scores and service scores.
    
    Args:
        restaurant_name (str): Name of the restaurant
        food_scores (List[int]): List of food quality scores (1-5)
        customer_service_scores (List[int]): List of customer service scores (1-5)
    
    Returns:
        Dict[str, float]: A dictionary with restaurant name and its overall score
    """
    if len(food_scores) != len(customer_service_scores):
        raise ValueError("Food and service score lists must be of equal length")
    
    # Ensure scores are within valid range
    food_scores = [max(1, min(5, score)) for score in food_scores]
    customer_service_scores = [max(1, min(5, score)) for score in customer_service_scores]
    
    n = len(food_scores)
    
    # Calculate geometric mean with custom weighting
    weighted_scores = [
        math.sqrt((food_score**2 * customer_service_score)) * (1 / (n * math.sqrt(125))) * 10 
        for food_score, customer_service_score in zip(food_scores, customer_service_scores)
    ]
    
    overall_score = sum(weighted_scores)
    
    # Ensure at least 3 decimal places
    return {restaurant_name: round(overall_score, 3)}

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
    2. Return the reviews
    
    Here are the reviews:
    
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
        llm_config=llm_config
    )

       
    #DATA AGENT
    data_fetch_agent = ConversableAgent(
        "data_fetch_agent",
        system_message=get_data_fetch_agent_prompt(user_query),
        llm_config=llm_config
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
        1. Break the reviews into `food` and `service` part. 
        - Example: The food at McDonald's was average, but the customer service was unpleasant. The uninspiring menu options were served quickly, but the staff seemed disinterested and unhelpful.
        - `food`: The food at McDonald's was average
        - `service`: but the customer service was unpleasant. The uninspiring menu options were served quickly, but the staff seemed disinterested and unhelpful.
        2. Using the `food` reviews to calculate the food score for each review
        3. Use the `service` reviews to calculate the service score for each review
        """,
        llm_config=llm_config
    )
    
    analysis_agent.register_for_llm(
        name="calculate_food_score", 
        description="Fetches the score for the food segment part of the text for each review."
    )(calculate_food_score)
    
    entrypoint_agent.register_for_execution(
        name="calculate_food_score"
    )(calculate_food_score)
    
    
    analysis_agent.register_for_llm(
        name="calculate_service_score", 
        description="Fetches the score for the service segment part of the text for each review."
    )(calculate_service_score)
    
    entrypoint_agent.register_for_execution(
        name="calculate_service_score"
    )(calculate_service_score)
    
    
    #SCORER AGENT
    scorer_agent = ConversableAgent(
        "scorer_agent",
        system_message="""
        You are an scorer agent responsible for calculate the score of a restaurant.
        Given a list of food and service scores, calculate and return the overall score.
        """,
        llm_config=llm_config
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
            "max_turns": 3,
            "silent": False,
            "summary_method": "last_msg"
        },
        {
            "recipient": analysis_agent,
            "message": "Break the collected reviews into food and service reviews and provide it is score",
            "max_turns": 3
        },
        {
            "recipient": scorer_agent,
            "message": "Analyze the collected reviews and provide the overall score",
            "max_turns": 3
        }
    ])

    return result

DATA = prep_data()

#%%
# Main execution block
if __name__ == "__main__":
    assert len(sys.argv) > 1, "Please ensure you include a query for some restaurant when executing main."
    main(sys.argv[1])
# %%
