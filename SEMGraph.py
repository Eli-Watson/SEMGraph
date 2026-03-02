#!/usr/bin/env python
#  ____  _____ __  __  ____                 _
# / ___|| ____|  \/  |/ ___|_ __ __ _ _ __ | |__
# \___ \|  _| | |\/| | |  _| '__/ _` | '_ \| '_ \
#  ___) | |___| |  | | |_| | | | (_| | |_) | | | |
# |____/|_____|_|  |_|\____|_|  \__,_| .__/|_| |_|
#                                    |_|
# Shell Eco Marathon Graphing Tool
# By Eli Watson
# my attempt at a cli python program - Eli Watson 4/3/25 (Comp Softmore Year)
# I hope that this script is helpful in making graphs to interpret the telemetry data put out by shell.
# Special Thanks to Marcus Schmitd from Schmitd Elektronik for helping me learn all this and all the work they have done for SEM
# https://schmid-elektronik.ch/racebootcamp/
# https://telemetry.sem-app.com/wiki/doku.php/telemetry_data/channel_descriptions

import cmd
import os

import inquirer
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import pyfiglet
from colorama import Fore, init

# option for colorama to reset the color after each use, otherwise it changes for the entire program
init(autoreset=True)

class CLI(cmd.Cmd):
    #These are the graphs avalable to be used, by both graph_and graph select.
    ENGINE_AGNOSTIC_GRAPHS = ["Map","Speed-Dist",]
    ICE_GRAPHS = ["Map-Flow","Flow-Dist","Acel-Speed-Dotplot","CorrFlow-Dist",]
    BE_GRAPHS = ["Joule-Dist","Joule-map","Current-Dist",]
    
    prompt = ">> "
    welcome = "Welcome to the Shell Eco Marathon Graphing (SEMGraph) tool. By Eli Watson, Bearcat Motorsports"

    # Helper Functions
    def print_banner(self):
        banner = pyfiglet.figlet_format("SEMGraph", font="standard")
        print(Fore.RED + banner)

    def preloop(self):
        # This method is automatically called before the CmdLoop starts.
        self.print_banner()
        print(self.welcome)
        print('Type "Help" for a list of available options')

    def select_data_file(self):
        base_data_dir = "./Data/"

        if not os.path.exists(base_data_dir):
            print(Fore.YELLOW + f"Base data directory '{base_data_dir}' does not exist.")
            return None, None
    
        # Get only folders inside ./Data/
        data_dirs = [
            d for d in os.listdir(base_data_dir)
            if os.path.isdir(os.path.join(base_data_dir, d))
        ]
    
        if not data_dirs:
            print(Fore.YELLOW + "No data directories found inside ./Data/")
            return None, None

        # Prompt user to select a directory
        questions = [
            inquirer.List(
                "Dir",
                message=Fore.RED + "Select a data directory:",
                choices=data_dirs,
            ),
        ]
    
        selected_dir = inquirer.prompt(questions)["Dir"]
        dir_to_list = os.path.join(base_data_dir, selected_dir)

        print(Fore.RED + f"Listing files in {dir_to_list}:")
    
        files = self.list_files_recursive(dir_to_list)
    
        if not files:
            print(Fore.YELLOW + f"No files found in {dir_to_list}.")
            return None, None
    
        # Prompt user to select a file
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
            print(
                Fore.YELLOW
                + f"Error: The file '{graphing_source}' does not exist in '{dir_to_list}'"
            )
            return None, None

        return file_path, dir_to_list

    def list_files_recursive(self, dir_path):
        """Recursively lists all files in a directory and its subdirectories."""
        all_files = []

        for root, dirs, files in os.walk(dir_path):
            for file in files:
                # Append the full relative path of each file found
                relative_path = os.path.relpath(os.path.join(root, file), dir_path)
                all_files.append(relative_path)

        return all_files

    # These are the actual graphs being generated
    def generate_graph(self, df, graph_type):
        """Helper method to generate graphs based on user selection."""
        match graph_type:
            case "Map":
                print("Generating map...")
                fig = df.plot(x="gps_longitude", y="gps_latitude", color="lap_lap")

            case "Speed-Dist":
                print("Generating speed-dist...")
                fig = df.plot(x="lap_dist", y="gps_speed", color="lap_lap")

            case "Map-Flow":
                print("Generating map-flow...")
                fig = df.plot(
                    x="gps_longitude",
                    y="gps_latitude",
                    color="lfm_instantflow",
                    kind="scatter",
                    facet_col="lap_lap",
                    facet_col_wrap=4,
                )

            case "Flow-Dist":
                print("Generating flow-dist...")
                fig = df.plot(x="lap_dist", y="lfm_instantflow", color="lap_lap")

            # this one has dosen't just use data straigh from the file, it caculates accel and conspuption for a unique graph
            case "Acel-Speed-Dotplot":
                print("Generating acel-speed-dotplot...")
                df["acceleration"] = 0.0
                df["consumption"] = 0.0
                window_len = 30

                for ind in range(window_len, len(df)):
                    ind_prev = ind - window_len
                    df.loc[ind, "acceleration"] = (
                        df.loc[ind, "gps_speed"] - df.loc[ind_prev, "gps_speed"]
                    ) / (
                        df.loc[ind, "obc_timestamp"] - df.loc[ind_prev, "obc_timestamp"]
                    )
                    df.loc[ind, "consumption"] = (
                        df.loc[ind, "lfm_integratedcorrflow"]
                        - df.loc[ind_prev, "lfm_integratedcorrflow"]
                    ) / (
                        df.loc[ind, "obc_timestamp"] - df.loc[ind_prev, "obc_timestamp"]
                    )

                fig = df.plot.scatter(
                    x="acceleration", y="gps_speed", color="consumption"
                )

            case "CorrFlow-Dist":
                print("Generating CorrFlow-Dist")
                fig = df.plot(
                    x="lap_dist", y="lap_lfm_integratedcorrflow", color="lap_lap"
                )

            case "Joule-Dist":
                print("Generating joule-dist...")
                fig = df.plot(x="lap_dist", y="lap_jm3_netjoule", color="lap_lap")

            case "Joule-map":
                print("Generating Joule-map...")
                fig = df.plot(x="gps_longitude",y="gps_latitude",color="jm3_current",kind="scatter",facet_col="lap_lap",facet_col_wrap=4,)

            case "Current-Dist":
                print("Generating Current-dist...")
                fig = df.plot(x="lap_dist", y="jm3_current", color="lap_lap")

            case _:
                print(Fore.YELLOW + f"Graph type '{graph_type}' is not recognized.")
                return

        fig.show()

    # Commands
    def do_quit(self, line):
        """Exit the CLI."""
        print(Fore.RED + "Are you sure you want to quit?")
        confirmquit = input("y or n: ")
        if confirmquit.lower() == "y":
            quit()
        else:
            print("Quit cancelled")

    def do_list_graphs(self, line):
        """List all avalibel Graphs"""
        print(Fore.RED + "Avalible Graphs")
        print("")
        print("ENGINE AGNOSTIC GRAPHS:")
        print(self.ENGINE_AGNOSTIC_GRAPHS )
        print("BATTERY ElECTRIC GRAPHS:")
        print(self.BE_GRAPHS)
        print("INTERNAL COMBUSTION GRAPHS:")
        print(self.ICE_GRAPHS)

    def do_graph_select(self, line):
        """Generate a specific graph from a filtered list of options."""
        print("Generating Graph...")

        file_path, _ = self.select_data_file()
        if not file_path:
            return

        # Read CSV
        pd.options.plotting.backend = "plotly"
        pio.templates.default = "plotly_dark"

        try:
            df = pd.read_csv(file_path, sep=",", low_memory=False)
            df = df.loc[df["lap_dist"] < 4000]
        except Exception as e:
            print(Fore.YELLOW + f"Error reading CSV file: {e}")
            return

        # Select Engine Type
        engine_question = [
            inquirer.List(
                "engine",
                message=Fore.RED + "Select Engine Type",
                choices=["ICE", "BE"],
            )
        ]
    
        engine_type = inquirer.prompt(engine_question)["engine"]
    
        # Filter graph list
        if engine_type == "ICE":
            graph_choices = self.ENGINE_AGNOSTIC_GRAPHS + self.ICE_GRAPHS
        else:
            graph_choices = self.ENGINE_AGNOSTIC_GRAPHS + self.BE_GRAPHS

        # Select Graph
        questions = [
            inquirer.List(
                "type",
                message=Fore.RED + "Select a Graph",
                choices=graph_choices,
            ),
        ]

        graph_type = inquirer.prompt(questions)["type"]
    
        self.generate_graph(df, graph_type)
    
    def do_graph(self, line):
        """Generate standard graphs from the telemetry data."""
        print("Generating Standard Graph Set.")

        file_path, _ = self.select_data_file()
        if not file_path:
            return

        pd.options.plotting.backend = "plotly"
        pio.templates.default = "plotly_dark"

        try:
            df = pd.read_csv(file_path, sep=",", low_memory=False)
            df = df.loc[df["lap_dist"] < 4000]
        except Exception as e:
            print(Fore.YELLOW + f"Error reading CSV file: {e}")
            return

        # Engine selection
        engine_question = [
            inquirer.List(
                "engine",
                message=Fore.RED + "Select Engine Type",
                choices=["ICE", "BE"],
            )
        ]

        engine_type = inquirer.prompt(engine_question)["engine"]
        print("Generating graphs...")

    # Engine agnostic always runs
        for graph in self.ENGINE_AGNOSTIC_GRAPHS:
            self.generate_graph(df, graph)

    # Engine specific
        if engine_type == "ICE":
            for graph in self.ICE_GRAPHS:
                self.generate_graph(df, graph)
        else:
            for graph in self.BE_GRAPHS:
                self.generate_graph(df, graph)

# Actually calls and runs the program
if __name__ == "__main__":
    CLI().cmdloop()


