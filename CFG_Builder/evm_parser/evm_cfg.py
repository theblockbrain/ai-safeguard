#!/usr/bin/env python3
import pyevmasm
from CFG_Builder.evm_parser.evm_ops import normalize_op
from CFG_Builder.CFG_utils.stack_mapping import StackMapping

# Represents a "basic block"
class Block:
	def __init__(self, start_addr, ops):
        # The address at which this block starts
		self.start_addr = start_addr
        # The list of decoded operations this block consists of
		self.ops = ops
		# Whether or not it is possible for the control flow to simply continue unaltered after the block
		self.can_falltrough = not self.ops[-1].name in ["JUMP", "STOP", "REVERT", "RETURN", "INVALID", "SELFDESTRUCT"]
        # Whether or not this block can make a jump
		self.can_jump = self.ops[-1].name in ["JUMP", "JUMPI"]
        # The address at which the control flow resumes after this block if it doesn't jump
		self.falltrough_addr = start_addr
		for op in ops:
			self.falltrough_addr += op.size
        # Used for operand normalization and to resolve jump destinations
		self.stack_mapping = StackMapping(ops)
        # The stack index on the preexisting stack from which this basic block will read a jump destination.
		self.jump_dest_stack_index = None
        # Statically known jump destination
		self.jump_dest = None
		if self.can_jump:
          # Create a stack mapping for this block but exclude the final jump instruction.
            # This means that the topmost item on the stack at this point will be the jump destination
			stack_mapping_for_jump = StackMapping(ops[:-1])
			if len(stack_mapping_for_jump.pushed) == 0:
                # If there aren't any stack items pushed by ourselves, the topmost item is the topmost remaining stack item after our pops
				self.jump_dest_stack_index = stack_mapping_for_jump.num_poped
			elif isinstance(stack_mapping_for_jump.pushed[-1], int):
                # If the topmost item is a back-reference, we maintain that back-reference as-is.
				self.jump_dest_stack_index = stack_mapping_for_jump.pushed[-1]
			elif isinstance(stack_mapping_for_jump.pushed[-1], bytes):
                # If the topmost item is a literal we have a static jump destination                
				self.jump_dest = int.from_bytes(stack_mapping_for_jump.pushed[-1], "big")
            # Otherwise, it is None, meaning that we don't know.
	
    # Express this basic block in a normalized form
	def as_text(self):
        # Prepend the block's address
		text = "# " + hex(self.start_addr) + "\n"
        # Append the normalized representation of each operations. Note that `normalize_op` may return an empty string to drop the operation.
		for op_idx, op in enumerate(self.ops):
			text = text + normalize_op(op, self.stack_mapping.value_usage_type.get(op_idx))
		return text


# Segregate the bytecode into basic blocks
def create_basic_blocks(evm_bytecode):
    # Finalized blocks, the key is their starting address
	blocks = {}
	
    # Info for the current non-finalized block
	current_block_start = 0
	current_block_ops = []
	
    # Current address in the bytecode
	asm_pos = 0
	
	for op in pyevmasm.evmasm.disassemble_all(evm_bytecode):
        # If there are any previous instructions not part of a finalized block, a JUMPDEST means that the previous block has ended and needs to be finalized
		if op.name == "JUMPDEST" and not len(current_block_ops) == 0:
			blocks[current_block_start] = Block(current_block_start, current_block_ops)
			current_block_start = asm_pos
			current_block_ops = []
		
		current_block_ops.append(op)
		asm_pos += op.size
		
        # Any of these instructions signal the end of a block.
		if op.name in ["JUMP", "JUMPI", "STOP", "REVERT", "RETURN", "INVALID", "SELFDESTRUCT"]:
			blocks[current_block_start] = Block(current_block_start, current_block_ops)
			current_block_start = asm_pos
			current_block_ops = []
	
    # If there are any trailing instructions, we finalize them to a block as well.
	if len(current_block_ops) > 0:
		blocks[current_block_start] = Block(current_block_start, current_block_ops)
	
	return blocks
