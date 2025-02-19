from flask import Flask, jsonify, request, send_from_directory, Response
import random
import os
from flask_cors import CORS
from groq import Groq
from elevenlabs.client import ElevenLabs

app = Flask(__name__, static_url_path='', static_folder='.')
CORS(app)

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", "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"))

# Initialize ElevenLabs client for TTS
tts_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY", "sk_59b54b6936e0db84a49846c56d6475980014ba026ba67d5b"))
VOICE_ID_PRO = os.getenv("VOICE_ID_PRO", "5Q0t7uMcjvnagumLfvZi")
VOICE_ID_CON = os.getenv("VOICE_ID_CON", "9BWtsMINqrJLrRacOk9x")

# Global debate state
debate_state = {
    'topic': "No topic yet",
    'round': 0,
    'debater_a': "",
    'debater_b': "",
    'votes_a': 0,
    'votes_b': 0
}

def generate_argument(topic, stance, round_number, custom_instruction=None):
    """
    Use the Groq API to generate a debate argument with distinct personality styles.
    
    :param topic: The debate topic.
    :param stance: "pro" or "con".
    :param round_number: The current debate round.
    :param custom_instruction: Optional custom instructions for the argument.
    :return: Generated argument as a string.
    """
    if stance.lower() == "pro":
        style_prompt = "Use humor and wit while arguing in favor."
        default_instruction = "Argue in favor of the topic using compelling points."
    else:
        style_prompt = "Use calm, academic reasoning."
        default_instruction = "Argue against the topic using logical evidence."

    instruction = custom_instruction if custom_instruction else default_instruction

    prompt = (
        f"You are a skilled debate assistant with a distinct personality. {style_prompt}\n"
        f"Generate a clear and persuasive {stance.upper()} argument for the debate topic: '{topic}' (Round {round_number}). "
        f"{instruction} Keep the answer concise (around 150 words)."
    )
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert debate assistant."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_completion_tokens=200,
            top_p=1,
            stop=None,
            stream=False,
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return f"[Error generating {stance} argument: {str(e)}]"


def evaluate_argument(argument):
    """ Simulate evaluation by returning a random score between 0 and 100. """
    return random.randint(0, 100)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/start_debate', methods=['POST'])
def start_debate():
    data = request.get_json()
    topic = data.get("topic", "Default Topic")
    
    # Reset debate state
    debate_state['topic'] = topic
    debate_state['round'] = 1
    
    arg_a = generate_argument(topic, "pro", 1)
    arg_b = generate_argument(topic, "con", 1)
    score_a = evaluate_argument(arg_a)
    score_b = evaluate_argument(arg_b)
    
    debate_state['debater_a'] = arg_a
    debate_state['debater_b'] = arg_b
    debate_state['votes_a'] = score_a
    debate_state['votes_b'] = score_b
    
    return jsonify(debate_state)

@app.route('/next_round', methods=['POST'])
def next_round():
    debate_state['round'] += 1
    topic = debate_state['topic']
    
    arg_a = generate_argument(topic, "pro", debate_state['round'])
    arg_b = generate_argument(topic, "con", debate_state['round'])
    score_a = evaluate_argument(arg_a)
    score_b = evaluate_argument(arg_b)
    
    debate_state['debater_a'] = arg_a
    debate_state['debater_b'] = arg_b
    debate_state['votes_a'] = score_a
    debate_state['votes_b'] = score_b
    
    return jsonify(debate_state)

@app.route('/get_state', methods=['GET'])
def get_state():
    return jsonify(debate_state)

@app.route('/speak/<side>', methods=['GET'])
def speak(side):
    """
    Generate speech audio for the given side ('pro' or 'con') using ElevenLabs TTS.
    Returns MP3 audio.
    """
    if side.lower() == "pro":
        text = debate_state.get('debater_a', "No argument available.")
        voice_id = VOICE_ID_PRO
    elif side.lower() == "con":
        text = debate_state.get('debater_b', "No argument available.")
        voice_id = VOICE_ID_CON
    else:
        return jsonify({"error": "Invalid side"}), 400

    try:
        audio_bytes = b""
        audio_stream = tts_client.text_to_speech.convert_as_stream(
            text=text,
            voice_id=voice_id,
            model_id="eleven_multilingual_v2"
        )
        for chunk in audio_stream:
            if isinstance(chunk, bytes):
                audio_bytes += chunk
        return Response(audio_bytes, mimetype="audio/mpeg")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
