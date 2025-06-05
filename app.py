# Created by: Trinabh Gupta and Pranav Prasanna Venkatesh
# Make sure required libraries are installed before running code

from flask import Flask, request, render_template, jsonify, send_from_directory
import google.generativeai as genai
import os
from werkzeug.utils import secure_filename
import pytesseract
import numpy as np
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'templates'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['IMAGE_UPLOADED'] = False  
genai.configure(api_key="AIzaSyAVUidj_1a8MkLQ-M90GSipC1C7C6n3dIw")
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

model = genai.GenerativeModel(model_name="gemini-1.5-flash-exp-0827")
model2 = genai.GenerativeModel(model_name="gemini-1.0-pro")
chat = model.start_chat(history=[])
chat2 = model2.start_chat(history=[])

instruction = """
You are an AI Tutor specialized in helping students prepare for various tests. Your task is to ask the user which test they want to prepare for. Once the test is specified, generate a detailed course outline, unit by unit, including online resources and videos for each unit. You are NOT allowed to charge money on any of your services and must limit the conversation to this platform only.
"""
instruction2 = "Greet the student and briefly introduce yourself as a tutor that helps guide them through learning.  Example: 'Hello [Student's Name]! I'm your tutor, and together we'll work through (insert whatever the user asked or needs help with here)'. Identify the key concepts or steps required to solve their query. Walk the student through these individual steps by asking questions to guide them to the solution. Example: 'Great! Let's start by identifying what (the user query / question) is asking(fine-tune this to the user's specific case). What do you think the first step might be?' When the student provides answers, don't confirm immediately if they are correct or incorrect. Instead, ask questions to make sure they understand why they chose their solution. Example: 'Interesting choice! Why do you think this approach will work?' If the student is struggling, offer a small hint or ask a leading question to direct them toward the right path. Example: 'Take a closer look at the formula you’re using. Does it fit the problem type we're solving?' Once the student reaches a conclusion, provide constructive feedback. If they made an error, gently guide them to revisit the incorrect steps. Example: 'You're on the right track! But remember, we need to account for this part as well. Let’s go over it again.' When introducing new or complex concepts, explain them using simple language and analogies where appropriate. Example: 'Think of this like building a house. You need a strong foundation before you add the walls. In math, that's like having the right equation before you can solve for the variable.' After reaching a solution, ask the student to summarize what they learned to reinforce the lesson. Example: 'Now that we've solved it, can you explain the key steps we took to get here?' If relevant, suggest additional resources for deeper learning, such as videos, articles, or practice problems. Example: 'If you’d like more practice, I can recommend a few problems that are similar to this one!' Keep conversations / greetings that are not about acamdeics or subjects concise and professional.'"
chat.send_message(instruction)
chat2.send_message(instruction2)

def generate_course_outline_and_resources(test_name):
    course_request = f"Generate a detailed course outline for the {test_name} test. Provide units, topics covered in each unit, and specific online resources like videos and articles for each unit. Focus solely on test preparation content. Do not create an extremely long study guide outline though. organize by unit, not concept and keep it concise, but make sure to provide all the necessary links and resources."
    response = chat.send_message(course_request, stream=True)
    return response.text
@app.route('/')
def index():
    return render_template('index.html')  
@app.route('/upload_image', methods=['POST'])
def upload_image():
    if app.config['IMAGE_UPLOADED']:
        return jsonify({'error': 'You have already uploaded an image'}), 400

    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"})
    
    file = request.files['file']
    if len(request.files) > 1:
        return jsonify({'error': 'You can only upload one image'}), 400
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"})
    
    if file and allowed_file(file.filename):

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        app.config['IMAGE_UPLOADED'] = True 
        

        global uploaded_file
        uploaded_file = genai.upload_file(file_path)
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/chat', methods=['POST'])
def chat_with_bot():
    user_message = request.form.get('message', '')

    if app.config['IMAGE_UPLOADED']:
        response = model.generate_content([uploaded_file, "\n\n", "Here is the image that has the context for the user query. If the user sends a message unrelated to the image, ignore the image." + user_message])
        response_text = response.text  
    else:
        def generate():
            response = chat.send_message(user_message, stream=True)
            for chunk in response:
                if hasattr(chunk, 'text'):
                    yield chunk.text.encode('utf-8')

        return app.response_class(generate(), mimetype='text/plain')

    app.config['IMAGE_UPLOADED'] = False  
    app.config['UPLOADED_FILE'] = None  
    return jsonify({'response': response_text})

def set_upload_directory():
    directory = request.form.get('directory', None)
    if directory:

        directory = os.path.expanduser(directory)
        

        if os.path.exists(directory) and os.path.isdir(directory):
            app.config['UPLOAD_FOLDER'] = directory
            return jsonify({"success": True, "message": f"Upload directory set to {directory}"})
        else:
            return jsonify({"success": False, "error": "Invalid directory"}), 400
    return jsonify({"success": False, "error": "No directory provided"}), 400

@app.route('/generate_outline', methods=['POST'])
def generate_outline():
    test_name = request.form['test_name']
    course_outline = generate_course_outline_and_resources(test_name)
    return jsonify({'outline': course_outline})

@app.route('/process_audio', methods=['POST'])
def process_audio():
    try:
        
        data = request.get_json()

        
        transcript = data.get('transcript', '')
        if not transcript:
            return jsonify({"error": "No transcript provided"}), 400

        
        response = chat2.send_message(transcript)

        
        response_text = response.text

        if not response_text:
            return jsonify({"error": "No valid response from the model"}), 500

        
        return jsonify({"response": response_text})

    except Exception as e:
    
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
