#!/usr/bin/python3
#
#cmdchain is meant to combine commands together into a single alias to automate tasks
#
#
#Let the user enter multi-line commands using nano
#Allow them to define variables within those commands
#Save the list of commands into a file
#Whenever "cmdchain run {NAME}" is run, it checks the cmdchain directory for a saved file under the name
#If it finds the file then it runs every line that doesnt start with a "#", "", or "<"

import subprocess
import argparse
from pathlib import Path
import string
from rich import print



#Gets the actual shell of the user instead of /bin/sh which leads to some issues
shell = subprocess.run("echo $SHELL", shell=True, capture_output=True, text=True).stdout.rstrip()
#Line of the custom variable table
varTableLineNumber = 0



#Function used to run a shell command using the actual shell of the user
def run_cmd(command, mode=0):
    if mode == 0:
        subprocess.run(command, shell=True, executable=shell)
    #Returns the output of the file
    elif mode == 1:
        return subprocess.run(command, shell=True, executable=shell, capture_output=True, text=True).stdout.rstrip()


#You can choose from any one of these colors along with adding "bold", "underlined", or "italic" before the color:
#black, red, green, yellow, blue, magenta, cyan, white, purple
#bright_black, bright_red, bright_green, bright_yellow, bright_blue, bright_magenta, bright_cyan, bright_white
file_colors = "[bold bright_blue]"
variable_colors = "[bold bright_magenta]"


cmdchain_directory = run_cmd("echo $HOME", 1) + "/.local/share/cmdchain"
text_editor = "nano"


#The amount of lines to remove when using "cmdchain show (name)", a size of 11 removes all the boilerplate text including the extra space
linesToHide = 11
boilerPlateText = """#Create a cmdchain here
#Use this format for variables: $varName
#To set a custom order for your variables use this format: <var1, var2, var3>
#If you want to use only some variables, exclude them from the custom var table
#
#Example cmdchain:
#<ip, count, file>
#ping -c $count $ip > $file
#echo >> $file
#echo The user $USERNAME ran this command at $(date) >> $file

"""



#This parses the custom variable table and returns a list of all the variables in the table
#If the variable table contains a variable that consists of anything besides characters or numbers it returns None
def parseVarTable(name):
    global varTableLineNumber
    path_to_file = cmdchain_directory + "/" + name
    varTableString = run_cmd("sed -n \'" + str(varTableLineNumber) + "p\' " + path_to_file, 1)
    varTableString = varTableString[1:-1]
    currentVar = ""
    allVars = []
    for char in varTableString:
        if char == ",":
            allVars.append(currentVar)
            currentVar = ""
            continue
        elif char == " ":
            continue
        elif char not in string.ascii_letters and char not in string.digits:
            return None
        currentVar += char
    allVars.append(currentVar)
    return allVars
        



#This function searches through a file line by line and returns a list of all the variables in a file
#A variable is found by looking for a "$" and then storing the trailing characters until it encounters a non letter / digit character
#This function also find the line of the custom variable
#The variable table will be in this format: <var1, var2, var3>
#If the variable table is found, it stops searching for variables and uses the table instead
def getAllVariables(name):
    global varTableLineNumber
    path_to_file = cmdchain_directory + "/" + name
    allVars = []
    inQuotes = False
    collectingVar = False
    escapingChar = False
    currentVar = ""
    lineNumber = 0
    with open(path_to_file, "r") as file:
        for line in file:
            lineNumber += 1
            if line[0] != "#" and line[0].strip():
                #If it finds the variable table, it returns the output of this function
                if line.strip().startswith("<") and line.strip().endswith(">"):
                    varTableLineNumber = lineNumber
                    return parseVarTable(name)
                for char in line:
                    #If it finds a $ inside of single quotes it skips it
                    if char == "'":
                        if inQuotes:
                            inQuotes = False
                        else:
                            inQuotes = True
                    #If it finds a $ and its not inside of '', it starts collecting chars
                    elif char == "$" and not inQuotes:
                        collectingVar = True
                    #If char is " " and is storing chars and currentVar is "$", it doesnt collect it
                    #Imagine a scenario echo $hello$ - it would collect $hello not the trailing $
                    elif char == " " and collectingVar and len(currentVar) == 1:
                        collectingVar = False
                    #If the char is not a character or number, it adds the word to the allVars list
                    elif char not in string.ascii_letters and char not in string.digits and collectingVar:
                        if currentVar in allVars:
                            currentVar = ""
                            collectingVar = False
                            continue
                        allVars.append(currentVar)
                        currentVar = ""
                        collectingVar = False
                    #If storing chars, append the char to the currentVar
                    elif collectingVar:
                        currentVar += char
    return(allVars)




