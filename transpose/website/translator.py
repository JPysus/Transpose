#Author - John Michael De Borja (JPysus)
#johnmichaeldb@gmail.com
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

E -> S MID_OP S | S MID_OP NV | NV MID_OP S | NV MID_OP NV
E -> S | NV
S -> O | L 
L -> MULTIPLIER L
L -> 'sum' LEADING | 'difference' LEADING | 'product' LEADING | 'quotient' LEADING
L -> EXACT NV NV | EXACT S S | EXACT S NV | EXACT NV S
LEADING -> NV ',' LEADING | S ',' LEADING 
LEADING -> NV 'and' NV | NV 'and' S | S 'and' NV | S 'and' S
LEADING -> 'and' NV | 'and' S
O -> NV MID_WORD NV | S MID_WORD S
O -> S ',' MID_WORD S | S ',' MID_WORD ',' S | S MID_WORD ',' S
O -> S ',' MID_WORD NV | NV MID_WORD ',' S
O -> S MID_WORD NV | NV MID_WORD S 

NV -> '#VAR#' | '#NUM#' | MULTIPLIER NV
MULTIPLIER -> 'square' | 'twice' | 'thrice' | '-'
MID_WORD -> EXACT | REVERSE
LEAD_WORD -> 'sum' | 'difference' | 'product' | 'quotient'
MID_OP -> '≠' | '=' | '≤' | '<' | '≥' | '>'
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
        '=': ['equal', 'yield'], 
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
        'twice': ['twice'],
        'thrice': ['thrice'],
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
stopword = ["an", "by", "the", "of", "from", "certain", 'as', 'another', 'when', "with"]
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

        # e.g. "one plus two is six" -> "one plus two = six"
        elif pos[i][0] == "be":
            if i > 0 and i != len(pos):
                if pos[i-1][1] in ('CD') or match(r"^-?\d*[a-z]$",pos[i-1][0]):
                    temp_op_keyword = list(operator['LEADING'])
                    temp_op_keyword += list(operator['MULTIPLIER'])
                    if pos[i+1][1] in ('CD') or match(r"^-?\d*[a-z]$", pos[i+1][0]) or pos[i+1][0] in temp_op_keyword:
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
                temp.append("product")
                temp.append(search("[0-9]+", temp_word).group())
                temp.append("and")
                v = search("[a-z]", temp_word).group()
                variable.remove(v)
                variable.append(v)
                temp.append(v)
            
            #if word is x, y, z, etc...
            elif temp_word in variable:
                temp.append(temp_word)
                variable.remove(temp_word)
                variable.append(temp_word)
            
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
    'less': '-',
    'times': '*',
    'divide': '/',
}
def _word_math_tree_to_list(tree, lead_op = None):
    #encloses all starts
    output = []

    #for E grammar
    if tree.label() in ('E'):
        for i in tree:
            if i.label() in ('S', 'NV'):
                output.append(_word_math_tree_to_list(i))

            elif i.label() in ('MID_OP'):
                output.append(i[0])
    
    #for NV grammar
    elif tree.label() in ('NV'):
        if isinstance(tree[0], str):
            output.append(tree[0])

        else:
            output.append(tree[0][0])
            output.append(_word_math_tree_to_list(tree[1]))

    #for S grammar 
    elif tree.label() in ('S'):
        for i in tree:
            if i.label() in ('O', 'L'):
                in_list = []
                in_list.append(_word_math_tree_to_list(i))
                output.append(in_list)
    
    #for L grammar
    elif tree.label() in ('L'):
        temp = []       #collects NV, S output
        temp_op = ""    #temp_op is operator for lead_op param.

        #for variations of L grammar
        for i in tree:
            if isinstance(i, str) and i in lead_op_sign.keys():
                temp_op = i

            elif i.label() in ('EXACT'):
                temp_op = i[0]

            elif i.label() in ('S', 'NV', 'L'):
                temp.append(_word_math_tree_to_list(i))

            elif i.label() in ('LEADING'):
                temp = _word_math_tree_to_list(i, lead_op = temp_op)

            elif i.label() in ('MULTIPLIER'):
                temp.append(i[0])
        
        if temp_op != "":
            #temp_op => operator
            #code to turn [x, y] => [x, temp_op, y]
            #transforming LEADING sequence into EXACT
            result = [lead_op_sign[temp_op]] * (len(temp) * 2 - 1)
            result[0::2] = temp
        
        else:
            result = temp    
        return result
    
    #for LEADING grammar
    elif tree.label() in ('LEADING'):
        for i in tree:
            #for ',' and 'and', skip these
            if isinstance(i, str):
                continue

            elif i.label() in ('S', 'NV'):
                output.append(_word_math_tree_to_list(i))

            #for LEADING again
            elif i.label() in ('LEADING'):
                temp = _word_math_tree_to_list(i, lead_op)
                for x in temp:
                    output.append(x)
            
    
    #for O grammar, add minus etc...
    elif tree.label() in ('O'):
        in_list = []
        for i in tree:
            #for ',' skip this
            if isinstance(i, str):
                continue
            
            elif i.label() in ('S', 'NV'):
                in_list.append(_word_math_tree_to_list(i))

            #for MID_WORD -> EXACT | REVERSE
            #from O grammar, then i[0][0]
            elif i.label() in ('MID_WORD'):
                in_list.append(i[0][0])

        output.append(in_list)
    return output

def _mid_operator_convert(s):
    for i in range(len(s)):
        if isinstance(s[i], str):
            if s[i] == "square":
                s[i] = "^ 2"
                s[i], s[i+1] = s[i+1], s[i]

            elif s[i] == "twice":
                s[i] = "2 *"

            elif s[i] == "thrice":
                s[i] = "3 *"

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
        sentence_list[i] = (' '.join(_flatten([sentence_list[i]])))
        #sentence_list[i] is enclosed in anoter []
        #for input cases like "one"
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