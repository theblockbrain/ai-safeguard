# Class for performing basic stack dataflow analysis.
# It is used to predict jump destinations and track the immediate values of PUSH operations.
class StackMapping:
	def __init__(self, ops):
        # Number of preexisting stack items popped by the operations.
		self.num_poped = 0
		
        # List of items pushed onto the stack. After executing the operations, the stack will be the preexisting stack 
        # with `self.numpoped` items popped from it and the items in `self.pushed` pushed onto it. Each item in this
        # list can be None (unknown value), a bytes value (representing a literal and statically known stack item) 
        # or an int (representing a copy of a preexisting stack item: 0 means the topmost preexisting stack item, 
        # 1 means the 2nd topmost item, etc.)
		self.pushed = []
		
        # Index (in the `ops` list) of the instruction at which any given stack item was created (DUPs and SWAPs 
        # do not count as creation). Each entry corresponds to the stack item at the same index in `self.pushed`.
        # Always has the same length as `self.pushed`.
		self.creation_op_idx = []
		
        # Mapping of instruction indices to usage types of the values produced by the instruction. Used for operand 
        # normalization {op_idx: ["ArithData", "LogicData", ...]}
		self.value_usage_type = {}
		
		# Helper function that adds the `category` to the usage type list of the instruction index
		# that produced the inputs to the instruction if `op` is one of the `ops`
		def operant_categorization(category, ops, op, stack_op_idx, usage_map):
			if op.name in ops:     # Check if the operation matches
       			 # Iterate over the instruction's inputs
				for stack_idx in range(len(stack_op_idx)-min(len(stack_op_idx), op.pops),len(stack_op_idx)):
            		# Skip if we don't know where the value came from
					if stack_op_idx[stack_idx] != None:
               			 # Initialize the usage map if it doesn't have an entry for the instruction
						if usage_map.get(stack_op_idx[stack_idx]) == None:
							usage_map[stack_op_idx[stack_idx]] = []
               			# Add the category if it isn't registered already
						if not category in usage_map[stack_op_idx[stack_idx]]:
							usage_map[stack_op_idx[stack_idx]].append(category)
		
		for op_idx, op in enumerate(ops):
			# Categorize the operands of various instructions into various categories
			operant_categorization("ArithData", ["ADD", "MUL", "SUB", "EXP", "SIGNEXTEND"], op, self.creation_op_idx, self.value_usage_type)
			operant_categorization("BlockData", ["BLOCKHASH", "COINBASE", "TIMESTAMP", "NUMBER"], op, self.creation_op_idx, self.value_usage_type)
			operant_categorization("LogicData", ["LT", "GT", "SLT", "SGT", "EQ", "ISZERO"], op, self.creation_op_idx, self.value_usage_type)
			operant_categorization("MemData", ["MLOAD"], op, self.creation_op_idx, self.value_usage_type)
			operant_categorization("StorData", ["SLOAD"], op, self.creation_op_idx, self.value_usage_type)
			operant_categorization("BitData", ["BYTE", "SHL", "SHR", "SAR", "AND", "OR", "XOR", "NOT"], op, self.creation_op_idx, self.value_usage_type)
			
			# Simulating the effects of stack-modifying operations
			if op.name[:4] == "PUSH":
				self.push(op.bytes[1:], op_idx)
			elif op.name == "POP":
				self.pop()
			elif op.name[:3] == "DUP":
				self.dup_n(int(op.name[3:]))
			elif op.name[:4] == "SWAP":
				self.swap_n(int(op.name[4:]))
			else:
				self.misc_op(op, op_idx)
	
	def push(self, value, op_idx):
		"""
		 Adds the value and the instruction index that created the value to the stack
		"""
		self.pushed.append(value)
		self.creation_op_idx.append(op_idx)
	
	def pop(self):
		"""
		Removes the topmost value from the stack.
		If there are no values pushed by the current list of operations left,
		it increases the number of values that have been popped from the pre-existing stack.
		"""
		if len(self.pushed) == 0:
			self.num_poped += 1
		else:
			self.pushed.pop()
			self.creation_op_idx.pop()
	
	def dup_n(self, n):
		"""
		Duplicates the n-th item from the top of the stack and pushes it to the top.
		"""
		if n <= len(self.pushed):
			# If we're duplicating a value we've pushed to the stack ourselves, we can just
			# copy the origin info and the value.
			self.pushed.append(self.pushed[-n])
			self.creation_op_idx.append(self.creation_op_idx[-n])
		else:
			# If we're duplicating a value from the pre-existing stack, we store a back-reference
			# for the value and add 'None' for the creation_op_idx to indicate that
			# we don't know where the value originally came from.
			self.pushed.append(n - len(self.pushed) - 1 + self.num_poped)
			self.creation_op_idx.append(None)
	
	def swap_n(self, n):
		"""
		Swaps the topmost item on the stack with the n-th item from the top.
		"""
		# If we're swapping with a stack item that we haven't pushed ourselves, 
		# we have to pop more values from the original stack and pretend we pushed them
		# right back on so that they are in the order as they were originally.
		if len(self.pushed) < n + 1:
			for x in range((n + 1) - len(self.pushed)):
				self.pushed.insert(0, self.num_poped)
				self.creation_op_idx.insert(0, None)
				self.num_poped += 1
		
		# Swap the value and creation index of the topmost item with the n-th item
		# counted from the top down (n=1 means swap the topmost with the 2nd topmost)
		self.pushed[-1], self.pushed[-1-n] = self.pushed[-1-n], self.pushed[-1]
		self.creation_op_idx[-1], self.creation_op_idx[-1-n] = self.creation_op_idx[-1-n], self.creation_op_idx[-1]
	
	def misc_op(self, op, op_idx):
		"""
        Simulates the stack operations of any operations, treats the output
        value(s) as unknown, except for arithmetic operations if the inputs are known.
        """
		# Number of items to pop from the stack
		pops = op.pops
		# Number of items to push to the stack
		pushes = op.pushes
		out_value = None

		# See <https://ethereum.github.io/yellowpaper/paper.pdf> page 30
		# Check the operation name and perform corresponding stack operation
		if op.name == "NOT":
			# Check if there is at least one item on the stack and if it is bytes
			if len(self.pushed) >= 1 and isinstance(self.pushed[-1], bytes):
				out_value = (int.from_bytes(self.pushed[-1], "big", signed=False) ^ ((2**256)-1)).to_bytes(32, "big")
		elif op.name in ["ADD", "MUL", "SUB", "DIV", "SDIV", "MOD", "SMOD", "EXP", "SIGNEXTEND", "AND", "OR", "XOR", "BYTE", "SHL", "SHR", "SAR"]:
        	# Check if there are at least two items on the stack and if they are bytes
			if len(self.pushed) >= 2 and isinstance(self.pushed[-1], bytes) and isinstance(self.pushed[-2], bytes):
				lhs_u = int.from_bytes(self.pushed[-1], "big", signed=False)
				rhs_u = int.from_bytes(self.pushed[-2], "big", signed=False)
				lhs_i = int.from_bytes(self.pushed[-1], "big", signed=True)
				rhs_i = int.from_bytes(self.pushed[-2], "big", signed=True)
				if op.name == "ADD":
					out_value = ((lhs_u + rhs_u) % 2**256).to_bytes(32, "big")
				elif op.name == "MUL":
					out_value = ((lhs_u * rhs_u) % 2**256).to_bytes(32, "big")
				elif op.name == "SUB":
					out_value = ((lhs_u - rhs_u) % 2**256).to_bytes(32, "big")
				elif op.name == "DIV":
					if rhs_u == 0:
						out_value = (0).to_bytes(32, "big")
					else:
						out_value = (lhs_u // rhs_u).to_bytes(32, "big")
				elif op.name == "SDIV":
					if rhs_i == 0:
						out_value = (0).to_bytes(32, "big", signed=True)
					elif lhs_i == (-2 ** 255) and rhs_i == -1:
						out_value = (-2 ** 255).to_bytes(32, "big", signed=True)
					else:
						out_value = (lhs_i // rhs_i).to_bytes(32, "big", signed=True)
				elif op.name == "MOD":
					if rhs_u == 0:
						out_value = (0).to_bytes(32, "big")
					else:
						out_value = (lhs_u % rhs_u).to_bytes(32, "big")
				elif op.name == "SMOD":
					if rhs_i == 0:
						out_value = (0).to_bytes(32, "big")
					else:
						out_value = (lhs_i % rhs_i).to_bytes(32, "big", signed=True)
				elif op.name == "EXP":
					out_value = pow(lhs_u, rhs_u, 2**256).to_bytes(32, "big")
				elif op.name == "SIGNEXTEND":
					out_value = 0
					for i in range(0,256):
						if i <= (256-8*(lhs_u+1)):
							out_value += ((rhs_u >> (255-(256-8*(lhs_u+1)))) & 1) << (255 - i)
						else:
							out_value += ((rhs_u >> (255-i)) & 1) << (255 - i)
					out_value = out_value.to_bytes(32, "big")
				elif op.name == "AND":
					out_value = (lhs_u & rhs_u).to_bytes(32, "big")
				elif op.name == "OR":
					out_value = (lhs_u | rhs_u).to_bytes(32, "big")
				elif op.name == "XOR":
					out_value = (lhs_u ^ rhs_u).to_bytes(32, "big")
				elif op.name == "BYTE":
					if lhs_u < 32:
						out_value = rhs_u[lhs_u].to_bytes(32, "big")
					else:
						out_value = (0).to_bytes(32, "big")
				elif op.name == "SHL":
					if lhs_u > 256:
						out_value = (0).to_bytes(32, "big")
					else:
						out_value = ((rhs_u << lhs_u) % 2**256).to_bytes(32, "big")
				elif op.name == "SHR":
					out_value = (rhs_u >> lhs_u).to_bytes(32, "big")
				elif op.name == "SAR":
					if lhs_u > 255:
						out_value = (0).to_bytes(32, "big")
					else:
						out_value = (rhs_i // 2**lhs_u).to_bytes(32, "big", signed=True)
		# 3-parameter operations
		elif op.name in ["ADDMOD", "MULMOD"]:
			# Check if the last 3 items on the pushed stack are bytes
			if len(self.pushed) >= 3 and isinstance(self.pushed[-1], bytes) and isinstance(self.pushed[-2], bytes) and isinstance(self.pushed[-3], bytes):
				# Convert the bytes to integers
				a = int.from_bytes(self.pushed[-1], "big", signed=False)
				b = int.from_bytes(self.pushed[-2], "big", signed=False)
				c = int.from_bytes(self.pushed[-3], "big", signed=False)
				if op.name == "ADDMOD":
					# Perform the ADDMOD operation and convert the result back to bytes
					if c == 0:
						out_value = (0).to_bytes(32, "big")
					else:
						out_value = ((a+b) % c).to_bytes(32, "big")
				elif op.name == "MULMOD":
					# Perform the MULMOD operation and convert the result back to bytes					
					if c == 0:
						out_value = (0).to_bytes(32, "big")
					else:
						out_value = ((a*b) % c).to_bytes(32, "big")
		
		# Remove the items that were used for the operation
		for x in range(pops):
			self.pop()

		# If the output value could not be determined, push None to indicate that
		if out_value == None:
			for x in range(pushes):
				self.push(None, op_idx)
		else:
			# If the output value could be determined, push it as a literal value
			assert pushes == 1
			self.push(out_value, op_idx)
	
	# Modifies the given `stack` as if the operations this `StackMapping` has been created with have been executed.
	# If the `stack` is shorter than what the operations are accessing, this is not an error and just means that we don't know what those values are.
	def apply_mapping(self, stack):
		# Check if the stack is shorter than the number of items being popped
		if len(stack) < self.num_poped:
       		# Backfill the stack with None to match the number of items being popped
			my_stack = stack.copy()
			for x in range(self.num_poped - len(stack)):
				my_stack.insert(0, None)
		else:
			my_stack = stack
    	# Remove the old values that are being popped by the operations
		new_stack = my_stack[:-self.num_poped]
    	# Insert new values that are being pushed by the operations
		for item in self.pushed:
			if isinstance(item, int):
            	# Check if the back-referenced item is available on the stack
				if len(my_stack) >= item + 1:
					new_stack.append(my_stack[-item-1])
				else:
					new_stack.append(None)
			else:
            	# Add the pushed item (literal value or None) to the new stack
				new_stack.append(item)
		return new_stack

