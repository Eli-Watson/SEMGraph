import cmd
import os
import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go
import pyfiglet
from colorama import Fore, Back, Style, init
import inquirer

# option for colorama to reset the color after each use, otherwise it changes for the entire program
init(autoreset=True)

class CLI(cmd.Cmd):
    prompt = '>> '
    welcome = 'Welcome to the Shell Eco Marathon Graphing (SEMGraph) tool. Type "help" for available commands. By Eli Watson'
    
    # Helper Functions

    def print_banner(self):
        # Create the ASCII banner text using the default "Standard" font
        banner = pyfiglet.figlet_format("SEMGraph", font="standard")
        print(Fore.RED + banner)

    def preloop(self):
        # This method is automatically called before the CmdLoop starts.
        self.print_banner()  
        print(self.welcome)
        print(Fore.WHITE)

    def select_data_file(self):
        """Helper method to handle file selection process using inquirer."""
        print('What Data Directory would you like to list? U for Urban P for Proto or S for Sample data?')

        questions = [
            inquirer.List(
                "Dir",
                message="What Data dir ",
                choices=["Urban", "Proto", "Sample"],
            ),
        ]
        question_dir = inquirer.prompt(questions)["Dir"]
        selected_dir = question_dir
        dir_to_list = ''

        match selected_dir:
            case "Urban":
                dir_to_list = "./Data/Urban/"
            case "Proto":
                dir_to_list = "./Data/Proto/"
            case "Sample":
                dir_to_list = "./Data/Sample/"

        if os.path.exists(dir_to_list):
            files = os.listdir(dir_to_list)
            print(Fore.RED + f"Files in {dir_to_list}:")
        else:
            print(Fore.YELLOW + f"Directory {dir_to_list} does not exist.")
            return None, None

        if files:  # Check if there are files to choose from
            questions_files = [
                inquirer.List(
                    "graph_file",
                    message="Which file would you like to graph?",
                    choices=files,
                ),
            ]
            graphing_source = inquirer.prompt(questions_files)["graph_file"]
            file_path = os.path.join(dir_to_list, graphing_source)

            if not os.path.exists(file_path):
                print(Fore.YELLOW + f"Error: The file '{graphing_source}' does not exist in the directory '{dir_to_list}'")
                return None, None

            return file_path, dir_to_list
        else:
            print(Fore.YELLOW + f"No files found in {dir_to_list}.")
            return None, None

    def generate_graph(self, df, graph_type):
        """Helper method to generate graphs based on user selection."""
        fig = None  # Initialize fig to ensure it's always defined

        if graph_type == 'map':
            print('Generating map...')
            fig = df.plot(x='gps_longitude', y='gps_latitude', color='lap_lap')
        elif graph_type == 'map-flow':
            print('Generating map-flow...')
            fig = df.plot(x='gps_longitude', y='gps_latitude', color='lfm_instantflow', kind='scatter', facet_col='lap_lap', facet_col_wrap=4)
        elif graph_type == 'flow-dist':
            print('Generating flow-dist...')
            fig = df.plot(x='lap_dist', y='lfm_instantflow', color='lap_lap')
        elif graph_type == 'joule-dist':
            print('Generating joule-dist...')
            fig = df.plot(x='lap_dist', y='lap_jm3_netjoule', color='lap_lap')
        elif graph_type == 'speed-dist':
            print('Generating speed-dist...')
            fig = df.plot(x='lap_dist', y='gps_speed', color='lap_lap')
        elif graph_type == 'acel-speed-dotplot':
            print('Generating acel-speed-dotplot...')
            df['acceleration'] = 0.
            df['consumption'] = 0.
            window_len = 30

            for ind in range(window_len, len(df)):
                ind_prev = ind - window_len
                df.loc[ind, 'acceleration'] = (df.loc[ind, 'gps_speed'] - df.loc[ind_prev, 'gps_speed']) / (df.loc[ind, 'obc_timestamp'] - df.loc[ind_prev, 'obc_timestamp'])
                df.loc[ind, 'consumption'] = (df.loc[ind, 'lfm_integratedcorrflow'] - df.loc[ind_prev, 'lfm_integratedcorrflow']) / (df.loc[ind, 'obc_timestamp'] - df.loc[ind_prev, 'obc_timestamp'])

            fig = df.plot.scatter(x='acceleration', y='gps_speed', color='consumption')
        else:
            print(Fore.YELLOW + f"Error: Graph type '{graph_type}' not recognized.")
        
        # Check if fig is still None (no valid graph was generated)
        if fig is not None:
            fig.show()
        else:
            print(Fore.YELLOW + "No valid graph could be generated due to invalid graph type.")

    # Commands 
    def do_quit(self, line):
        """Exit the CLI."""
        print(Fore.RED + "Are you sure you want to quit?")
        confirmquit = input("y or n: ")
        if confirmquit.lower() == "y":
            quit()
        else:
            print("Quit cancelled")

    def do_graph_select(self, line):
        """Generate a specific graph from a list of options."""
        print("Generating Graph...")

        file_path, _ = self.select_data_file()
        if not file_path:
            return
        
        # Read the data
        pd.options.plotting.backend = 'plotly'
        pio.templates.default = 'plotly_dark'
        try:
            df = pd.read_csv(file_path, sep=',', low_memory=False)
            df = df.loc[df['lap_dist'] < 4000]
        except Exception as e:
            print(Fore.YELLOW + f"Error reading CSV file: {e}")
            return

        # Ask for the graph type
        print(Fore.RED + "What graph type would you like to generate?")
        print('')
        print("map: a map of the course using GPS")
        print("map-flow: A GPS map of the track overlayed with data from flow meter")
        print("flow-dist: Flow rate at different distances")
        print("joule-dist: Net amount of energy used at different distances")
        print("speed-dist: Speed at different distances")
        print("acel-speed-dotplot: Dotplot of acceleration, speed and fuel consumption")
        print('')

        questions = [
            inquirer.Checkbox(
                "type",
                message="What Data dir ",
                choices=["map", "map-flow","flow-dist","joule-dist", "speed-dist", "acel-speed-dotplot"]
                ),
        ]
        graph_type = inquirer.prompt(questions)['type']
        self.generate_graph(df, graph_type)

    def do_graph(self, line):
        """Generate standard graphs from the telemetry data."""
        print("Generating Standard Graph Set.")
        
        file_path, _ = self.select_data_file()
        if not file_path:
            return
        
        # Read the data
        pd.options.plotting.backend = 'plotly'
        pio.templates.default = 'plotly_dark'

        try:
            df = pd.read_csv(file_path, sep=',', low_memory=False)
            df = df.loc[df['lap_dist'] < 4000]
        except Exception as e:
            print(Fore.YELLOW + f"Error reading CSV file: {e}")
            return

        # Generate multiple graphs
        print("Generating graphs...")
        self.generate_graph(df, 'map')
        self.generate_graph(df, 'map-flow')
        self.generate_graph(df, 'flow-dist')
        self.generate_graph(df, 'joule-dist')
        self.generate_graph(df, 'speed-dist')
        self.generate_graph(df, 'acel-speed-dotplot')

    def do_settings(self, line):
        """Option to change user settings"""
        print(Fore.RED + 'Settings')
        print('What Setting would you like to change?')
        print('')

if __name__ == '__main__':
    CLI().cmdloop()
