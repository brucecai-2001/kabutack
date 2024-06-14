from core.tool.tool_utils import register_tool

@register_tool('calculator')
def calculator(parameters: dict):
    """A calculator for math calculationwhich support operations"""

    operation = parameters['operation']
    first_number = parameters['first_number']
    second_number = parameters['second_number']

    calculation_result = ""
    if operation == "add":
        calculation_result =  f'''{first_number} add {second_number} is {str( float(first_number) + float(second_number) )}'''
    elif operation == "minus":
        calculation_result = f'''{first_number} minus {second_number} is {str( float(first_number) - float(second_number) )}'''
    elif operation == 'multiply':
        calculation_result = f'''{first_number} multiply {second_number} is {str( float(first_number) * float(second_number) )}'''
    elif operation == 'division':
        calculation_result = f'''{first_number} divide {second_number} is {str( float(first_number) / float(second_number) )}'''

    return calculation_result