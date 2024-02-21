from flask import Flask, render_template, request, send_file
from PIL import Image
import os

app = Flask(__name__)

last_message = ""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/image/encode')
def encode_file():
    return render_template('image/encode.html')

@app.route('/image/decode')
def decode_file():
    return render_template('image/decode.html', decoded_message=last_message, decoded_message_available=bool(last_message))

# The encode of a message into an image algorithm
def encode_image(input_path, text):

    # Read the data
    image = Image.open(input_path)

    # Get the dimensions
    x, y = image.size
    n = len(text)

    # Check if it's possible for encoding
    if x * y // 3 < n:
        raise ValueError("Text is too large to be encoded in this image") # I want to be honest, I just hope this works, it wasn't actually tested
    else:
        # Load the pixels
        pixels = image.load()
        i = 0
        j = 0
        for c in text:

            # Get the binary of the character
            unicode = ord(c)
            binary = format(unicode, 'b')

            # Add leading zeros if necessary
            while len(binary) < 8:
                binary = '0' + binary

            # Encode on the first pixel
            r, g, b = pixels[i, j]
            r = (r & 254) | int(binary[0])
            g = (g & 254) | int(binary[1])
            b = (b & 254) | int(binary[2])
            pixels[i, j] = (r, g, b)
            i = i + 1
            if i == x:
                i = 0
                j = j + 1

            # Encode on the second pixel
            r, g, b = pixels[i, j]
            r = (r & 254) | int(binary[3])
            g = (g & 254) | int(binary[4])
            b = (b & 254) | int(binary[5])
            pixels[i, j] = (r, g, b)
            i = i + 1
            if i == x:
                i = 0
                j = j + 1
            #Encode on the third pixel
            r, g, b = pixels[i, j]
            r = (r & 254) | int(binary[6])
            g = (g & 254) | int(binary[7])
            pixels[i, j] = (r, g, b)
            i = i + 1
            if i == x:
                i = 0
                j = j + 1

    # Create the NULL character to end the string
    r, g, b = pixels[i, j]
    r = (r & 254)
    g = (g & 254)
    b = (b & 254)
    pixels[i, j] = (r, g, b)
    i = i + 1
    if i == x:
        i = 0
        j = j + 1

    # Encode on the second pixel
    r, g, b = pixels[i, j]
    r = (r & 254)
    g = (g & 254)
    b = (b & 254)
    pixels[i, j] = (r, g, b)
    i = i + 1
    if i == x:
        i = 0
        j = j + 1

    #Encode on the third pixel
    r, g, b = pixels[i, j]
    r = (r & 254)
    g = (g & 254)
    pixels[i, j] = (r, g, b)

    # Save and return the encoded image
    encoded_path = 'static/images/last_encoded.png'
    image.save(encoded_path)
    return encoded_path

# The decode of an image algorithm
def decode_image(input_path):

    # Read the data
    image = Image.open(input_path)

    # Get the dimensions
    x, y = image.size
    pixels = image.load()

    # Initialise the values
    i = 0
    j = 0
    string = ""
    while True:
        binary = ""

        # Get the first 3 bits of the letter
        r, g, b = pixels[i, j]
        r = r & 1
        binary = binary + str(r)
        g = g & 1
        binary = binary + str(g)
        b = b & 1
        binary = binary + str(b)
        i = i + 1
        if i == x:
            i = 0
            j = j + 1
        
        # Get the next 3 bits of the letter
        r, g, b = pixels[i, j]
        r = r & 1
        binary = binary + str(r)
        g = g & 1
        binary = binary + str(g)
        b = b & 1
        binary = binary + str(b)
        i = i + 1
        if i == x:
            i = 0
            j = j + 1
        
        # Get the last 2 bits of the letter
        r, g, b = pixels[i, j]
        r = r & 1
        binary = binary + str(r)
        g = g & 1
        binary = binary + str(g)
        i = i + 1
        if i == x:
            i = 0
            j = j + 1
        
        # Transform the string on 0s and 1s into a number, check if is NULL.If it isn't, transform it to a character
        nr = int(binary, 2)
        if nr == 0:
            break
        else:
            string = string + chr(nr)
    
    return string

# For the encode part of the image
@app.route('/encode', methods=['POST'])
def encode():
    # Retrieve the image and the message that were send
    image = request.files['image']
    message = request.form['message']

    # Save the uploaded image if it asked for later
    image.save('static/images/last_input.png')

    # Encode the message into the image and save that image too
    encoded_image_path = encode_image('static/images/last_input.png', message)

    # Return the encoded image to show in the 'encode.html' file
    return send_file(encoded_image_path, as_attachment=True)

# For asking for the last encoded image
@app.route('/image/last/encoded', methods=['GET'])
def get_encoded():
    return send_file('static/images/last_encoded.png', as_attachment=True)

# For the decode part of the message
@app.route('/decode', methods=['POST'])
def decode():
    # For when the user askes for the latest message decoded
    global last_message

    # Retrieve image from the form data
    image = request.files['image']

    # Save the uploaded image to the desired location
    image_path = 'static/images/last_asked_decode.png'
    image.save(image_path)

    # Call the decode_image function with the provided input
    decoded_message = decode_image(image_path)

    last_message = decoded_message  # Update the last message variable with the decoded message
    return render_template('image/decode.html', decoded_message=last_message, decoded_message_available=bool(last_message)) # Send the values to actually be displayed

# For when the user asks for the latest message that was decoded
@app.route('/image/last/decoded', methods=['GET'])
def get_decoded():
    if last_message:
        with open('static/messages/last_decoded_message.txt', 'w') as file:
            file.write(last_message)
        return send_file('static/messages/last_decoded_message.txt', as_attachment=True)
    else:
        return render_template('image/decode.html', decoded_message=last_message, decoded_message_available=bool(last_message))

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port=80)
