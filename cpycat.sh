#!/bin/bash
print_usage_message() {
	echo "Usage: $0 [OPTIONS] (files)/(strings)"
	echo ""
	echo "A tool used to copy the contents of file or a string into your clipboard"
	echo ""
	echo "options:"
	echo "  -s, --string"
	echo "	Forces cpycat to treat the argument as a string"
	echo "  -f, --file"
	echo "	Forces cpycat to treat the argument as a file"
	echo "  -h, --help"
	echo "	Shows this message and exits"
	exit 1
}

#If no argument is provided it prints the usage information
if [[ -z $1 ]]; then
	print_usage_message
fi

force_string=false
force_file=false
to_copy=""

while [[ $# -gt 0 ]]; do
	case "$1" in
		-h|--help)
			print_usage_message
			;;
		-s|--string)
			force_string=true
			shift
			;;
		-f|--file)
			force_file=true
			shift
			;;
		-*)
			print_usage_message
			;;
		*)
			if [[ -z $to_copy ]]; then
				to_copy=$1
			else
				to_copy="$to_copy $1"
			fi
			shift
			;;
	esac
done

#If 2 arguments are passed, it uses the else block
if $force_file || [[ -f "$to_copy" ]] && ! $force_string; then
	cat $to_copy | xclip -r -selection clipboard
else
	echo "$to_copy" | xclip -r -selection clipboard
fi
