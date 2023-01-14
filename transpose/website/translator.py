from nltk import CFG
from nltk import Tree
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk import pos_tag
from nltk import ChartParser

from re import search, match, findall

from text2digits import text2digits

t2d = text2digits.Text2Digits()
math_word_grammar = CFG.fromstring("""

E -> S '≠' S | S '=' S | S '<' S | S '>' S | S '≤' S | S '≥' S
E -> S '≠' NV | S '=' NV | S '<' NV | S '>' NV | S '≤' NV | S '≥' NV
E -> NV '≠' S | NV '=' S | NV '<' S | NV '>' S | NV '≤' S | NV '≥' S
E -> NV '≠' NV | NV '=' NV | NV '<' NV | NV '>' NV | NV '≤' NV | NV '≥' NV
E -> S
S -> 'square' S | 'square' NV
S -> O | L | '-' O | '-' L
L -> 'sum' LEADING | 'difference' LEADING | 'product' LEADING | 'quotient' LEADING
L -> 'divide' NV NV | 'more' NV NV
LEADING -> NV ',' LEADING | S ',' LEADING 
LEADING -> NV 'and' NV | NV 'and' S | S 'and' NV | S 'and' S
LEADING -> 'and' NV | 'and' S
NV -> '#VAR#' | '#NUM#'
O -> NV EXACT NV | NV REVERSE NV | S EXACT S | S REVERSE S 
O -> S ',' EXACT S | S ',' REVERSE S | S ',' EXACT NV | S ',' REVERSE NV 
O -> NV EXACT S | NV REVERSE S
EXACT -> 'more' | 'less' | 'times' | 'divide'
REVERSE -> 'more_than' | 'less_than'

""")

operator = {
    '5EQUALITY':{
        '<': ['be less than or equal to'],   
    },
    '4EQUALITY':{
        '≠': ['be not equal to'],
    },
    '3EQUALITY':{
        '=': ['be equal to'],
        '<': ['be less than', 'be fewer than'],
        '>': ['be more than', 'be greater than'],
        '≤': ['be at most'],
        '≥': ['be at least'],
    },
    '2EXACT':{
        'less':['take away'],
    },
    '2REVERSE':{
        'less_than': ['subtract from', 'less than', 'fewer than'],
        'more_than': ['more than', 'greater than'],
    },
    'EQUALITY':{
        '=': ['equal'], 
    },
    'EXACT':{
        'more': ['plus', 'add', 'increase', 'exceed', 'more'], 
        'less':['subtract', 'minus', 'decrease', 'less', 'diminish', 'reduce', 'lost'],
        'times': ['time', 'times', 'multiply'],
        'divide': ['divide']
    },
    'LEADING':{
        'sum': ['sum','total','addition'],
        'difference': ['difference'],
        'product': ['multiplication', 'product'],
        'quotient': ['quotient', 'ratio'],
    },
    'EXPONENT':{
        'square':['square'],
    },
    'MULTIPLIER':{
        '2 times': ['twice'],
        '3 times': ['thrice'],
    },
}
operator_sign = {
    'more': '+',
    'less': '-',
    'times': '*',
    'divide': '/',
}
keyword = [word for i in operator.keys() for j in operator[i].keys() for word in operator[i][j]]
keyword = list(set(keyword+[j for i in operator.keys() for j in operator[i].keys()]))
keyword.sort(key=len, reverse=True)
stopword = ["an", "by", "the", "of", "from", "certain", 'as', 'another']
    #filter LEADING keywords out
modified_keyword = list(set(keyword) - set([word for i in operator["LEADING"].keys() for word in operator["LEADING"][i]]))

