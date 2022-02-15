extends Node

const DEFAULT_CONFIG: Dictionary = {
	"LastDir": "",
	"RecentPaths": [],
}

const DEFAULT_FIELDS: Dictionary = {
	"GameName": "Game",
	"Version": "0.0.1",
	"MainFile": "Game.blend",
	"DataFile": "./data.dat",
	"DataSource": "./data",
	"DataChunkSize": 32,
	"Persistent": [
		"*.bgeconf",
		"*.sav"
	],
	"Ignore": [
		"*.pyc",
		"*.blend1"
	]
}

onready var current_project_path: String = ""
onready var current_project_data: Dictionary = {}
onready var config: Dictionary = {}


func _ready() -> void:
	load_config()


func load_config():
	var config_path = OS.get_user_data_dir() + "/config.json"
	var config_file = File.new()
	
	if config_file.open(config_path, File.READ) == OK:
		config = JSON.parse(config_file.get_as_text()).result
		print("Loaded config from", config_path)
		
	else:
		config = JSON.parse(JSON.print(DEFAULT_CONFIG)).result
		save_config()
	
	config_file.close()


func save_config():
	var config_path = OS.get_user_data_dir() + "/config.json"
	var config_file = File.new()
	
	if config_file.open(config_path, File.WRITE) == OK:
		
		if config_file.file_exists(config_path):
			config_file.store_string(JSON.print(config))
			print("Created new config in " + config_path)
			
		else:
			config_file.store_string(JSON.print(DEFAULT_CONFIG))
			print("Saved config to " + config_path)
			
	else:
		print("Could not create config file at " + config_path)


func get_json_no_comments(json: String) -> String:
	var lines = json.split("\n")
	var finalJson = ""
	
	for line in lines:
		line = line.strip_edges()
		
		if not line.begins_with("//"):
			finalJson += line
			
	return finalJson

