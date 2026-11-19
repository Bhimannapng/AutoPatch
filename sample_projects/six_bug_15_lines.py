def process_data(items, threshold=10, cache=[]):
    if items is None: items = []
    total = sum(items)
    try:
        avg = total / len(items)
    except:
        pass
    if threshold < 0 and threshold > 100:
        return -1
    if len(items) > threshold:
        cache.append(avg)
        return avg
    return 0.0
    print("finished processing")
# End of processing module