#Prints out the names of all files in the cmdchain directory with their required variables
def print_show_message():
    file_names = [file.name for file in Path(cmdchain_directory).iterdir() if file.is_file()]
    for file in file_names:
        variablesInFile = getAllVariables(file)
        if not variablesInFile or variablesInFile[0] == "":
            print(file_colors + file + "[/" + file_colors[1:])
            print("Variables : " + variable_colors + "None" + "[/" + variable_colors[1:])
            #Use this print statement instead to not have "None" italicized, it also needs to be changed in the cmd_show function
        else:
            print(file_colors + file + "[/" + file_colors[1:])
            print("Variables : ", end="")
            for i in range(len(variablesInFile)):
                if i == len(variablesInFile) - 1:
                    print(variable_colors + variablesInFile[i] + "[/" + variable_colors[1:])
                    continue
                print(variable_colors + variablesInFile[i] + "[/" + variable_colors[1:] + ", ", end="")
            





#If no arguments are passed in, it lists the cmdchain directory
#If an argument is passed in, it checks if it exists in the cmdchain directory
#If an argument is passed in and it exists, it lists file name and the required variables with their respective colors
def cmd_show(name):
    if name is None:
        print_show_message()
    elif not Path(cmdchain_directory + "/" + name).is_file():
        print("This cmdchain doesnt exist, consider creating one")
    else:
        path_to_file = cmdchain_directory + "/" + name
        #cuts off the first 11 lines(boiler plate text) from any cmdchain file
        variablesInFile = getAllVariables(name)
        print(file_colors + name + "[/" + file_colors[1:])
        print("Variables : ", end="")
        if not variablesInFile or variablesInFile[0] == "":
            print(variable_colors + "None" + "[/" + variable_colors[1:])
            variablesInFile = []
        for i in range(len(variablesInFile)):
            if i == len(variablesInFile) - 1:
                print(variable_colors + variablesInFile[i] + "[/" + variable_colors[1:])
                continue
            print(variable_colors + variablesInFile[i] + "[/" + variable_colors[1:] + ", ", end="")
        print("\n----------CMDCHAIN----------")
        if varTableLineNumber == 0:
            run_cmd("tail -n +" + str(linesToHide + 1) + " " + cmdchain_directory + "/" + name)
        else:
            run_cmd("sed \'" + str(varTableLineNumber) + "d\' " + path_to_file + " | tail -n +" + str(linesToHide + 1))
        print("----------CMDCHAIN----------")





#If the file exists, it says cmdchain already created and exits
#Else, it creates a file with the name in the cmdchain directory with the boilerplate text and opens an editor
def cmd_create(name):
    path_to_file = cmdchain_directory + "/" + name
    if Path(path_to_file).is_file():
        print("cmdchain already created, consider editing")
    else: 
        with open(path_to_file, "w") as file:
            file.write(boilerPlateText)
        run_cmd(text_editor + " " + path_to_file)







#If the file exists, open text editor
#If the file doesnt exist, say you need to create one first then exit
def cmd_edit(name):
    path_to_file = cmdchain_directory + "/" + name
    if Path(path_to_file).is_file():
        run_cmd(text_editor + " " + path_to_file)
    else:
        print("This cmdchain doesnt exist, consider creating one")
        




#If the cmdchain doesnt exist by that name it exits
#If it encounters a variable in the variable table that consist of something other than letters or numbers
#IF there is a mismiatch of variables then it returns the usage with the right amoun tof variables
#For every line that doesnt start with a "#", "", or "<" it replaces the line with every argument passed in
#It then executes the line with all the variables substituted
def cmd_run(name, args):
    global varTableLineNumber
    path_to_file = cmdchain_directory + "/" + name
    if not Path(path_to_file).is_file():
        print("This cmdchain doesnt exist, consider creating one")
        return
    variablesInFile = getAllVariables(name)
    if variablesInFile is None and varTableLineNumber != 0:
        print("Variables declared in the variable table must consist of only letters and numbers")
        return
    if not variablesInFile or variablesInFile[0] == "":
        variablesInFile = []
    if len(variablesInFile) != len(args):
        scriptName = Path(__file__).name
        if len(variablesInFile) == 0:
            print("usage: " + scriptName + " run " + name)
            return
        print("usage: " + scriptName + " run " + name + " -a/--args ", end="")
        for arg in variablesInFile:
            print("[not bold white](" + arg + ")[/not bold white] ", end="")
        print() 
        return
    with open(path_to_file, "r") as file:
        for line in file:
            if line[0] != "#" and line[0].strip() and line[0] != "<":
                tempLine = line.strip()
                for i in range(len(args)):
                    tempLine = tempLine.replace("$" + variablesInFile[i], args[i])
                run_cmd(tempLine)




