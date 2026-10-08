# def word_count(text):
#     result = {}
#     words = text.split()
#     for i in words:
#         result[i] = result.get(i,0) + 1
#     return result
# print(word_count("Apple apple BANANA".lower()))
def word_count(text):
    result = {}
    words = text.split()
    for i in words:
        w = i.lower()
        result[w] = result.get(w,0) + 1
    return result
print(word_count("Apple apple BANANA"))