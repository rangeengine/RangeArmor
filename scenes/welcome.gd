extends Control

onready var globals: BGArmorGlobals = $"/root/Globals"


func _ready() -> void:
	OS.set_window_title(ProjectSettings.get_setting("application/config/name"))
	var home_dir = OS.get_environment('HOME')
	$FileDialogNew.current_dir = home_dir
	$FileDialogOpen.current_dir = home_dir
	
	if globals.config.get("LastDir"):
		var dir = Directory.new()
		if dir.dir_exists(globals.config.get("LastDir")):
			$FileDialogNew.current_dir = globals.config.get("LastDir")
			$FileDialogOpen.current_dir = globals.config.get("LastDir")
			
	if globals.config.get("RecentPaths"):
		_add_recent_paths()


# Signal handlers
func _on_ButtonNew_pressed() -> void:
	$FileDialogNew.popup()


func _on_FileDialogNew_file_selected(path: String) -> void:
	var cur_dir: Directory = Directory.new()
	
	if cur_dir.dir_exists(path):
		$AcceptDialog.dialog_text = "A folder with the same name already exists:\n" + path
		$AcceptDialog.popup_centered()
		
	else:
		_create_new_project(path)


func _on_ButtonOpen_pressed() -> void:
	$FileDialogOpen.popup()


func _on_FileDialogOpen_file_selected(path: String) -> void:
	_load_project(path)


func _on_FileDialogOpen_dir_selected(dir: String) -> void:
	_load_project(dir)


func _on_ButtonDocs_pressed() -> void:
	var doc = "https://rangeengine.tech/api/" + globals.RANGE_ENGINE_VERSION + "/html/manual/tutorials/range_armor/index.html"
	var _error = OS.shell_open(doc)


func _on_ButtonSource_pressed() -> void:
	var _error = OS.shell_open("https://github.com/rangeengine/RangeArmor")


func _on_ButtonClearRecent_pressed() -> void:
	var buttons = get_tree().get_nodes_in_group("recent_path")
	
	for b in buttons:
		var button: Button = b
		button.queue_free()
		
	var recent_paths: Array = globals.config.get("RecentPaths", [])
	recent_paths.clear()
	globals.config["RecentPaths"] = recent_paths
	globals.save_config()


func _on_ButtonRecent_pressed(path: String) -> void:
	_load_project(path)


# Abstraction methods
func _validate_data(data: Dictionary) -> bool:
	
	# Validate fields on loaded project
	for key in data.keys():
		if not key in globals.DEFAULT_FIELDS.keys():
			return false
	
	# Add non existent fields to loaded project
	for key in globals.DEFAULT_FIELDS.keys():
		if not key in data.keys():
			data[key] = globals.DEFAULT_FIELDS[key]
	
	return true


func _project_updated(data: Dictionary) -> bool:
	var app_version: int = ProjectSettings.get("global/app_version")
	var project_version: int = data.get("BGArmorVersion", 0)
	
	if not project_version or project_version and project_version < app_version:
		return false
	
	return true


func _update_runtime_files(data: Dictionary):
	var dir: Directory = Directory.new()
	var cur_dir: String = globals.current_project_dir
	var _error = dir.copy(_get_pathfile(dir) + "launcher/launcher.py", cur_dir + "/launcher/launcher.py")
	
	if not _project_updated(data):
		print("X Project outdated with current app version, updating runtime files...")
		
		for file in globals.DEFAULT_PROJECT_FILES:
			if "/Launcher" in file:
				_error = dir.copy(_get_pathfile(dir) + file, cur_dir + "/" + file)
				print("  > Copied file: ", file)
			if "/Launcher.exe" in file:
				_error = dir.copy(_get_pathfile(dir) + file, cur_dir + "/" + file)
				print("  > Copied file: ", file)


func _create_new_project(path: String):
	var dir: Directory = Directory.new()
	
	print("Creating new project at: " + path)
	
	for folder in globals.DEFAULT_PROJECT_FOLDERS:
		var cur_folder = path + "/" + folder
		var _error = dir.make_dir_recursive(cur_folder)
		print("  Created new folder: " + cur_folder)
	
	for file in globals.DEFAULT_PROJECT_FILES:
		var cur_folder = path + "/" + file
		var _error = dir.copy(_get_pathfile(dir) + file, cur_folder)
		print("  Copied file: " + cur_folder)
		
	var _project_name: String = path.split("/")[-1].strip_edges()
	var project_file_path = path + "/launcher/config.json"
	var file = File.new()
	
	if file.open(project_file_path, File.WRITE) == OK:
		file.store_string(JSON.print(globals.DEFAULT_FIELDS))
	file.close()
	
	print("Created new project at: " + project_file_path)
	_load_project(path)

func _get_pathfile(dir: Directory):
	# Try to fix rangearmor in range engine not copy files
	var pathfile = "res://release/"
	# print("Result = ", dir.file_exists("res://release/launcher/launcher.py"))
	if not (dir.file_exists("res://release/launcher/launcher.py")):
		pathfile = "res://rangearmor/release/"
	return pathfile

func _load_project(path: String):
	var cur_dir = path
	path = path + "/launcher/config.json"
	var file = File.new()
	file.open(path, File.READ)
	var file_data = JSON.parse(globals.get_json_no_comments(file.get_as_text()))
	file.close()
	
	if cur_dir:
		globals.config["LastDir"] = cur_dir
		
	globals.add_project_to_recent(cur_dir)
	globals.save_config()
	
	if file_data.error == OK:
		file_data = file_data.result
		
		if _validate_data(file_data):
			globals.current_project_path = path
			globals.current_project_data = file_data
			globals.current_project_dir = cur_dir
			
			_update_runtime_files(file_data)
			
			if not _project_updated(file_data):
				file_data["BGArmorVersion"] = ProjectSettings.get("global/app_version")
			
			var _error = get_tree().change_scene("res://scenes/editor.tscn")
			
		else:
			$AcceptDialog.dialog_text = "Invalid project directory:\n" + cur_dir
			$AcceptDialog.popup_centered()
		
	else:
		$AcceptDialog.dialog_text = "Could not read file:\n" + path
		$AcceptDialog.popup_centered()


func _add_recent_paths():
	var recent_paths = globals.config.get("RecentPaths", [])
	
	for path in recent_paths:
		var dir = Directory.new()
		if dir.dir_exists(path):
			var cur_button = Button.new()
			cur_button.text = path
			cur_button.flat = true
			cur_button.connect("pressed", self, "_on_ButtonRecent_pressed", [path])
			cur_button.add_to_group("recent_path")
			cur_button.self_modulate = Color.dodgerblue
			$Panel/VBoxContainer/HBoxContainer/VBoxContainerRecent.add_child(cur_button)
