import gvgen


# Walk the control flow graph to discover all possible edges.
# In cases where we can't determine the jump destination,
# the jump is considered to go to a special "[anywhere]" block
def generate_graph(blocks):
	known_edges = []
	
    # Blocks that have an outgoing edge to the "[anywhere]" block.
	anywhere_edges = []
	
    # List of execution paths that we have already explored or that are registered to be explored in `exe_paths`
	registered_paths = [[blocks[0]]]
	
    # List of possible execution paths to be explored. Each execution path consists of the known stack and the list of visited blocks.
	exe_paths = [([],[blocks[0]])]
	
    # Add an outgoing edge to `a` if it doesn't have one already
	def new_edge_to_anywhere(a, existing):
		if not a in existing:
			anywhere_edges.append(a)
	
	# Create a new path based on the given `path` and the block `b`.
	def try_new_edge(path, b, edges, exe_paths, stack):
    	# Add the corresponding edge to the graph if it doesn't exist yet.
		if not (path[-1], b) in edges:
			edges.append((path[-1],b))

		# Check for recursive situations
		if b in path:
        	# If we are in a recursive situation, continue the analysis without making assumptions about the stack contents
			if not [b] in registered_paths:
				registered_paths.append([b])
				exe_paths.append(([],[b]))
			return
		
    	# Create a copy of the path to avoid modifying the original reference
		new_path = path.copy()
		new_path.append(b)
		
   		 # Register the new path for further exploration if it hasn't been explored yet.
		if not new_path in registered_paths:
			registered_paths.append(new_path)
			new_stack = path[-1].stack_mapping.apply_mapping(stack)
			exe_paths.append((new_stack, new_path))
	
	# Explore all possible paths
	while len(exe_paths) > 0:
    	# Take the next path for analysis
		stack, path = exe_paths.pop()
		block = path[-1]
    	# If the block can perform a jump, determine the jump destination
		if block.can_jump:
			if block.jump_dest != None:
				try_new_edge(path, blocks[block.jump_dest], known_edges, exe_paths, stack)
			elif block.jump_dest_stack_index != None and block.jump_dest_stack_index + 1 <= len(stack):
				# If the jump destination is not known, but there's a reference to a stack item, check if we have the value
				if stack[-block.jump_dest_stack_index-1] != None:
					# If we do, we have our jump destination
					try_new_edge(path, blocks[int.from_bytes(stack[-block.jump_dest_stack_index-1], "big")], known_edges, exe_paths, stack)
				else:
					new_edge_to_anywhere(block, anywhere_edges)
			else:
				new_edge_to_anywhere(block, anywhere_edges)

   		# Check if the block can fall through, and if the fall through address is valid
		if block.can_falltrough and blocks.get(block.falltrough_addr) != None:
			try_new_edge(path, blocks[block.falltrough_addr], known_edges, exe_paths, stack)
	
	# Create the graph from the collected data
	g = gvgen.GvGen()
	
	# Create a node for edges going to [anywhere] if necessary
	if len(anywhere_edges) > 0:
		anywhere = g.newItem("[anywhere]")
	
	# Create a node for each block in the graph
	graph_blocks = {}
	for offset, block in blocks.items():
		graph_blocks[offset] = g.newItem(block.as_text())
	
	# Add edges to [anywhere] if necessary
	for block in anywhere_edges:
		g.newLink(graph_blocks[block.start_addr], anywhere)
	
	# Add regular edges
	for from_block, to_block in known_edges:
		g.newLink(graph_blocks[from_block.start_addr], graph_blocks[to_block.start_addr])
	
	return g
