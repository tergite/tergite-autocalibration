def box_print(text: str):
    margin = 20
    print(u"\u2554" + u"\u2550" * (len(text)+margin) + u"\u2557")
    print(u"\u2551" + margin//2*" " + text + margin//2*" " + u"\u2551")
    print(u"\u255a" + u"\u2550" * (len(text)+margin) + u"\u255d")
    return

def draw_arrow_chart(header:str, node_list: list[str]):
    # max_length = max(len(item) for item in node_list)
    # total_length = sum([len(node)//2 for node in node_list]) + 2*len(node_list) + 6
    total_length = sum([6 for node in node_list]) + 2*len(node_list) + 6
    total_length = max(60,total_length)
    print(u"\u2554" + u"\u2550" * total_length + u"\u2557")
    length = 0
    print(u"\u2551" + " " + header + " " * (total_length -len(header)-1) + u"\u2551")
    for i, item in enumerate(node_list):
        if i < len(node_list):
            print(u"\u2551" + " "*length + u"\u21aa" + " " + item + " " * (total_length-length-len(item) - 2) + u"\u2551")
            # length += len(item) // 2
            length += 6
    print(u"\u255a" + u"\u2550" * total_length + u"\u255d")
