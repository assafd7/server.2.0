import socket
from PIL import Image
from io import BytesIO
import base64

MAX_PACKET = 1024

commands = ["DIR", "DELETE", "COPY", "EXECUTE", "TAKE_SCREENSHOT", "SEND_PHOTO", "EXIT"]


def command_check(message):
    """
    Checks to see if the message is a valid command.
    Parameters:
      message (str): The command the user has entered.
    Returns:
      str: If message is command, it returns the message else returns 'invalid'.
    """
    if message not in commands:
        print(f'invalid message, only use one of these commands {commands}')
        return False
    else:
        return True


def new_send_protocol(command, parameters):
    """
    Encode the command and parameters and create a formatted message.

    Parameters:
    - command (str): The command to be sent.
    - *parameters lst(str): Variable number of parameters to be sent.

    Returns:
    - bytes: The formatted message with a length indicator.
    """
    try:
        encoded_command = command.encode()

        fixed_parameters = [str(param).replace("\\", "//") for param in parameters]

        encoded_parameters = [param.encode() for param in fixed_parameters]

        message_parts = [encoded_command] + encoded_parameters
        message = b'$'.join(message_parts)

        message_length = len(message) + 8
        message_length = str(message_length).zfill(7)
        length_indicator = f"{message_length}".encode('utf-8')

        total_message = b'$'.join([length_indicator, message])
        return total_message
    except Exception as e:
        error_message = f"Error: {e}"
        return error_message.encode()


def decode_image(image_bytes):
    try:
        image_buffer = BytesIO(image_bytes)
        image = Image.open(image_buffer)
        image.save("screenshot.jpg")
        print("Image saved to screenshot.jpg")

    except Exception as e:
        print(f"Error decoding and creating image: {e}")
        return None


def new_receive_protocol(client_socket):
    """
    Decode and extract information from the received message.
    Parameters:
    - client socket : to receive the message from the sender
    Returns:
    - tuple: A tuple containing the command and parameters.
    """
    try:
        length_indicator = client_socket.recv(7).decode()
        length_indicator = int(length_indicator) - 7
        received_message = b''
        while length_indicator >= 1024:
            received_message += client_socket.recv(int(1024))
        if 1024 > length_indicator > 0:
            received_message += client_socket.recv(int(length_indicator))

        parts = received_message.split(b'$')
        parts = parts[1:]
        command = parts[0].decode('utf-8')
        if command == "SEND_PHOTO":
            image_bytes = base64.b64decode(parts[1])
            decode_image(image_bytes)
            return [command, "image saved in screenshot.jpg"]
        else:
            parameters_to_decode = parts[1:]

        decoded_strings = [byte.decode() for byte in parameters_to_decode]

        fixed_parameters = [param.replace("//", "\\") for param in decoded_strings]
        received_cmd_prm = [command]
        for param in fixed_parameters:
            received_cmd_prm.append(param)
        return received_cmd_prm
    except Exception as e:
        return f"Error: {e}"


def main():
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        my_socket.connect(('127.0.0.1', 8820))
        while True:
            command = input("input your command(DIR, DELETE, COPY, EXECUTE, TAKE_SCREENSHOT, SEND_PHOTO, EXIT): ")
            if not command_check(command):
                command = input("input valid command (DIR, DELETE, COPY, EXECUTE, TAKE_SCREENSHOT, SEND_PHOTO, EXIT): ")

            parameters = []
            input1 = ''
            while input1 != "$":
                input1 = input("input parameters, input '$' to stop: ")
                if input1 != '$':
                    parameters.append(input1)

            my_socket.send(new_send_protocol(command, parameters))
            msg_parts = new_receive_protocol(my_socket)
            if len(msg_parts) == 2:
                parameter1 = msg_parts[1]
            else:
                parameter1 = 'no parameter'

            print(msg_parts[0] + "\n" + parameter1)
            if command == "EXIT":
                break
    except socket.error as err:
        print('Received socket error:', str(err))
    finally:
        my_socket.close()


if __name__ == '__main__':
    main()
