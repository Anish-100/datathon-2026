import ast
from API.Prediction import closest_commerical_zone as ccz
from API.Prediction import melissa_prediction as mp
import API.api as api


# Run this program to begin the whole process.

def run():
    # Get all the important parameters + weights for each
    question = get_query() + PROMPT + PROMPT_2
    query = api.main(prompt=question)

    # Saves results to raw_text
    pairs = parse_query_results(query)
    mp.main(pairs)
    #Reads from raw_text
    ccz.main('API/Prediction/raw_text_2.txt')

def parse_query_results(raw_response):
    """Parse the LLM string response into a list of tuples."""
    print('Query Results')
    print(raw_response)
    pairs = ast.literal_eval(raw_response.strip())
    return pairs

def get_query():
    return str(input("Please enter your business idea along with are some main data points that" \
    " you would like to see. Mentioning demographics and other relevant data will be helpful.:"))

    
PROMPT = """
Based on the business idea proposed, modify these traits where Y is yes N is No.
 This is based in rancho santa margarita, so take that in concern when creating your values.
You will create a a list of 9 tuples, the first of each tuple will be specificed below also with tags of what it should look like.
The second of each tuple will be the weight you think will apply to each tuple out of 100.
The more important these core ideas are to the business idea, the higher weightage they should get out of 100. 
('Y', 0.0),    # dog_owner
('N', 0.0),    # cat_owner
(9, 80.0),     # net_worth
('Y', 50.0),   # cc_user
(2, 20.0),     # vehicle_count
('O', 30.0),   # owner_renter
(3, 15.0),     # household_size
(1, 10.0),     # num_children
('Y', 0.0),    # home_improvement_diy
Ensure no special symbols like %/^&*@!
Return them in this order only.
Return a list of these tuples in Python, and nothing else. 
"""
PROMPT_2 ="""
dog_owner: Compares dog-owner flag ('Y'/'N') against the RSM ZIP code's mode.

cat_owner: Compares cat-owner flag ('Y'/'N') against the RSM ZIP code's mode.

net_worth: Compares net worth code (1-9) against the RSM ZIP code's median code. 1=<$1, 2=$1-4.9k, 3=$5-14.9k, 4=$15-24.9k, 5=$25-49.9k, 6=$50-99.9k, 7=$100-249.9k, 8=$250-499.9k, 9=$500k+

cc_user: Compares credit card user flag ('Y'/'N') against the RSM ZIP code's mode.

vehicle_count: Compares number of registered vehicles per household against the RSM ZIP code's median. RSM is car-dependent; 2-3 vehicles per household is typical.

owner_renter: Compares owner/renter flag ('O'/'R') against the RSM ZIP code's mode. 92688 ~71% owners, 92679 ~91% owners.

household_size: Compares household size (integer count) against the RSM ZIP code's average. 92688 ~2.87, 92679 ~2.99 — both lean family-sized.

num_children: Compares number of children (integer count) against the RSM ZIP code's average. RSM is family-oriented; typical range is 1-2 children per household.

home_improvement_diy: Compares home-improvement DIY flag ('Y'/'N') against the RSM ZIP code's mode.

**Note:** The `main()` function in your provided code does not currently have a docstring.
"""
if __name__ == '__main__':
    run()