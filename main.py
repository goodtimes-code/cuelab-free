from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
import mido
import time
from mido import Message
import threading

# Load notes from the file
def load_notes():
    try:
        with open('notes.txt', 'r') as file:
            return file.read()
    except Exception as e:
        print(f"Error loading notes: {e}")
        return ""

# Save notes to the file
def save_notes(content):
    try:
        with open('notes.txt', 'w') as file:
            file.write(content)
    except Exception as e:
        print(f"Error saving notes: {e}")

# Parse notes for playback with validation for MIDI range
def parse_notes(content):
    notes = []
    for line in content.strip().splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            note_groups = line.split(';')
            step_notes = []
            for note_group in note_groups:
                note_group = note_group.strip()
                parts = note_group.split(',')
                if len(parts) == 2:
                    try:
                        channel_number = int(parts[0])
                        note_number = int(parts[1])

                        # Validate that both values are within the MIDI range
                        if not (0 <= channel_number <= 15):
                            print(f"Invalid channel number '{channel_number}' in notes.txt: {note_group}")
                            continue  # Skip this note group

                        if not (0 <= note_number <= 127):
                            print(f"Invalid note number '{note_number}' in notes.txt: {note_group}")
                            continue  # Skip this note group

                        step_notes.append((channel_number, note_number))
                    except ValueError:
                        print(f"Invalid numbers in notes.txt: {note_group}")
            if step_notes:
                notes.append(step_notes)
    return notes

# Initialize variables
output_port_name = 'CueLab Free'
output = mido.open_output(output_port_name, virtual=True)
current_index = -1
last_played_notes = []

# Function to play a list of notes
def play_notes(note_list):
    global last_played_notes
    # Turn off any previously played notes
    for channel_number, note_number in last_played_notes:
        output.send(Message('note_off', note=note_number, channel=channel_number))
    last_played_notes.clear()
    
    # Send Note On messages for the new notes
    for channel_number, note_number in note_list:
        output.send(Message('note_on', note=note_number, velocity=127, channel=channel_number))
        last_played_notes.append((channel_number, note_number))
    
    # Hold the notes briefly
    time.sleep(0.1)
    print(f"Played notes: {[note[1] for note in note_list]} on channels: {[note[0] for note in note_list]}")

# Kivy App
class MidiApp(App):
    # Set the window title
    title = "CueLab Free"

    def build(self):
        # Main layout for the app
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Larger TextInput for displaying and editing notes.txt content
        self.notes_input = TextInput(text=load_notes(), font_size='16sp', size_hint=(1, 0.6), multiline=True)
        # Bind the on_text event to save notes in real-time
        self.notes_input.bind(text=self.on_text_change)
        main_layout.add_widget(self.notes_input)

        # Layout for main control buttons (Next Note and Previous Note) directly above menu buttons
        button_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.2))
        
        back_button = Button(text="Previous Note (←)", size_hint=(0.5, 1))
        back_button.bind(on_release=lambda x: self.start_left())
        button_layout.add_widget(back_button)

        start_button = Button(text="Next Note (→)", size_hint=(0.5, 1))
        start_button.bind(on_release=lambda x: self.start_right())
        button_layout.add_widget(start_button)

        main_layout.add_widget(button_layout)

        # Layout for the menu buttons at the bottom
        menu_layout = BoxLayout(orientation='horizontal', spacing=5, size_hint=(1, 0.2))

        reset_button = Button(text='Reset (0)', font_size=22, size_hint=(None, None), size=(160, 60))
        reset_button.bind(on_release=lambda btn: self.menu_action('reset'))
        menu_layout.add_widget(reset_button)

        quit_button = Button(text='Quit (Esc)', font_size=22, size_hint=(None, None), size=(160, 60))
        quit_button.bind(on_release=lambda btn: self.stop())
        menu_layout.add_widget(quit_button)

        main_layout.add_widget(menu_layout)

        # Bind keyboard events
        Window.bind(on_key_down=self.on_key_down)

        return main_layout

    def on_text_change(self, instance, value):
        # Save the content whenever text changes
        save_notes(value)
        print("Notes saved to notes.txt.")

    def start_right(self):
        global current_index
        notes = parse_notes(self.notes_input.text)
        if current_index < len(notes) - 1:
            current_index += 1
            play_notes(notes[current_index])

    def start_left(self):
        global current_index
        notes = parse_notes(self.notes_input.text)
        if current_index > 0:
            current_index -= 1
            play_notes(notes[current_index])

    def menu_action(self, action):
        if action == 'reset':
            self.reset_position()

    def reset_position(self):
        # Reset current index to the start and play the first notes
        global current_index
        current_index = 0
        notes = parse_notes(self.notes_input.text)
        if notes:
            play_notes(notes[current_index])

    def on_key_down(self, window, key, *args):
        # Key bindings for controls
        if key == 276:  # Left arrow
            self.start_left()
        elif key == 275:  # Right arrow
            self.start_right()
        elif key == 48:   # '0' key
            self.reset_position()
        elif key == 27:   # Esc key
            self.stop()

# Start Kivy application
if __name__ == '__main__':
    MidiApp().run()