#If the file exists, it keeps the user in a while loop until they answer y/n to remove
#Else it prints the file doesnt exist and exits
def cmd_remove(name):
    path_to_file = cmdchain_directory + "/" + name
    if Path(path_to_file).is_file():
        while True:
            choice = input("Are you sure you want to delete this cmdchain? [Y/n]: ").lower()
            if choice == "y":
                run_cmd("rm " + path_to_file)
                return
            elif choice == "n":
                return
    else:
        print("This cmdchain doesn't exist")



#If the file exists, it keeps the user in a while loop until they answer y/n to rename
#If file doesnt exist and says that the file doesnt exist and exits
def cmd_rename(name, newName):
    path_to_file = cmdchain_directory + "/" + name
    path_to_newFile = cmdchain_directory + "/" + newName
    if Path(path_to_file).is_file():
        while True:
            choice = input("Are you sure you want to rename this cmdchain? [Y/n]: ").lower()
            if choice == "y":
                run_cmd("mv " + path_to_file + " " + path_to_newFile)
                return
            elif choice == "n":
                return
    else:
        print("This cmdchain doesn't exist")




#It initializes all the parses from arg parse to have pretty error messages and usages
def main():
    run_cmd("mkdir -p " + cmdchain_directory)
    parser = argparse.ArgumentParser(description="A script used to automate the process of running multiple commands")
    subparsers = parser.add_subparsers(dest="action", metavar="")

    #Show
    parser_show = subparsers.add_parser("show", help="Show an existing cmdchain")
    parser_show.add_argument("name", metavar="NAME", nargs="?", help="Name of the cmdchain to show")
    parser_show.set_defaults(func=cmd_show, subparser=parser_show)

    #Create
    parser_create = subparsers.add_parser("create", help="Create a new cmdchain")
    parser_create.add_argument("name", metavar="NAME", nargs="?", help="Name of the cmdchain to create")
    parser_create.set_defaults(func=cmd_create, subparser=parser_create)

    #Edit
    parser_edit = subparsers.add_parser("edit", help="Edit an existing cmdchain")
    parser_edit.add_argument("name", metavar="NAME", nargs="?", help="Name of the cmdchain to edit")
    parser_edit.set_defaults(func=cmd_edit, subparser=parser_edit)

    #Run
    parser_run = subparsers.add_parser("run", help="Run an existing cmdchain", usage="%(prog)s NAME [-a ARGS ...]")
    parser_run.add_argument("name", metavar="NAME", nargs="?", help="Name of the cmdchain to run")
    parser_run.add_argument("-a", "--args", nargs="*", default=[], help="Arguments to pass into the cmdchain")
    parser_run.set_defaults(func=cmd_run, subparser=parser_run)

    #Remove
    parser_remove = subparsers.add_parser("remove", help="Remove an existing cmdchain")
    parser_remove.add_argument("name", metavar="NAME", nargs="?", help="Name of the cmdchain to remove")
    parser_remove.set_defaults(func=cmd_remove, subparser=parser_remove)

    #Rename
    parser_rename = subparsers.add_parser("rename", help="Rename an existing cmdchain")
    parser_rename.add_argument("CurrentName", metavar="NAME", nargs="?", help="Name of the cmdchain to rename")
    parser_rename.add_argument("NewName", metavar="NEW_NAME", nargs="?", help="New name of the cmdchain")
    parser_rename.set_defaults(func=cmd_rename, subparser=parser_rename)


    args = parser.parse_args()

    if args.action is None:
        parser.print_help()
        return



    #Print the help message if missing an argument after the action argument so: cmdchain (action) (this)
    #Dont do it if the action is show or rename since show can have 0 arguments and rename has a "CurrentName" attribute instead of a "Name" attribute
    if getattr(args, "name", None) is None and (args.action != "show" and args.action != "rename"):
        args.subparser.print_help()
        return
    if args.action == "rename":
        if getattr(args, "CurrentName", None) is None or getattr(args, "NewName", None) is None:
            args.subparser.print_help()
            return
        args.func(getattr(args, "CurrentName", None), getattr(args, "NewName", None))
        return
    if args.action == "run":
        args.func(getattr(args, "name", None), getattr(args, "args", None))
        return
    
    args.func(getattr(args, "name", None))


if __name__ == "__main__":
    main()
