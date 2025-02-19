import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import pygame
import subprocess
import sys
import platform

class GameEditor:
    def __init__(self, master):
        self.master = master
        master.title("Construct-like Editor")
        master.geometry("1000x600")

        # Store window components in separate frames
        self.left_frame = tk.Frame(master, width=600, height=600)
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        self.left_frame.grid_propagate(False)  # Prevent frame from shrinking
        
        self.right_frame = tk.Frame(master, width=400, height=600)
        self.right_frame.grid(row=0, column=1, sticky="nsew")
        
        # Configure grid weights
        master.grid_columnconfigure(0, weight=3)
        master.grid_columnconfigure(1, weight=1)
        master.grid_rowconfigure(0, weight=1)

        # Initialize Pygame (without embedding in Tkinter)
        os.environ['SDL_VIDEODRIVER'] = ''  # Let SDL choose the best driver
        pygame.init()
        
        # Set up the preview canvas
        self.canvas = tk.Canvas(self.left_frame, width=600, height=400, bg='white')
        self.canvas.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Setup right side with separate frames for properties and toolbox
        self.properties_frame = tk.LabelFrame(self.right_frame, text="Properties", width=380, height=300)
        self.properties_frame.pack(pady=10, padx=10, fill=tk.BOTH)
        self.properties_frame.pack_propagate(False)  # Prevent frame from shrinking

        self.toolbox_frame = tk.LabelFrame(self.right_frame, text="Toolbox", width=380, height=200)
        self.toolbox_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Game objects list and selection tracking
        self.objects = []
        self.selected_object = None
        self.selected_index = None
        
        # Create UI components
        self.create_toolbox()
        self.create_properties_panel()
        
        # Set up periodic refreshing of the canvas
        self.update_preview()
    
    def create_toolbox(self):
        btn_add_sprite = ttk.Button(self.toolbox_frame, text="Add Sprite", command=self.add_sprite)
        btn_add_sprite.pack(pady=5, padx=10, fill=tk.X)
        
        btn_export = ttk.Button(self.toolbox_frame, text="Export to Python", command=self.export_python)
        btn_export.pack(pady=5, padx=10, fill=tk.X)
        
        btn_export_dmg = ttk.Button(self.toolbox_frame, text="Export to DMG", command=self.export_dmg)
        btn_export_dmg.pack(pady=5, padx=10, fill=tk.X)
        
        btn_delete = ttk.Button(self.toolbox_frame, text="Delete Selected", command=self.delete_selected)
        btn_delete.pack(pady=5, padx=10, fill=tk.X)
        
        # Add object list
        self.obj_list_frame = tk.Frame(self.toolbox_frame)
        self.obj_list_frame.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        
        ttk.Label(self.obj_list_frame, text="Objects:").pack(anchor='w')
        
        # Scrollable listbox to show all objects
        listbox_frame = tk.Frame(self.obj_list_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.obj_listbox = tk.Listbox(listbox_frame)
        self.obj_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.obj_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.obj_listbox.yview)
        
        self.obj_listbox.bind('<<ListboxSelect>>', self.on_select_from_list)

    def on_select_from_list(self, event):
        selection = self.obj_listbox.curselection()
        if selection:
            index = selection[0]
            if 0 <= index < len(self.objects):
                self.selected_object = self.objects[index]
                self.selected_index = index
                self.update_property_display()
                self.update_preview()
    
    def create_properties_panel(self):
        properties_inner = tk.Frame(self.properties_frame)
        properties_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create property fields with proper labels
        prop_row = 0
        
        ttk.Label(properties_inner, text="X Position:").grid(row=prop_row, column=0, sticky='w', pady=2)
        self.prop_x = ttk.Entry(properties_inner, width=10)
        self.prop_x.grid(row=prop_row, column=1, sticky='ew', padx=5, pady=2)
        prop_row += 1
        
        ttk.Label(properties_inner, text="Y Position:").grid(row=prop_row, column=0, sticky='w', pady=2)
        self.prop_y = ttk.Entry(properties_inner, width=10)
        self.prop_y.grid(row=prop_row, column=1, sticky='ew', padx=5, pady=2)
        prop_row += 1
        
        ttk.Label(properties_inner, text="Width:").grid(row=prop_row, column=0, sticky='w', pady=2)
        self.prop_width = ttk.Entry(properties_inner, width=10)
        self.prop_width.grid(row=prop_row, column=1, sticky='ew', padx=5, pady=2)
        prop_row += 1
        
        ttk.Label(properties_inner, text="Height:").grid(row=prop_row, column=0, sticky='w', pady=2)
        self.prop_height = ttk.Entry(properties_inner, width=10)
        self.prop_height.grid(row=prop_row, column=1, sticky='ew', padx=5, pady=2)
        prop_row += 1
        
        ttk.Label(properties_inner, text="Image:").grid(row=prop_row, column=0, sticky='w', pady=2)
        self.prop_image = ttk.Entry(properties_inner, state='readonly')
        self.prop_image.grid(row=prop_row, column=1, sticky='ew', padx=5, pady=2)
        prop_row += 1
        
        # Configure column weights
        properties_inner.columnconfigure(1, weight=1)
        
        # Update button
        btn_update = ttk.Button(properties_inner, text="Update Properties", command=self.update_properties)
        btn_update.grid(row=prop_row, column=0, columnspan=2, sticky='ew', pady=10)
        
        # Disable properties initially
        self.clear_properties()

    def clear_properties(self):
        """Clear and disable property fields when no object is selected"""
        self.prop_x.delete(0, tk.END)
        self.prop_y.delete(0, tk.END)
        self.prop_width.delete(0, tk.END)
        self.prop_height.delete(0, tk.END)
        self.prop_image.configure(state='normal')
        self.prop_image.delete(0, tk.END)
        self.prop_image.configure(state='readonly')
        
        # Disable fields when no selection
        if self.selected_object is None:
            self.prop_x.configure(state='disabled')
            self.prop_y.configure(state='disabled')
            self.prop_width.configure(state='disabled')
            self.prop_height.configure(state='disabled')
        else:
            self.prop_x.configure(state='normal')
            self.prop_y.configure(state='normal')
            self.prop_width.configure(state='normal')
            self.prop_height.configure(state='normal')

    def update_property_display(self):
        """Update the property panel with the selected object's values"""
        if self.selected_object:
            # Enable and clear fields
            self.prop_x.configure(state='normal')
            self.prop_y.configure(state='normal')
            self.prop_width.configure(state='normal')
            self.prop_height.configure(state='normal')
            self.clear_properties()
            
            # Set values
            self.prop_x.insert(0, str(self.selected_object['x']))
            self.prop_y.insert(0, str(self.selected_object['y']))
            self.prop_width.insert(0, str(self.selected_object['width']))
            self.prop_height.insert(0, str(self.selected_object['height']))
            
            self.prop_image.configure(state='normal')
            self.prop_image.insert(0, os.path.basename(self.selected_object['path']))
            self.prop_image.configure(state='readonly')

    def add_sprite(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")])
        if file_path:
            try:
                # Load the image with Pygame
                img = pygame.image.load(file_path)
                
                # Create object data
                new_obj = {
                    'x': 100,
                    'y': 100,
                    'width': 50,
                    'height': 50,
                    'image': img,
                    'path': file_path,
                    'rect': pygame.Rect(100, 100, 50, 50),
                    'name': os.path.basename(file_path)
                }
                
                self.objects.append(new_obj)
                # Update objects list
                self.update_object_list()
                
                # Select the new object
                self.selected_object = new_obj
                self.selected_index = len(self.objects) - 1
                self.obj_listbox.selection_clear(0, tk.END)
                self.obj_listbox.selection_set(self.selected_index)
                
                self.update_property_display()
                self.update_preview()
                
            except (pygame.error, IOError) as e:
                messagebox.showerror("Error", f"Could not load image: {e}")

    def update_object_list(self):
        """Update the listbox with current objects"""
        self.obj_listbox.delete(0, tk.END)
        for i, obj in enumerate(self.objects):
            self.obj_listbox.insert(tk.END, f"{i+1}. {obj['name']}")

    def on_canvas_click(self, event):
        """Handle clicking on the canvas to select objects"""
        # Get canvas coordinates
        x, y = event.x, event.y
        
        # Check if clicked on any sprite (in reverse order to select top sprites first)
        for i, obj in reversed(list(enumerate(self.objects))):
            rect = pygame.Rect(obj['x'], obj['y'], obj['width'], obj['height'])
            if rect.collidepoint(x, y):
                self.selected_object = obj
                self.selected_index = i
                self.update_property_display()
                
                # Update listbox selection
                self.obj_listbox.selection_clear(0, tk.END)
                self.obj_listbox.selection_set(i)
                
                self.update_preview()
                return
        
        # If clicked nowhere, deselect
        self.selected_object = None
        self.selected_index = None
        self.clear_properties()
        self.obj_listbox.selection_clear(0, tk.END)
        self.update_preview()

    def update_properties(self):
        """Update the selected object with values from property fields"""
        if self.selected_object is not None and self.selected_index is not None:
            try:
                # Get new values
                new_x = int(self.prop_x.get())
                new_y = int(self.prop_y.get())
                new_width = int(self.prop_width.get())
                new_height = int(self.prop_height.get())
                
                # Validate values (prevent negative dimensions)
                if new_width <= 0 or new_height <= 0:
                    raise ValueError("Width and height must be positive")
                
                # Update object
                self.selected_object['x'] = new_x
                self.selected_object['y'] = new_y
                self.selected_object['width'] = new_width
                self.selected_object['height'] = new_height
                self.selected_object['rect'] = pygame.Rect(new_x, new_y, new_width, new_height)
                
                # Update the preview
                self.update_preview()
                
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid values: {e}")

    def delete_selected(self):
        """Delete the currently selected object"""
        if self.selected_object in self.objects and self.selected_index is not None:
            # Remove from list
            del self.objects[self.selected_index]
            
            # Clear selection
            self.selected_object = None
            self.selected_index = None
            
            # Update UI
            self.update_object_list()
            self.clear_properties()
            self.update_preview()

    def update_preview(self):
        """Redraw all sprites on the canvas"""
        # Clear canvas
        self.canvas.delete("all")
        
        # Draw all objects
        for i, obj in enumerate(self.objects):
            # Draw the image
            try:
                # Scale image for canvas
                img_surface = pygame.transform.scale(obj['image'], (obj['width'], obj['height']))
                img_data = pygame.image.tostring(img_surface, 'RGBA')
                
                # Create PhotoImage from raw data
                from PIL import Image, ImageTk
                pil_img = Image.frombytes('RGBA', (obj['width'], obj['height']), img_data)
                tk_img = ImageTk.PhotoImage(pil_img)
                
                # Keep reference to prevent garbage collection
                obj['tk_img'] = tk_img
                
                # Draw image on canvas
                self.canvas.create_image(obj['x'], obj['y'], image=tk_img, anchor='nw', tags=f"obj{i}")
                
                # Draw selection rectangle if selected
                if obj == self.selected_object:
                    self.canvas.create_rectangle(
                        obj['x'], obj['y'],
                        obj['x'] + obj['width'], obj['y'] + obj['height'],
                        outline='red', width=2, tags=f"sel{i}"
                    )
            except (pygame.error, IOError, AttributeError) as e:
                # Draw placeholder if image can't be rendered
                self.canvas.create_rectangle(
                    obj['x'], obj['y'],
                    obj['x'] + obj['width'], obj['y'] + obj['height'],
                    fill='gray', tags=f"obj{i}"
                )
                self.canvas.create_text(
                    obj['x'] + obj['width']//2, obj['y'] + obj['height']//2,
                    text="Image Error", fill="white", tags=f"err{i}"
                )
        
        # Schedule next update
        self.master.after(100, self.update_preview)

    def export_python(self):
        """Export the game to a Python script"""
        if not self.objects:
            messagebox.showwarning("Warning", "No objects to export")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python files", "*.py")],
            title="Export to Python"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write("import pygame\nimport os\nimport sys\n\n")
                    f.write("def resource_path(relative_path):\n")
                    f.write("    \"\"\"Get absolute path to resource, works for dev and for PyInstaller\"\"\"\n")
                    f.write("    try:\n")
                    f.write("        # PyInstaller creates a temp folder and stores path in _MEIPASS\n")
                    f.write("        base_path = sys._MEIPASS\n")
                    f.write("    except Exception:\n")
                    f.write("        base_path = os.path.abspath('.')\n")
                    f.write("    return os.path.join(base_path, relative_path)\n\n")
                    
                    f.write("def main():\n")
                    f.write("    pygame.init()\n")
                    f.write("    screen = pygame.display.set_mode((600, 400))\n")
                    f.write("    pygame.display.set_caption('My Game')\n")
                    f.write("    clock = pygame.time.Clock()\n")
                    f.write("    running = True\n\n")
                    
                    # Load game objects
                    f.write("    # Load game objects\n")
                    for i, obj in enumerate(self.objects):
                        img_filename = os.path.basename(obj['path'])
                        f.write(f"    img_path{i} = resource_path('{img_filename}')\n")
                        f.write(f"    obj{i}_img = pygame.image.load(img_path{i}).convert_alpha()\n")
                        f.write(f"    obj{i}_img = pygame.transform.scale(obj{i}_img, ({obj['width']}, {obj['height']}))\n")
                        f.write(f"    obj{i}_rect = pygame.Rect({obj['x']}, {obj['y']}, {obj['width']}, {obj['height']})\n\n")
                    
                    # Game loop
                    f.write("    # Game loop\n")
                    f.write("    while running:\n")
                    f.write("        # Handle events\n")
                    f.write("        for event in pygame.event.get():\n")
                    f.write("            if event.type == pygame.QUIT:\n")
                    f.write("                running = False\n\n")
                    
                    f.write("        # Draw everything\n")
                    f.write("        screen.fill((255, 255, 255))\n")
                    
                    for i in range(len(self.objects)):
                        f.write(f"        screen.blit(obj{i}_img, obj{i}_rect)\n")
                    
                    f.write("\n        pygame.display.flip()\n")
                    f.write("        clock.tick(60)\n\n")
                    
                    f.write("    pygame.quit()\n\n")
                    f.write("if __name__ == '__main__':\n")
                    f.write("    main()\n")
                
                # Copy image files to the same directory
                export_dir = os.path.dirname(file_path)
                for obj in self.objects:
                    dest_path = os.path.join(export_dir, os.path.basename(obj['path']))
                    if dest_path != obj['path']:  # Don't copy if already there
                        import shutil
                        shutil.copy2(obj['path'], dest_path)
                
                messagebox.showinfo("Success", f"Game exported to {file_path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {e}")

    def export_dmg(self):
        """Export as macOS application bundle and DMG"""
        # Check if we're on macOS
        if platform.system() != 'Darwin':
            messagebox.showerror("Error", "DMG export is only supported on macOS")
            return
            
        if not self.objects:
            messagebox.showwarning("Warning", "No objects to export")
            return
        
        # First, create Python file
        py_path = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python files", "*.py")],
            title="Save Python File for DMG Export"
        )
        
        if not py_path:
            return  # User cancelled
            
        try:
            # Export Python file first
            self.export_python()
            
            # Create setup.py for py2app
            setup_path = os.path.join(os.path.dirname(py_path), "setup.py")
            with open(setup_path, 'w') as f:
                f.write("from setuptools import setup\n\n")
                f.write(f"APP = ['{os.path.basename(py_path)}']\n")
                f.write("DATA_FILES = [\n")
                
                # Add all image files
                for obj in self.objects:
                    f.write(f"    '{os.path.basename(obj['path'])}',\n")
                
                f.write("]\n\n")
                f.write("OPTIONS = {\n")
                f.write("    'argv_emulation': True,\n")
                f.write("    'packages': ['pygame'],\n")
                f.write("    'excludes': ['numpy', 'scipy', 'matplotlib'],\n")  # Reduce size
                f.write("    'plist': {\n")
                f.write("        'CFBundleName': 'My Game',\n")
                f.write("        'CFBundleDisplayName': 'My Game',\n")
                f.write("        'CFBundleIdentifier': 'com.mygame.app',\n")
                f.write("        'CFBundleVersion': '1.0.0',\n")
                f.write("        'CFBundleShortVersionString': '1.0.0'\n")
                f.write("    }\n")
                f.write("}\n\n")
                f.write("setup(\n")
                f.write("    app=APP,\n")
                f.write("    data_files=DATA_FILES,\n")
                f.write("    options={'py2app': OPTIONS},\n")
                f.write("    setup_requires=['py2app'],\n")
                f.write(")\n")
            
            # Create build script
            build_script = os.path.join(os.path.dirname(py_path), "build_dmg.sh")
            dmg_path = py_path.replace('.py', '.dmg')
            
            with open(build_script, 'w') as f:
                f.write("#!/bin/bash\n\n")
                f.write(f"cd '{os.path.dirname(py_path)}'\n\n")
                f.write("echo 'Cleaning previous builds...'\n")
                f.write("rm -rf build dist\n\n")
                f.write("echo 'Building application with py2app...'\n")
                f.write("python3 setup.py py2app -A\n\n")  # -A for alias mode (faster development)
                f.write("echo 'Creating DMG file...'\n")
                f.write(f"hdiutil create -volname 'My Game' -srcfolder dist/*.app -ov -format UDZO '{dmg_path}'\n\n")
                f.write("echo 'Done! DMG created at {dmg_path}'\n")
            
            # Make executable and run
            os.chmod(build_script, 0o755)
            
            # Show instructions to user
            messagebox.showinfo(
                "DMG Export", 
                f"Setup complete! To build the DMG:\n\n"
                f"1. Open Terminal\n"
                f"2. Run: cd '{os.path.dirname(py_path)}'\n"
                f"3. Run: ./build_dmg.sh\n\n"
                f"This will create: {dmg_path}"
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set up DMG export: {e}")


if __name__ == "__main__":
    # Initialize main window
    root = tk.Tk()
    root.title("macOS Game Editor")
    
    # Check dependencies
    try:
        from PIL import Image, ImageTk
    except ImportError:
        messagebox.showerror(
            "Missing Dependency", 
            "This application requires the Pillow library.\n"
            "Please install it with: pip install pillow"
        )
        root.destroy()
        sys.exit(1)
        
    try:
        import pygame
    except ImportError:
        messagebox.showerror(
            "Missing Dependency", 
            "This application requires Pygame.\n"
            "Please install it with: pip install pygame"
        )
        root.destroy()
        sys.exit(1)
    
    # Start application
    editor = GameEditor(root)
    root.mainloop()
