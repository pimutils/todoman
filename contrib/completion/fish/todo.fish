_TODO_COMPLETE=fish_source todo | source

function __fish_todo_complete_categories
	set -l python (__fish_anypython) || return
	todo --porcelain list | $python -c "
import json
import sys
events = json.load(sys.stdin)
categories = set()
for event in events:
	for category in event['categories']:
		categories.add(category)
print('\n'.join(categories))
"
end
complete -c todo -n "__fish_seen_subcommand_from list" -x -s c -l category -a "(__fish_todo_complete_categories)"

function __fish_todo_complete_statuses
	set -l statuses NEEDS-ACTION CANCELLED COMPLETED IN-PROCESS ANY
	set -l token (commandline -t)

	if string match -qr ^-s -- $token
		set token (string sub -s 3 -- $token)
	end

	set -l complete (string split , -- $token)[1..-2]

	for s in $statuses
		if ! string match -q -- $s $complete
			string join -- , $complete $s
		end
	end
end
complete -c todo -n "__fish_seen_subcommand_from list" -x -s s -l status -a "(__fish_todo_complete_statuses)"