#preprocessing
def _preprocess(sentence):
    #1. noise reduction
        #lowercasing and punctuation
    sentence = sentence.lower()
    sentence = sentence.replace('.', '')

        #Lemmatization
    token = word_tokenize(sentence)
    pos = pos_tag(token)
    sentence = [WordNetLemmatizer().lemmatize(word, 'v') for word in token]
    sentence = ' '.join(sentence)

    #2. standardize keywords
    for i in operator.keys():
        for j in operator[i].keys():
            for k in operator[i][j]:
                if(str(k) in sentence):
                    sentence = sentence.replace(k, j)
    #1. noise reduction again
        #stopword
    sentence = word_tokenize(sentence)
    temp = []
    for i in sentence:
        if i not in stopword:
            temp.append(i)
    sentence = ' '.join(temp)

    #3. expanding one-half, one-third, etc....

    temp = findall('[a-z]-[a-z]', sentence)
    for i in temp:
        sentence = sentence.replace(i, i.replace("-", " "))
    sentence = sentence.replace("half", "second")
    sentence = sentence.replace("halve", "second")
    sentemp = word_tokenize(sentence)
    postemp = _flatten([pos_tag([i]) for i in sentemp])

    #[i][0] = word
    #[i][1] = PartOfSpeech
    temp2 = "" #output to be returned
    i = 0
    
        #converts one-half into quotient of one and two
        #adds ", times " if the next token is a number, variable or in LEADING keyword
    while(i < len(postemp)):
        if postemp[i][1] in ('CD') and i < len(postemp) - 1:
            if postemp[i+1][1] in ('JJ') and postemp[i+1][0].endswith(("second", "third", "th")):
                temp2 += 'quotient ' + postemp[i][0] + " and " + postemp[i+1][0]
                
                if i < len(postemp) - 2 and postemp[i+2][0] not in modified_keyword+[',']:
                    temp2 += ', times '
                i += 2
                continue
        temp2 += postemp[i][0]+" "
        i += 1
    return temp2

# conversions
def _name_conversion(sentence):
    #2. variable conversion

    token = word_tokenize(sentence)
    pos = pos_tag(token)
    variable = ['x', 'y', 'z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v']
    #[i][0] = word
    #[i][1] = PartOfSpeech
    i = 0
    temp = [] #output to be returned
    while(i < len(pos)):
        # e.g. "a number" -> "number", "a plus b" -> "a plus b"
        if pos[i][0] == "a":
            if i != len(pos) - 1 and not (match(r"^-?\d+$",pos[i+1][0]) or pos[i+1][0] in variable or pos[i+1][0] in modified_keyword+['and', ',']):
                None
            else:
                temp.append(pos[i][0])
                variable.remove(pos[i][0])
                variable.append(pos[i][0])
        
        # e.g. filter out the word "to", or "ratio x to y" -> "ratio x and y"
        elif pos[i][0] == "to":
            if i > 1 and pos[i-2][0] == "quotient":
                temp.append("and")
            else:
                None

        # e.g. "one plus two is six" -> "one plus two is equal to"
        elif pos[i][0] == "be":
            if i > 1 and i != len(pos) and pos[i-1][1] in ('CD') and (pos[i+1][1] in ('CD') or pos[i+1][0] in keyword):
                temp.append("=")
            else:
                None

        # e.g. "negative" -> "-"
        elif pos[i][0] == "negative":
            if i != len(pos) - 1 and (match(r"^-?\d+$",pos[i+1][0]) or pos[i+1][0] in variable):
                temp.append('-'+pos[i+1][0])
                i += 1
            else:
                temp.append('-')

        # e.g. "number" -> "x" ,"number c" -> "c"
        elif pos[i][0] == "number" and i != len(pos) - 1:
            if pos[i+1][1] in ('CD') or match(r"^-?\d+$",pos[i+1][0]) or pos[i+1][0] in variable:
                None
            else:
                var_clone = variable[0]
                temp.append(var_clone)
                variable.remove(var_clone)
                variable.append(var_clone)

        elif pos[i][0].endswith('_than'):
            temp.append(pos[i][0])

        # inclusion of recognized keywords/variables/numbers
        elif pos[i][1] in ('CD') or match(r"^-?\d+$",pos[i][0]) or pos[i][0] in keyword+['and', ','] or pos[i][0] in variable:
            temp_word = pos[i][0]
            temp_pos = pos[i][1]
            # if word is 2x, 2y, 4z, etc....
            if match("^[0-9]+[a-z]$", temp_word):
                temp.append(search("[0-9]+", temp_word).group())
                temp.append("times")
                v = search("[a-z]", temp_word).group()
                variable.remove(v)
                variable.append(v)
                temp.append(v)
                temp.append(',')
            else:
                temp.append(temp_word)
        # if it gets here
        # it means word is unknown, 
        # and will be turned into a variable
        else:
            var_clone = variable[0]
            temp.append(var_clone)
            variable.remove(var_clone)
            variable.append(var_clone)
        i += 1
    return temp

