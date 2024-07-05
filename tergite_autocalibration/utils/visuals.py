def box_print(text: str):
    margin = 20
    print("\u2554" + "\u2550" * (len(text) + margin) + "\u2557")
    print("\u2551" + margin // 2 * " " + text + margin // 2 * " " + "\u2551")
    print("\u255a" + "\u2550" * (len(text) + margin) + "\u255d")
    return


def draw_arrow_chart(header: str, node_list: list[str]):
    # max_length = max(len(item) for item in node_list)
    # total_length = sum([len(node)//2 for node in node_list]) + 2*len(node_list) + 6
    total_length = sum([6 for node in node_list]) + 2 * len(node_list) + 6
    total_length = max(60, total_length)
    print("\u2554" + "\u2550" * total_length + "\u2557")
    length = 0
    print("\u2551" + " " + header + " " * (total_length - len(header) - 1) + "\u2551")
    for i, item in enumerate(node_list):
        if i < len(node_list):
            print(
                "\u2551"
                + " " * length
                + "\u21aa"
                + " "
                + item
                + " " * (total_length - length - len(item) - 2)
                + "\u2551"
            )
            # length += len(item) // 2
            length += 6
    print("\u255a" + "\u2550" * total_length + "\u255d")
