
def likeBatch(sfobject, items, queryLength):

    # given an object and list of words, create a list of batch query strings
    likeString = ','.join([f"{sfobject} LIKE '%{el}%'" for el in items])

    # find the first comma following every 15k elements
    indexSplits = [likeString.find(',',queryLength*x) for x in range(1,int(len(likeString)/queryLength)+1)]

    if len(indexSplits) == 0:
        queries = [' OR '.join(likeString.split(','))]
    else:
        splitTuples = list(zip([x+1 for x in indexSplits], indexSplits[1:]+[None]))
        first = (None, indexSplits[0])
        splitTuples.append(first)

        queries = []
        for string in [likeString[i:j] for i,j in splitTuples]:
            quertString = ' OR '.join(string.split(','))
            queries.append(quertString)

    return queries


def inBatch(itemList, queryLength):

    # given an object and list of words, create a list of batch query strings
    itemString = ','.join(itemList)
    # find the comma following every 15k th element
    indexSplits = [itemString.find(',',queryLength*x) for x in range(1,int(len(itemString)/queryLength)+1)]

    if len(indexSplits) == 0:
        queries = [itemList]
    else:
        splitTuples = list(zip([x+1 for x in indexSplits], indexSplits[1:]+[None]))
        first = (None, indexSplits[0])
        splitTuples.append(first)

        queries = [itemString[i:j].split(',') for i,j in splitTuples]

    return queries


def basicQuery(list):

    if len(list) == 1:
        query = f"('{list[0]}')"
        return query
    else:
        query = tuple(list)
        return query
