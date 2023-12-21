"""
length_indicator$command$paramete1$parameter2$....parameterN
"""

import socket
import glob
import shutil
import os
import subprocess
import base64
import pyautogui
from PIL import Image


IP = '0.0.0.0'
PORT = 8820
QUEUE_SIZE = 1
MAX_PACKET = 1024


def dir(file_path):
    """Receives a file path
    returns a string of the files list in the path.
    """
    try:
        my_file = str(file_path) + '/*'
        files_list = glob.glob(my_file)
        files = ""
        for file in files_list:
            files += file
            files += "\n"
        list_files = [files]
        print(list_files)
        if list_files == ['']:
            return ["Directory not found or contains no files"]
        return list_files
    except FileNotFoundError:
        print("er1")
        return ["Directory not found"]


def delete(file_path):
    """
    :param file_path: The path of the file to be deleted.
    :return: A message indicating the result of the file deletion.
    """
    try:
        os.remove(file_path)
        return "File successfully deleted"
    except FileNotFoundError:
        return ["Error Directory not found"]
    except PermissionError:
        return ["Error permission denied"]


def copy_file(source_path, destination_path):
    """
    :param source_path: file path to copy from
    :param destination_path: file path to copy to
    :return: confirmation or deconfirmation of the action
    """
    try:
        shutil.copy2(source_path, destination_path)
        return [f"File copied successfully from {source_path} to {destination_path}"]
    except FileNotFoundError:
        return ["One or both of the given files not found"]
    except PermissionError:
        return ["Permission denied"]


def execute_program(program_path):
    """
    Execute a program. example: "C:/Program Files/Notepad++/notepad++.exe"
    Parameters:
    - program_path (str): The full path to the program to be executed.
    Returns:
    - str: A message indicating whether the execution was successful or not.
    """
    try:
        subprocess.call([program_path])
        return [f"Program '{program_path}' executed successfully"]
    except FileNotFoundError:
        return [f"Error: Program '{program_path}' not found"]
    except Exception as e:
        print(e)
        return [f"error is {e}"]


def take_screenshot_and_save():
    """
    Take a screenshot and save it to ."screenshot.jpg"
    Returns:
    - str: A message indicating whether the operation was successful or not.
    """
    try:
        screenshot = pyautogui.screenshot()
        screenshot.save("screenshot.jpg")
        return [f"Screenshot saved successfully to screenshot.jpg"]
    except Exception as e:
        return [f"Error: {e}"]


def image_encode():
    """
    encoding screenshot.jpg
    :return: encoded string
    """
    try:
        with open("screenshot.jpg", 'rb') as image_file:
            image_bytes = image_file.read()
            encoded_image = base64.b64encode(image_bytes)
            encoded_string = encoded_image.decode("utf-8")
            return [encoded_string]
    except Exception as e:
        print(f"Error: {e}")
        return [f"error occurred {e}"]


def new_receive_protocol(client_socket):
    """
    Decode and extract information from the received message.
    Parameters:
    - client socket : to receive the message from the sender
    Returns:
    - list: A list containing the command and parameters.
    """
    try:
        length_indicator = client_socket.recv(7).decode()
        length_indicator = int(length_indicator) - 7
        client_socket.recv(1)  # remove the split sign of length indicator($)
        received_message = b''
        while length_indicator >= 1024:
            received_message += client_socket.recv(int(1024))
        if 1024 > length_indicator > 0:
            received_message += client_socket.recv(int(length_indicator))

        parts = received_message.split(b'$')

        command = parts[0].decode('utf-8')
        parameters_to_decode = parts[1:]
        decoded_strings = [byte.decode() for byte in parameters_to_decode]

        fixed_parameters = [param.replace("//", "\\") for param in decoded_strings]
        received_cmd_prm = [command]
        for param in fixed_parameters:
            received_cmd_prm.append(param)

        return received_cmd_prm
    except Exception as e:
        return f"Error: {e}"


def new_send_protocol(command, parameters):
    """
    Encode the command and parameters and create a formatted message.

    Parameters:
    - command (str): The command to be sent.
    - list (str): parameters to be sent.

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
        return new_send_protocol("error", error_message)


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((IP, PORT))
        server_socket.listen(QUEUE_SIZE)
        print('Server is up and running...')
        while True:
            client_socket, client_address = server_socket.accept()
            print(f'Connected to {client_address}')
            try:
                while True:
                    msg_parts = new_receive_protocol(client_socket)
                    command = msg_parts[0]

                    if len(msg_parts) == 2:
                        parameter1 = msg_parts[1]
                        parameter2 = ''
                    elif len(msg_parts) == 3:
                        parameter1 = msg_parts[1]
                        parameter2 = msg_parts[2]
                    else:
                        parameter1 = 'no parameter'
                        parameter2 = 'no parameter'

                    print("command is", command, msg_parts)
                    if command == "DIR":
                        return_msg = dir(parameter1)
                    elif command == "DELETE":
                        return_msg = delete(parameter1)
                    elif command == "COPY":
                        return_msg = copy_file(parameter1, parameter2)
                    elif command == "EXECUTE":
                        return_msg = execute_program(parameter1)
                    elif command == "TAKE_SCREENSHOT":
                        return_msg = take_screenshot_and_save()
                    elif command == "SEND_PHOTO":
                        return_msg = image_encode()
                    elif command == "EXIT":
                        client_socket.send(new_send_protocol(command, 'You were disconnected from the server'))
                        break  # move to next client
                    else:
                        return_msg = ["invalid command"]
                    client_socket.send(new_send_protocol(command, return_msg))
            except socket.error as msg:
                print('Client socket disconnected - ' + str(msg))
            finally:
                client_socket.close()
                print(f'Connection to {client_address} closed')
    except socket.error as msg:
        print('Failed to open server socket - ' + str(msg))
    finally:
        server_socket.close()


if __name__ == '__main__':
    main()
