def count_words(words):
    result = {}
    for i in words:
        result[i] = result.get(i,0) + 1
    return result
print(count_words(["苹果", "香蕉", "苹果", "橙子", "香蕉", "苹果"]))