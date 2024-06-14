from core.tool.tool_utils import register_tool


@register_tool('compare')
def compare(parameters: dict, first_num, second_num) -> str:
    """Compare two number, the result could be larger, smaller or equal"""

    first_num = parameters['first_number']
    second_num = parameters['second_number']
    
    compare_result = ""
    if float(first_num) == float(second_num):
        compare_result =  f'''{first_num} is equal to {second_num}'''
    elif float(first_num) > float(second_num):
        compare_result = f'''{first_num} is larger than {second_num}'''
    else:
        compare_result = f'''{first_num} is less than {second_num}'''
    
    return compare_result