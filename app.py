from flask import Flask, jsonify, request, send_from_directory
import random
import os
from flask_cors import CORS
from groq import Groq

app = Flask(__name__, static_url_path='', static_folder='.')
CORS(app)  # Enable CORS for all routes

# Create a Groq client using your API key.
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", "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"))

# Global debate state (for simplicity, using a global dictionary)
debate_state = {
    'topic': "No topic yet",
    'round': 0,
    'debater_a': "",
    'debater_b': "",
    'votes_a': 0,
    'votes_b': 0
}

def generate_argument(topic, stance, round_number):
    """
    Use the Groq API (via the Groq Python client) to generate a debate argument.

    :param topic: The debate topic.
    :param stance: "pro" or "con".
    :param round_number: Current round number.
    :return: Generated argument as a string.
    """

    # Distinct personalities for each stance
    if stance.lower() == "pro":
        # Example: a humorous, energetic style
        style_prompt = (
            "You have a humorous, energetic style. Use casual language and witty lines "
            "to present your points in an engaging way."
        )
        additional_instruction = (
            "Argue that expensive water does taste different. Emphasize factors like unique mineral content, "
            "premium purification processes, and an enhanced sensory experience that justifies the higher cost."
        )
    else:  # con
        # Example: a calm, academic style
        style_prompt = (
            "You have a calm, academic style. Use formal language, logical structure, and well-researched points "
            "to present your argument."
        )
        additional_instruction = (
            "Argue that expensive water does not taste different. Emphasize that blind taste tests show no significant "
            "difference and that any perceived difference is due to marketing and psychological effects."
        )

    # Combine everything into one prompt
    prompt = (
        f"You are a skilled debate assistant with a distinct personality. {style_prompt}\n"
        f"Generate a clear and persuasive {stance.upper()} argument for the debate topic: '{topic}'. "
        f"Include references to round {round_number} if it adds context. {additional_instruction} "
        "Keep the answer concise (around 150 words)."
    )

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert debate assistant."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",  # Use the appropriate model as per Groq's documentation.
            temperature=0.7,
            max_completion_tokens=200,
            top_p=1,
            stop=None,
            stream=False,
        )
        argument_text = chat_completion.choices[0].message.content.strip()
    except Exception as e:
        argument_text = f"[Error generating {stance} argument: {str(e)}]"
    
    return argument_text



@app.route('/')
def index():
    # Serve the index.html file from the current directory.
    return send_from_directory('.', 'index.html')

@app.route('/start_debate', methods=['POST'])
def start_debate():
    """
    Start a new debate.
    Expects JSON data with the debate topic:
      { "topic": "Your debate topic" }
    """
    data = request.get_json()
    topic = data.get("topic", "Default Topic")
    
    debate_state['topic'] = topic
    debate_state['round'] = 1
    
    # Generate initial debate arguments using Groq API
    debate_state['debater_a'] = generate_argument(topic, "pro", debate_state['round'])
    debate_state['debater_b'] = generate_argument(topic, "con", debate_state['round'])
    
    # Simulate initial audience votes
    debate_state['votes_a'] = random.randint(0, 100)
    debate_state['votes_b'] = random.randint(0, 100)
    
    return jsonify(debate_state)

@app.route('/next_round', methods=['POST'])
def next_round():
    """
    Proceed to the next debate round.
    Updates the debate state with new AI-generated arguments and random audience votes.
    """
    debate_state['round'] += 1
    topic = debate_state['topic']
    
    # Generate new arguments for the next round
    debate_state['debater_a'] = generate_argument(topic, "pro", debate_state['round'])
    debate_state['debater_b'] = generate_argument(topic, "con", debate_state['round'])
    
    # Simulate updated audience votes for this round
    debate_state['votes_a'] = random.randint(0, 100)
    debate_state['votes_b'] = random.randint(0, 100)
    
    return jsonify(debate_state)

@app.route('/get_state', methods=['GET'])
def get_state():
    """
    Return the current debate state as JSON.
    This endpoint is used by the frontend to update the UI.
    """
    return jsonify(debate_state)

if __name__ == '__main__':
    # Run the Flask server on localhost:5000
    app.run(debug=True)