lead_op_sign = {
    'sum': '+',
    'difference': '-',
    'product': '*',
    'quotient': '/',
    'more': '+',
    'divide': '/',
}
def _word_math_tree_to_list(tree, lead_op = None):
    output = []
    #encloses all starts
    if isinstance(tree, str) and tree == "square":
        output.append(tree)

    elif tree.label() in ('NV'):
        output.append(tree.leaves()[0])

    elif tree.label() in ('E'):
        for i in tree:
            if isinstance(i, str):
                output.append(i)
            else:
                in_list = []
                in_list.append(_word_math_tree_to_list(i))
                output.append(in_list)

    elif tree.label() in ('S'):
        for i in tree:
            if isinstance(i, str) and i == '-':
                output.append(i)
            else:
                in_list = []
                in_list.append(_word_math_tree_to_list(i))
                output.append(in_list)
    
    #combines all words from L to LEADING SEQUENCE, 
    elif tree.label() in ('L'):
        if tree[1].label() in ('NV'):
            temp = _word_math_tree_to_list(tree[1], lead_op = tree[0])
            temp += _word_math_tree_to_list(tree[2], lead_op = tree[0])
        else:
            temp = _word_math_tree_to_list(tree[1], lead_op = tree[0])
        
        #small code to put OPERATOR word between VAR/NUM, in a LEADING sequence
        result = [lead_op_sign[tree[0]]] * (len(temp) * 2 - 1)
        result[0::2] = temp
        return result
    
    #gets all LEADING words
    elif tree.label() in ('LEADING'):
        for i in tree:
            if type(i) is str:
                continue
                
            elif i.label() in ('NV'):
                output.append(i.leaves()[0])
                
            #recursion, traverses S 
            #goes back to L
            elif i.label() in ('S'):
                output.append(_word_math_tree_to_list(i, lead_op))
            
            #recursion, traverses LEADING 
            #goes back to L
            elif i.label() in ('LEADING'):
                temp = _word_math_tree_to_list(i, lead_op)
                for x in temp:
                    output.append(x)
    
    #for add minus etc...
    elif tree.label() in ('O'):
        in_list = []
        for i in tree:
            if type(i) is str:
                continue
            
            #recursion, gets all NUM VAR add minus etc... from O
            #goes back to S
            elif i.label() in ('NV', 'EXACT', 'REVERSE'):
                in_list.append(i.leaves()[0])
                
            #recursion, traverses S 
            #goes back to S
            elif i.label() in ('S'):
                in_list.append(_word_math_tree_to_list(i))
        output.append(in_list)
    return output

def _mid_operator_convert(s):
    for i in range(len(s)):
        if isinstance(s[i], str) and s[i] == "square":
            s[i] = "^ 2"
            s[i], s[i+1] = s[i+1], s[i]
        if type(s[i]) is list:
            s[i] = _mid_operator_convert(s[i])
            continue
        #swap i-1 and i+1 then change to EXACT
        if s[i] in operator['2REVERSE'].keys():
            if type(s[i+1]) is list:
                s[i+1] = _mid_operator_convert(s[i+1])
            s[i-1], s[i+1] = s[i+1], s[i-1]
            s[i] = 'more' if s[i] == 'more_than' else 'less'
        #keyword to signs
        if s[i] in operator['EXACT'].keys():
            s[i] = operator_sign[s[i]]
    return s

