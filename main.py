import os
import time
import base64
import hashlib
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from cryptography.fernet import Fernet

class FileManagerApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical')

        # Search bar
        self.search_input = TextInput(hint_text='Search files...', size_hint_y=None, height=40)
        self.search_input.bind(text=self.on_search)
        self.layout.add_widget(self.search_input)

        # File chooser
        self.file_chooser = FileChooserIconView(path=os.path.expanduser('~'))
        self.layout.add_widget(self.file_chooser)

        # Password input for encryption
        self.password_input_encrypt = TextInput(hint_text='Enter password to encrypt', password=True, size_hint_y=None, height=40)
        self.layout.add_widget(self.password_input_encrypt)

        # Shared users input
        self.password_input_shared_with = TextInput(hint_text='Share with (comma-separated)', size_hint_y=None, height=40)
        self.layout.add_widget(self.password_input_shared_with)

        # Encrypt and Share button
        encrypt_btn = Button(text='Encrypt and Share', on_press=self.encrypt_file)
        self.layout.add_widget(encrypt_btn)

        # Password input for decryption
        self.password_input_decrypt = TextInput(hint_text='Enter password to decrypt', password=True, size_hint_y=None, height=40)
        self.layout.add_widget(self.password_input_decrypt)

        # Decrypt button
        decrypt_btn = Button(text='Decrypt File', on_press=self.decrypt_file)
        self.layout.add_widget(decrypt_btn)

        # Change password inputs
        self.password_input_old = TextInput(hint_text='Enter old password', password=True, size_hint_y=None, height=40)
        self.layout.add_widget(self.password_input_old)

        self.password_input_new = TextInput(hint_text='Enter new password', password=True, size_hint_y=None, height=40)
        self.layout.add_widget(self.password_input_new)

        # Change Password button
        change_password_btn = Button(text='Change Password', on_press=self.change_password)
        self.layout.add_widget(change_password_btn)

        # Button to view file traces
        view_trace_btn = Button(text='View File Trace', on_press=self.view_file_trace)
        self.layout.add_widget(view_trace_btn)

        return self.layout

    def on_search(self, instance, value):
        if not value:
            self.file_chooser.filter = []
            self.file_chooser.refresh()
            return
        self.file_chooser.filter = [value]
        self.file_chooser.refresh()

    def generate_key(self, password):
        password_bytes = password.encode('utf-8')
        key = hashlib.sha256(password_bytes).digest()
        return base64.urlsafe_b64encode(key)

    def log_file_activity(self, file_name, action):
        log_file = f"{file_name}.log"
        with open(log_file, 'a') as log:
            log.write(f"{time.ctime()}: {action}\n")

    def encrypt_file(self, instance):
        selected = self.file_chooser.selection
        if not selected:
            self.show_popup('Error', 'No file selected.')
            return

        password = self.password_input_encrypt.text
        shared_with = self.password_input_shared_with.text.split(',')  # Get users to share with
        if not password:
            self.show_popup('Error', 'Please enter a password.')
            return

        key = self.generate_key(password)
        cipher = Fernet(key)

        try:
            with open(selected[0], 'rb') as file:
                original = file.read()
                encrypted = cipher.encrypt(original)

            encrypted_filename = selected[0] + '.encrypted'
            with open(encrypted_filename, 'wb') as file:
                file.write(encrypted)

            # Log file activity
            self.log_file_activity(encrypted_filename, "File Encrypted")
            self.show_popup('Success', f'File encrypted as {encrypted_filename}\nShared with: {", ".join(shared_with)}')
        except Exception as e:
            self.show_popup('Error', f'An error occurred: {str(e)}')

    def decrypt_file(self, instance):
        selected = self.file_chooser.selection
        if not selected:
            self.show_popup('Error', 'No file selected.')
            return

        password = self.password_input_decrypt.text
        if not password:
            self.show_popup('Error', 'Please enter a password.')
            return

        key = self.generate_key(password)
        cipher = Fernet(key)

        try:
            with open(selected[0], 'rb') as file:
                encrypted_data = file.read()
                decrypted = cipher.decrypt(encrypted_data)

            decrypted_filename = selected[0].replace('.encrypted', '')
            with open(decrypted_filename, 'wb') as file:
                file.write(decrypted)

            self.show_popup('Success', f'File decrypted as {decrypted_filename}')
            # Log file activity
            self.log_file_activity(decrypted_filename, "File Decrypted")
        except Exception as e:
            self.show_popup('Error', f'An error occurred: {str(e)}')

    def change_password(self, instance):
        selected = self.file_chooser.selection
        if not selected:
            self.show_popup('Error', 'No file selected.')
            return

        old_password = self.password_input_old.text
        new_password = self.password_input_new.text
        if not old_password or not new_password:
            self.show_popup('Error', 'Please enter both old and new passwords.')
            return

        key = self.generate_key(old_password)
        cipher = Fernet(key)

        try:
            with open(selected[0], 'rb') as file:
                encrypted_data = file.read()
                decrypted = cipher.decrypt(encrypted_data)

            # Encrypt the file with the new password
            new_key = self.generate_key(new_password)
            new_cipher = Fernet(new_key)
            encrypted = new_cipher.encrypt(decrypted)

            # Save the new encrypted file
            with open(selected[0], 'wb') as file:
                file.write(encrypted)

            self.show_popup('Success', 'Password changed and file re-encrypted.')
            # Log file activity
            self.log_file_activity(selected[0], "Password Changed")
        except Exception as e:
            self.show_popup('Error', f'An error occurred: {str(e)}')

    def view_file_trace(self, instance):
        selected = self.file_chooser.selection
        if not selected:
            self.show_popup('Error', 'No file selected.')
            return

        trace_file = f"{selected[0]}.log"
        if not os.path.exists(trace_file):
            self.show_popup('Info', 'No trace available for this file.')
            return

        layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))

        with open(trace_file, 'r') as log:
            for line in log:
                layout.add_widget(Label(text=line.strip()))

        scroll_view = ScrollView(size_hint=(1, 0.5))
        scroll_view.add_widget(layout)

        popup = Popup(title='File Trace', content=scroll_view, size_hint=(0.9, 0.9))
        popup.open()

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.7, 0.5))
        popup.open()

if __name__ == '__main__':
    FileManagerApp().run()
