import gi
import os
import fnmatch
import logging

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

# Configure logging
logging.basicConfig(filename="search_log.txt", level=logging.DEBUG, format="%(asctime)s - %(message)s")

class FileSearchApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Quick File Search")
        
        # Set dark theme
        settings=Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", True)

        # Window setup
        self.set_default_size(600, 400)
        self.connect("destroy", Gtk.main_quit)

        # Initialize attributes
        self.search_locations=[]
        self.exclude_paths=[]
        self.logging_enabled=0
        self.selected_file_path=None

        # Create GUI components
        self.create_ui()

    def create_ui(self):
        grid=Gtk.Grid(column_spacing=10, row_spacing=10, margin=10)
        self.add(grid)

        # Search fields
        self.entry_name=Gtk.Entry(placeholder_text="Search by name")
        grid.attach(Gtk.Label(label="File Name:"), 0, 0, 1, 1)
        grid.attach(self.entry_name, 1, 0, 1, 1)

        self.entry_type=Gtk.Entry(placeholder_text="File type (e.g. .txt, .py)")
        grid.attach(Gtk.Label(label="File Type:"), 0, 1, 1, 1)
        grid.attach(self.entry_type, 1, 1, 1, 1)

        # Recursive search checkbox
        self.recursive_check=Gtk.CheckButton(label="Recursive Search")
        grid.attach(self.recursive_check, 1, 2, 1, 1)

        # Case insensitive search checkbox
        self.case_insensitive_check=Gtk.CheckButton(label="Case Insensitive")
        grid.attach(self.case_insensitive_check, 0, 3, 2, 1)

        # Exclude path field
        self.entry_exclude=Gtk.Entry(placeholder_text="Exclude paths (comma-separated)")
        grid.attach(Gtk.Label(label="Exclude Paths:"), 0, 4, 1, 1)
        grid.attach(self.entry_exclude, 1, 4, 1, 1)

        # Add search locations button
        self.locations_button=Gtk.Button(label="Add Search Location")
        self.locations_button.connect("clicked", self.on_add_location_clicked)
        grid.attach(self.locations_button, 0, 5, 2, 1)

        # List to display search locations
        self.location_store=Gtk.ListStore(str)
        self.location_view=Gtk.TreeView(model=self.location_store)
        self.location_view.append_column(Gtk.TreeViewColumn("Search Locations", Gtk.CellRendererText(), text=0))
        grid.attach(Gtk.Label(label="Search Locations:"), 0, 6, 2, 1)
        grid.attach(self.location_view, 0, 7, 2, 1)

        # Search button
        self.search_button=Gtk.Button(label="Search")
        self.search_button.connect("clicked", self.on_search_clicked)
        grid.attach(self.search_button, 0, 8, 2, 1)

        # Results area
        self.results_store=Gtk.ListStore(str)
        self.results_view=Gtk.TreeView(model=self.results_store)
        self.results_view.append_column(Gtk.TreeViewColumn("Search Results", Gtk.CellRendererText(), text=0))
        self.results_view.connect("row-activated", self.on_result_clicked)
        self.results_view.connect("cursor-changed", self.on_selection_changed)
        grid.attach(Gtk.Label(label="Search Results:"), 0, 9, 2, 1)
        grid.attach(self.results_view, 0, 10, 2, 1)

        # Enable logging checkbox
        self.logging_check=Gtk.CheckButton(label="Enable Logging")
        grid.attach(self.logging_check, 0, 11, 2, 1)

        # File options area
        self.options_box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        grid.attach(self.options_box, 2, 10, 1, 1)

        # File option buttons
        self.create_file_option_buttons()

        # About button
        about_button=Gtk.Button(label="About")
        about_button.connect("clicked", self.on_about_clicked)
        grid.attach(about_button, 0, 12, 2, 1)

    def create_file_option_buttons(self):
        # Define the file option buttons
        self.open_button=Gtk.Button(label="Open in New Window")
        self.open_button.connect("clicked", self.on_open_file_clicked)
        self.options_box.pack_start(self.open_button, True, True, 0)

        self.cut_button=Gtk.Button(label="Cut")
        self.cut_button.connect("clicked", self.on_cut_file_clicked)
        self.options_box.pack_start(self.cut_button, True, True, 0)

        self.copy_button=Gtk.Button(label="Copy")
        self.copy_button.connect("clicked", self.on_copy_file_clicked)
        self.options_box.pack_start(self.copy_button, True, True, 0)

        self.paste_button=Gtk.Button(label="Paste")
        self.paste_button.connect("clicked", self.on_paste_file_clicked)
        self.options_box.pack_start(self.paste_button, True, True, 0)

        self.remove_button=Gtk.Button(label="Remove")
        self.remove_button.connect("clicked", self.on_remove_file_clicked)
        self.options_box.pack_start(self.remove_button, True, True, 0)

        # Hide options box by default
        self.options_box.hide()

    def on_add_location_clicked(self, widget):
        dialog=Gtk.FileChooserDialog(
            title="Select Search Location", 
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        if dialog.run() == Gtk.ResponseType.OK:
            folder=dialog.get_filename()
            self.search_locations.append(folder)
            self.location_store.append([folder])
        dialog.destroy()

    def on_search_clicked(self, widget):
        # Get search parameters
        name=self.entry_name.get_text()
        file_type=self.entry_type.get_text()
        recursive=self.recursive_check.get_active()
        case_insensitive=self.case_insensitive_check.get_active()
        exclude_paths=[path.strip() for path in self.entry_exclude.get_text().split(",") if path.strip()]
        logging_enabled=self.logging_check.get_active()

        # Start search
        self.results_store.clear()
        for location in self.search_locations:
            for root, dirs, files in os.walk(location):
                # Apply exclusion paths
                if any(excl in root for excl in exclude_paths):
                    continue

                # Perform search by name and type
                matched_files=[]
                for f in files:
                    # Check name match considering case insensitivity
                    match_name=fnmatch.fnmatch(f.lower() if case_insensitive else f, f"*{name.lower()}*" if case_insensitive else f"*{name}*")
                    match_type=f.endswith(file_type) if file_type else True

                    if match_name and match_type:
                        matched_files.append(f)

                # Add results
                for file in matched_files:
                    full_path=os.path.join(root, file)
                    self.results_store.append([full_path])

                    # Logging
                    if logging_enabled:
                        logging.info(f"Found: {full_path}")

                if not recursive:
                    break

    def on_result_clicked(self, tree_view, path, column):
        # Handle left-click to open file
        model=tree_view.get_model()
        file_path=model[path][0]
        os.system(f"xdg-open '{file_path}'")

    def on_selection_changed(self, tree_view):
        selection=tree_view.get_selection()
        model, treeiter=selection.get_selected()
        if treeiter is not None:
            self.selected_file_path=model[treeiter][0]
            self.options_box.show_all()  # Show options box
        else:
            self.selected_file_path=None
            self.options_box.hide()  # Hide options box

    def on_open_file_clicked(self, widget):
        if self.selected_file_path:
            directory=os.path.dirname(self.selected_file_path)  # Get the directory of the selected file
            os.system(f"xdg-open '{directory}'")  # Open the file manager in that directory


    def on_cut_file_clicked(self, widget):
        # Implement cut functionality (to be defined as needed)
        pass

    def on_copy_file_clicked(self, widget):
        # Implement copy functionality (to be defined as needed)
        pass

    def on_paste_file_clicked(self, widget):
        # Implement paste functionality (to be defined as needed)
        pass

    def on_remove_file_clicked(self, widget):
        if self.selected_file_path:
            dialog=Gtk.MessageDialog(
                self,
                Gtk.DialogFlags.MODAL,
                Gtk.MessageType.QUESTION,
                Gtk.ButtonsType.YES_NO,
                "Are you sure you want to remove this file?"
            )
            dialog.format_secondary_text(f"File: {self.selected_file_path}")
            response=dialog.run()
            if response == Gtk.ResponseType.YES:
                os.remove(self.selected_file_path)
                self.results_store.remove(self.results_store.get_iter_first())
                logging.info(f"Removed: {self.selected_file_path}")
            dialog.destroy()

    def on_about_clicked(self, widget):
        dialog=Gtk.MessageDialog(
            self,
            Gtk.DialogFlags.MODAL,
            Gtk.MessageType.INFO,
            Gtk.ButtonsType.OK,
            "Quick File Search Application\n\nAuthor: Jay Mee @ J~Net 2024\nVersion: 1.0"
        )
        dialog.run()
        dialog.destroy()

if __name__ == "__main__":
    app=FileSearchApp()
    app.show_all()
    Gtk.main()

