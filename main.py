# main.py
# Tkinter GUI for CS 3502 project 3.
# Rhett Ward


import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path
import os
import time

import fileops


class FileManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Rhett Ward File Gui")
        self.root.geometry("820x560")

        # start in the user's home folder instead of C:\ to avoid immediate permission errors
        self.current_path = str(Path.home())

        # clipboard for copy/move.
        self.clipboard_path = None
        self.clipboard_mode = None

        self._build_top_bar()
        self._build_file_list()
        self._build_button_bar()
        self._build_status_bar()

        self.refresh()

    #region Widget Setup

    def _build_top_bar(self):
        frame = tk.Frame(self.root)
        frame.pack(fill="x", padx=6, pady=4)

        tk.Button(frame, text="Up", width=6, command=self.go_up).pack(side="left")

        self.path_label = tk.Label(frame, text="", anchor="w", relief="sunken", padx=6)
        self.path_label.pack(side="left", fill="x", expand=True, padx=6)

        tk.Button(frame, text="Refresh", width=8, command=self.refresh).pack(side="left")

    def _build_file_list(self):
        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=6, pady=2)

        columns = ("name", "type", "size", "modified")
        self.tree = ttk.Treeview(
            frame, columns=columns, show="headings", selectmode="browse"
        )
        self.tree.heading("name", text="Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("size", text="Size")
        self.tree.heading("modified", text="Modified")
        self.tree.column("name", width=340)
        self.tree.column("type", width=70, anchor="center")
        self.tree.column("size", width=100, anchor="e")
        self.tree.column("modified", width=160)

        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # double click: folders navigate in, files open the editor
        self.tree.bind("<Double-1>", self.on_double_click)

    def _build_button_bar(self):
        frame = tk.Frame(self.root)
        frame.pack(fill="x", padx=6, pady=4)

        buttons = [
            ("New File",   self.new_file),
            ("New Folder", self.new_folder),
            ("Open",       self.open_selected),
            ("Rename",     self.rename_selected),
            ("Delete",     self.delete_selected),
            ("Copy",       self.copy_selected),
            ("Move",       self.move_selected),
            ("Paste",      self.paste_selected),
            ("Properties", self.show_properties),
        ]
        for label, handler in buttons:
            tk.Button(frame, text=label, width=11, command=handler).pack(side="left", padx=2)

    def _build_status_bar(self):
        self.status = tk.Label(self.root, text="Ready", anchor="w", relief="sunken", padx=6)
        self.status.pack(fill="x", side="bottom")

    #endregion Widget Setup

    #region Helpers

    def set_status(self, msg):
        self.status.config(text=msg)

    def refresh(self):
        #read current folder and repopulate list
        self.path_label.config(text=self.current_path)

        for row in self.tree.get_children():
            self.tree.delete(row)

        try:
            entries = fileops.list_directory(self.current_path)
        except PermissionError:
            messagebox.showerror(
                "Permission denied",
                f"You don't have permission to read this folder:\n{self.current_path}",
            )
            self.set_status("Permission denied")
            return
        except FileNotFoundError:
            messagebox.showerror("Not found", "That folder doesn't exist anymore.")
            # try to back out to a folder that still exists
            self.current_path = str(Path.home())
            self.refresh()
            return
        except OSError as e:
            messagebox.showerror("Error", f"Could not read folder: {e}")
            return

        # folders first, then files, each alphabetical
        entries.sort(key=lambda e: (not e["is_dir"], e["name"].lower()))

        for e in entries:
            type_str = "Folder" if e["is_dir"] else "File"
            size_str = "" if e["is_dir"] else self._format_size(e["size"])
            if e["mtime"]:
                mod_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(e["mtime"]))
            else:
                mod_str = ""
            # uses the full path as the row id
            self.tree.insert(
                "", "end", iid=e["path"],
                values=(e["name"], type_str, size_str, mod_str),
            )

        self.set_status(f"{len(entries)} item(s)")

    def _format_size(self, n):
        units = ("B", "KB", "MB", "GB", "TB")
        i = 0
        while n >= 1024 and i < len(units) - 1:
            n /= 1024
            i += 1
        if i == 0:
            return f"{int(n)} {units[i]}"
        return f"{n:.1f} {units[i]}"

    def get_selected_path(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return sel[0]  # row id is the full path

    #endregion Helpers

    #region Navigation

    def go_up(self):
        parent = os.path.dirname(self.current_path)
        # prevents infinite drive root loop
        if parent and parent != self.current_path:
            self.current_path = parent
            self.refresh()

    def on_double_click(self, event):
        path = self.get_selected_path()
        if path is None:
            return
        if os.path.isdir(path):
            self.current_path = path
            self.refresh()
        else:
            self.open_selected()

    #endregion Navigation

    #region CRUD

    #Create
    def new_file(self):
        name = simpledialog.askstring("New File", "File name:", parent=self.root)
        if not name:
            return
        full = os.path.join(self.current_path, name)
        try:
            fileops.create_empty_file(full)
        except FileExistsError:
            messagebox.showerror("Already exists", f"A file called '{name}' already exists here.")
            return
        except PermissionError:
            messagebox.showerror("Permission denied", "You don't have permission to create a file here.")
            return
        except OSError as e:
            messagebox.showerror("Error", f"Could not create file: {e}")
            return
        self.set_status(f"Created {name}")
        self.refresh()

    #Create
    def new_folder(self):
        name = simpledialog.askstring("New Folder", "Folder name:", parent=self.root)
        if not name:
            return
        full = os.path.join(self.current_path, name)
        try:
            fileops.create_directory(full)
        except FileExistsError:
            messagebox.showerror("Already exists", f"A folder called '{name}' already exists here.")
            return
        except PermissionError:
            messagebox.showerror("Permission denied", "You don't have permission to create a folder here.")
            return
        except OSError as e:
            messagebox.showerror("Error", f"Could not create folder: {e}")
            return
        self.set_status(f"Created folder {name}")
        self.refresh()

    #Read
    def open_selected(self):
        path = self.get_selected_path()
        if path is None:
            messagebox.showinfo("No selection", "Pick a file to open first.")
            return
        # opening a folder = navigating into it
        if os.path.isdir(path):
            self.current_path = path
            self.refresh()
            return
        try:
            content = fileops.read_file(path)
        except PermissionError:
            messagebox.showerror("Permission denied", "You don't have permission to read this file.")
            return
        except OSError as e:
            messagebox.showerror("Error", f"Could not read file: {e}")
            return

        EditorWindow(self.root, path, content, self.refresh, self.set_status)

    #Update
    def rename_selected(self):
        path = self.get_selected_path()
        if path is None:
            messagebox.showinfo("No selection", "Pick something to rename first.")
            return
        old_name = os.path.basename(path)
        new_name = simpledialog.askstring(
            "Rename", "New name:", initialvalue=old_name, parent=self.root
        )
        if not new_name or new_name == old_name:
            return
        new_path = os.path.join(os.path.dirname(path), new_name)
        try:
            fileops.rename_path(path, new_path)
        except FileExistsError:
            messagebox.showerror("Already exists", f"Something named '{new_name}' is already there.")
            return
        except PermissionError:
            messagebox.showerror("Permission denied", "You don't have permission to rename this.")
            return
        except OSError as e:
            messagebox.showerror("Error", f"Could not rename: {e}")
            return
        self.set_status(f"Renamed to {new_name}")
        self.refresh()

    #Delete
    def delete_selected(self):
        path = self.get_selected_path()
        if path is None:
            messagebox.showinfo("No selection", "Pick something to delete first.")
            return
        name = os.path.basename(path)

        if os.path.isdir(path):
            self._delete_directory(path, name)
        else:
            self._delete_file(path, name)

    #Delete
    def _delete_file(self, path, name):
        if not messagebox.askyesno("Delete file", f"Delete '{name}'?\nThis cannot be undone."):
            return
        try:
            fileops.delete_file(path)
        except PermissionError:
            messagebox.showerror("Permission denied", "You don't have permission to delete this file.")
            return
        except OSError as e:
            # on Windows this is what you get if the file is open in another program
            messagebox.showerror("Error", f"Could not delete file: {e}")
            return
        self.set_status(f"Deleted {name}")
        self.refresh()

    #Delete
    def _delete_directory(self, path, name):
        try:
            empty = fileops.is_directory_empty(path)
        except PermissionError:
            messagebox.showerror("Permission denied", "You don't have permission to read this folder.")
            return

        if empty:
            if not messagebox.askyesno("Delete folder", f"Delete empty folder '{name}'?"):
                return
            try:
                fileops.delete_empty_directory(path)
            except PermissionError:
                messagebox.showerror("Permission denied", "You don't have permission to delete this folder.")
                return
            except OSError as e:
                messagebox.showerror("Error", f"Could not delete folder: {e}")
                return
        else:
            msg = f"'{name}' is not empty. Delete it and everything inside?\nThis cannot be undone."
            if not messagebox.askyesno("Delete folder", msg):
                return
            try:
                fileops.delete_directory_recursive(path)
            except PermissionError:
                messagebox.showerror("Permission denied", "You don't have permission to delete this folder.")
                return
            except OSError as e:
                messagebox.showerror("Error", f"Could not delete folder: {e}")
                return

        self.set_status(f"Deleted {name}")
        self.refresh()

    #Read
    def copy_selected(self):
        path = self.get_selected_path()
        if path is None:
            messagebox.showinfo("No selection", "Pick something to copy first.")
            return
        self.clipboard_path = path
        self.clipboard_mode = "copy"
        name = os.path.basename(path)
        self.set_status(f"Copied '{name}'. Navigate to a folder and click Paste.")

    #Read & Update
    def move_selected(self):
        path = self.get_selected_path()
        if path is None:
            messagebox.showinfo("No selection", "Pick something to move first.")
            return
        self.clipboard_path = path
        self.clipboard_mode = "move"
        name = os.path.basename(path)
        self.set_status(f"Cut '{name}' for move. Navigate to a folder and click Paste.")

    #Create
    def paste_selected(self):
        if self.clipboard_path is None:
            messagebox.showinfo(
                "Nothing to paste",
                "Use Copy or Move first to pick something, then come back and click Paste.",
            )
            return

        src = self.clipboard_path


        if not os.path.exists(src):
            messagebox.showerror("Source gone", "The original item no longer exists.")
            self.clipboard_path = None
            self.clipboard_mode = None
            return

        name = os.path.basename(src)
        dest_path = os.path.join(self.current_path, name)

        #prevent pasting a folder into a folder it is already in
        if os.path.abspath(dest_path) == os.path.abspath(src):
            messagebox.showerror("Cannot paste", "The item is already in this folder.")
            return

        # abspath to prevent /foo/bar looks like it starts with /foo/b
        if os.path.isdir(src):
            src_abs = os.path.abspath(src)
            dest_dir_abs = os.path.abspath(self.current_path)
            if dest_dir_abs == src_abs or dest_dir_abs.startswith(src_abs + os.sep):
                messagebox.showerror("Cannot paste", "Cannot paste a folder into itself.")
                return

        if not self._handle_overwrite(dest_path, name):
            return

        try:
            if self.clipboard_mode == "copy":
                fileops.copy_path(src, dest_path)
                verb = "Copied"
            else:
                fileops.move_path(src, dest_path)
                verb = "Moved"
        except PermissionError:
            messagebox.showerror("Permission denied", "You don't have permission for that.")
            return
        except OSError as e:
            messagebox.showerror("Error", f"Could not paste: {e}")
            return

        self.set_status(f"{verb} {name} here")

        # move clears the clipboard since the source is gone now,
        # Explorer behaves with Ctrl+C versus Ctrl+X.
        if self.clipboard_mode == "move":
            self.clipboard_path = None
            self.clipboard_mode = None

        self.refresh()

    #Create & Delete
    def _handle_overwrite(self, dest_path, name):

        if not os.path.exists(dest_path):
            return True

        if not messagebox.askyesno(
            "Already exists",
            f"'{name}' already exists at the destination.\nOverwrite?",
        ):
            return False

        try:
            if os.path.isdir(dest_path):
                fileops.delete_directory_recursive(dest_path)
            else:
                fileops.delete_file(dest_path)
        except PermissionError:
            messagebox.showerror("Permission denied", "Cannot overwrite the existing item.")
            return False
        except OSError as e:
            messagebox.showerror("Error", f"Could not overwrite: {e}")
            return False

        return True

    #Read
    def show_properties(self):
        path = self.get_selected_path()
        if path is None:
            messagebox.showinfo("No selection", "Pick something to see properties for.")
            return
        try:
            info = fileops.get_file_info(path)
        except PermissionError:
            messagebox.showerror("Permission denied", "Can't read properties for this item.")
            return
        except OSError as e:
            messagebox.showerror("Error", f"Could not get properties: {e}")
            return

        name = os.path.basename(path)
        lines = [
            f"Name:      {name}",
            f"Path:      {path}",
            f"Type:      {'Folder' if info['is_dir'] else 'File'}",
            f"Size:      {info['size']} bytes",
            f"Modified:  {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(info['mtime']))}",
            f"Created:   {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(info['ctime']))}",
            f"Accessed:  {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(info['atime']))}",
            f"Readable:  {info['readable']}",
            f"Writable:  {info['writable']}",
            f"Mode bits: {oct(info['mode'])}",
        ]
        messagebox.showinfo("Properties", "\n".join(lines))

#endregion CRUD

class EditorWindow:
    #Popup window for viewing and editing a single file.

    def __init__(self, parent, path, content, on_save, set_status):
        self.path = path
        self.on_save = on_save
        self.set_status = set_status

        self.win = tk.Toplevel(parent)
        self.win.title(f"Editing - {os.path.basename(path)}")
        self.win.geometry("640x440")

        self.text = tk.Text(self.win, wrap="word", undo=True)
        self.text.pack(fill="both", expand=True, padx=4, pady=4)
        self.text.insert("1.0", content)

        btns = tk.Frame(self.win)
        btns.pack(fill="x", padx=4, pady=4)
        tk.Button(btns, text="Save", width=10, command=self.save).pack(side="right", padx=2)
        tk.Button(btns, text="Close", width=10, command=self.win.destroy).pack(side="right", padx=2)

    def save(self):
        # end-1c trims the trailing newline that Tk's Text widget always adds
        new_content = self.text.get("1.0", "end-1c")
        try:
            fileops.write_file(self.path, new_content)
        except PermissionError:
            messagebox.showerror("Permission denied", "This file is read-only or in use by another program.")
            return
        except OSError as e:
            messagebox.showerror("Error", f"Could not save file: {e}")
            return
        self.set_status(f"Saved {os.path.basename(self.path)}")
        self.on_save()


def main():
    root = tk.Tk()
    FileManagerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()