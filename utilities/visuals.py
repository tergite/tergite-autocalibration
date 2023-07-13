def box_print(text: str):
    margin = 20
    print(u"\u2554" + u"\u2550" * (len(text)+margin) + u"\u2557")
    print(u"\u2551" + margin//2*" " + text + margin//2*" " + u"\u2551")
    print(u"\u255a" + u"\u2550" * (len(text)+margin) + u"\u255d")
    return