def _tree_conversion(token):
    #3. tree conversion
        # for recognizing constants and variables
        # recreates the original sentence with #VAR# #NUM# replacements
    mod_token = ['#NUM#' if match(r"^-?[0-9]+$", i) else i for i in token]
    mod_token = ['#VAR#' if match(r"^-?[a-z]$", i) else i for i in mod_token]
    numbers = [i for i in token if match(r"^-?[0-9]+$", i)]
    var = [i for i in token if match(r"^-?[a-z]$", i)]

        #converting the token to TREE object
    trees = []
    parser = ChartParser(math_word_grammar)

    for tree in parser.parse(mod_token):
        treestr = str(tree)
        for n in numbers:
            treestr = treestr.replace('#NUM#', str(n), 1)
        for l in var:
            treestr = treestr.replace('#VAR#', l, 1)
        trees.append(Tree.fromstring(treestr))

    return trees

def _conversion(sentence):
    #1. number conversion
    sentence = t2d.convert(sentence)

    #2. variable conversion
    token = _name_conversion(sentence)
    
    #3. tree conversion
    trees = _tree_conversion(token)
    if len(trees) == 0:
        return None

    #4. tree reformatting
    sentence_list = []
    for tree in trees:
        temp = _word_math_tree_to_list(tree)
        sentence_list.append(_semi_flattener(temp))
    for i in range(len(sentence_list)):
        sentence_list[i] = _mid_operator_convert(sentence_list[i])

    return sentence_list

# post-processing
def _postprocessing(sentence_list):
    for i in range(len(sentence_list)):
        sentence_list[i] = _parenthesis_adder(sentence_list[i])
        sentence_list[i] = (' '.join(_flatten(sentence_list[i])))
    return (sentence_list)

def _semi_flattener(tree_list):
    # list flattener specifically for tree_list
    # dont replace with _flatten(S)
    if type(tree_list) is not list:
        return tree_list
    
    elif len(tree_list) > 1: 
        for i in range(len(tree_list)):
            if type(tree_list[i]) == list and len(tree_list[i]) > 0:
                tree_list[i] = _semi_flattener(tree_list[i])
                
    elif (len(tree_list)) == 1:
        tree_list = _semi_flattener(tree_list[0])
        
    return tree_list

def _flatten(S):
    if S == []:
        return S
    if isinstance(S[0], list):
        return _flatten(S[0]) + _flatten(S[1:])
    return S[:1] + _flatten(S[1:])

def _parenthesis_adder(l):
    for i in range(len(l)):
        if type(l[i]) is list:
            if(l[i][0] != '('):
                l[i].insert(0, '(')
                l[i].append(')')
                l[i] = _parenthesis_adder(l[i])
    return l

# translate func
def translate(sentence):
    sentence = _preprocess(sentence)

    sentence_list = _conversion(sentence)
    if sentence_list is None:
        return None
    
    sentence_list = _postprocessing(sentence_list)

    return sentence_list

#optional function
def prettier(trans):
#making output more readable

    txt = trans
    txt = txt.replace("( ", "(")
    txt = txt.replace(" )", ")")
    
    x = findall(r"[0-9]+ \* [a-z]", txt)
    if x:
        x = list(set(x))
        y = [i.replace(" * ", "") for i in x]
        for i, j in zip(x, y):
            txt = txt.replace(i, j)

    x = findall(r"\([0-9]+[a-z]\)", txt)
    if x:
        x = list(set(x))
        y = [i.strip("()") for i in x]
        for i, j in zip(x, y):
            txt = txt.replace(i, j)

    if txt != trans:
        return txt
    else:
        return trans