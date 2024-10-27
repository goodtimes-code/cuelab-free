import mido
import time
from mido import Message
from pynput import keyboard

# Function to load notes from the text file
def load_notes():
    notes = []
    try:
        with open('notes.txt', 'r') as file:
            for line in file:
                line = line.strip()
                # Ignore lines that are empty or start with '#'
                if line and not line.startswith('#'):
                    # Split the line by semicolons to handle multiple notes
                    note_groups = line.split(';')
                    step_notes = []
                    for note_group in note_groups:
                        note_group = note_group.strip()
                        parts = note_group.split(',')
                        if len(parts) == 2:
                            try:
                                channel_number = int(parts[0])
                                note_number = int(parts[1])
                                step_notes.append((channel_number, note_number))
                            except ValueError:
                                print(f"Invalid numbers in notes.txt: {note_group}")
                        else:
                            print(f"Invalid note format in notes.txt: {note_group}")
                    if step_notes:
                        notes.append(step_notes)
                    else:
                        print(f"No valid notes found in line: {line}")
    except Exception as e:
        print(f"Error loading notes: {e}")
    return notes

# Initial loading of notes
notes = load_notes()

# Create a virtual MIDI output port
output_port_name = 'CueLab Free'
output = mido.open_output(output_port_name, virtual=True)
print(f"Virtual MIDI Output Port '{output_port_name}' created.")

# Initialize variables
current_index = -1  # Start at -1 so the first right arrow press plays the first note
last_played_notes = []

def play_notes(note_list):
    global last_played_notes
    # If notes were previously played, send Note Off messages
    for channel_number, note_number in last_played_notes:
        msg_off = Message('note_off', note=note_number, channel=channel_number)
        output.send(msg_off)
    last_played_notes.clear()

    # Send Note On messages for all notes in the current step
    for channel_number, note_number in note_list:
        msg_on = Message('note_on', note=note_number, velocity=127, channel=channel_number)
        output.send(msg_on)
        last_played_notes.append((channel_number, note_number))

    # Hold the notes for a short duration
    time.sleep(0.1)
    print(f"Played notes: {[note[1] for note in note_list]} on channels: {[note[0] for note in note_list]}")

def on_press(key):
    global current_index, notes
    try:
        if key == keyboard.Key.right:
            # Move forward in the list
            if current_index < len(notes) - 1:
                current_index += 1
                note_list = notes[current_index]
                play_notes(note_list)
            else:
                print("Reached the end of the note list.")
        elif key == keyboard.Key.left:
            # Move backward in the list
            if current_index > 0:
                current_index -= 1
                note_list = notes[current_index]
                play_notes(note_list)
            else:
                print("At the beginning of the note list.")
        elif key.char == 'r':
            # Reload notes.txt and maintain current position without replaying
            new_notes = load_notes()
            if len(new_notes) > current_index:
                # Only update if the new list accommodates the current index
                notes = new_notes
                print(f"Notes reloaded from notes.txt. Current position: {current_index + 1}")
            else:
                print("Reloaded notes are shorter than the current index.")
        elif key.char == '0':
            # Reset position to the beginning and play the first notes
            current_index = 0
            print("Position reset to the beginning of the note list and first notes played.")
            play_notes(notes[current_index])  # Play the notes at position 0
        elif key == keyboard.Key.esc:
            # Exit the program
            print("Exiting program.")
            return False
    except AttributeError:
        # Handle keys that have no 'char' attribute (e.g., special keys)
        pass
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("Press the right arrow key to play the next note or chord.")
    print("Press the left arrow key to play the previous note or chord.")
    print("Press 'r' to reload the notes from notes.txt.")
    print("Press '0' to reset to the beginning of the note list and play the first notes.")
    print("Press Esc to exit the program.")
    print("Make sure your MIDI software is connected to the virtual port.")
    # Start listening to keyboard inputs
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == "__main__":
    main()