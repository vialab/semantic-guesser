#include <iostream>
#include <fstream>
#include <vector>
#include <sstream>
#include <stdlib.h>
#include <unordered_map> 
#include <dirent.h>
#include <queue>
#include <regex>
#include <iterator>

using namespace std;

typedef match_results<const char*> cmatch;

typedef struct {
    std::string word;
    double p;
} Terminal;

class Guess {
    public:
        double p;
        std::string rule;
        std::vector<int> terminals;
        unsigned pivot;
};

/*typedef struct {
    double p;
    std::string rule;
    int[] terminals;
} Guess;*/

std::unordered_map<std::string, double> rules;
std::unordered_map<std::string, std::vector<Terminal>> tag_dicts;

bool replace(std::string& str, const std::string& from, const std::string& to) {
    size_t start_pos = str.find(from);
    if(start_pos == std::string::npos)
        return false;
    str.replace(start_pos, from.length(), to);
    return true;
}

// From http://stackoverflow.com/questions/236129/splitting-a-string-in-c
std::vector<std::string> &split(const std::string &s, char delim, std::vector<std::string> &elems) {
    std::stringstream ss(s);
    std::string item;
    while (std::getline(ss, item, delim)) {
        elems.push_back(item);
    }
    return elems;
}

std::vector<std::string> split(const std::string &s, char delim) {
    std::vector<std::string> elems;
    split(s, delim, elems);
    return elems;
}

std::vector<std::string> unpack(const std::string &s){

    std::vector<std::string> tags;
    std::stringstream temp("");
    for ( int i = 0 ; i < s.length(); i++)
    {
         if (s[i]=='(') 
             continue;
         else if (s[i]==')'){
             tags.push_back(temp.str());
             temp.str("");
             temp.clear();
         } else {
             temp << s[i];
         }
    }
    return tags;
}

/*def probability(base_struct, tags, terminals):
    p = base_structures[base_struct]
    
    for i, tag in enumerate(tags):
        word_index = terminals[i]
        p *= tag_dicts[tag][word_index][1]
    
    return p
*/

double probability(const std::string &rule, const std::vector<std::string> &tags, 
                    const std::vector<int> &terminals){
    
    double p = rules[rule];
    
    for (int i=0; i<tags.size(); i++){
        std::string tag = tags[i];
        int word_index = terminals[i];
        p *= tag_dicts[tag][word_index].p;
    }
    
    return p;
}

/*def decode_guess(p, tags, terminals, pivot):
    result = ''
    for i, tag in enumerate(tags):
        word_index = terminals[i]
        result += tag_dicts[tag][word_index][0]
    
    return [result]*/


std::string decode_guess(const Guess &guess){
    std::stringstream temp("");
                
    std::vector<std::string> tags = unpack(guess.rule);

    for (int i=0; i<tags.size(); i++){
        std::string tag = tags[i];
        int word_index = guess.terminals[i];
        
        temp << tag_dicts[tag][word_index].word;
    }
    
    return temp.str();
}

bool operator<( const Guess& a, const Guess& b ) {
    return a.p < b.p;
}

int main() {

    std::ifstream fs("grammar/rules.txt");
    std::string line;
    
    while (std::getline(fs, line)){
        std::vector<std::string> fields = split(line, '\t');
        std::string rule = fields[0];
        double p = atof(fields[1].c_str());
        rules[rule] = p;
    }
    fs.close();

    DIR *dir = opendir("grammar/seg_dist");
    struct dirent *ent;

    while ((ent = readdir(dir)) != NULL){
        std::string path("grammar/seg_dist/" + std::string(ent->d_name));
        std::ifstream fs(path);
        
        std::vector<Terminal> terminals;

        while (std::getline(fs, line)){
            std::vector<std::string> entry = split(line, '\t');
            if (entry.empty()){
                continue;
            }
            std::string word = entry[0];
            double p = atof(entry[1].c_str());
            Terminal t = {word, p};
            terminals.push_back(t);           
        }
        
        std::string tag (ent->d_name);
        replace(tag, ".txt", "");
        
        tag_dicts[tag] = terminals;

        /*std::vector<Terminal> pi = tag_dicts[tag];
        for(std::vector<int>::size_type i = 0; i != pi.size(); i++) {        
            cout << tag << pi[i].word << pi[i].p <<'\n'; 
        }*/

        fs.close();

    }
    closedir(dir);

    priority_queue<Guess, vector<Guess>, less<vector<Guess>::value_type> > queue;

    for (auto kv : rules) {
        std::string r = kv.first;

        std::vector<std::string> tags = unpack(r);
        
        std::vector<int> terminals;
        for (int i=0; i<tags.size(); i++){
            terminals.push_back(0);
        }
        
        Guess g;
        g.terminals = terminals;
        g.p = probability(r, tags, terminals);
        g.pivot = 0;
        g.rule = r;
        
        queue.push(g);
    }
    
    int nguesses = 0;

    while (!queue.empty()){
        Guess curr = queue.top();
        queue.pop();
                
//        std::cout << decode_guess(curr) << "\n";
        nguesses++;
        
        if (nguesses % 1000000 == 0)
            cout << nguesses << "\n";
        
        std::vector<std::string> tags = unpack(curr.rule);
        for (int i=curr.pivot; i<tags.size(); i++ ){
            std::string tag = tags[i];
            int next_word_index = curr.terminals[i] + 1;
            
            if (next_word_index < tag_dicts[tag].size()){
                std::vector<int> new_terminals(curr.terminals);
                new_terminals[i]++;                

                double new_p = probability(curr.rule, tags, new_terminals);
                int new_pivot = i;
                
                Guess g;
                g.terminals = new_terminals;
                g.p = new_p;
                g.pivot = new_pivot;
                g.rule = curr.rule;
                
                queue.push(g);   
            }
        }
    }
    
    /*    nguesses = 0  
    while not queue.empty():
        curr = queue.get()

        (p, base_struct, terminals, pivot) = curr
        tags = unpack(base_struct)
        
        gs = decode_function(p, tags, terminals, pivot)
            
        for g in gs: 
            if len(g) >= min_length:
                try:
                    print g
                    nguesses += 1
                    if nguesses >= max_guesses: return
                    # debugging
                    #if nguesses % 1000000 == 0: print queue.qsize()
                except:  # treat errors like "Broken pipe"
                    return
                
        
        for i in range(pivot, len(tags)):
            tag = tags[i]
            next_word_index = terminals[i] + 1
            
            # if possible, replace terminals[i] by the next lower probability value
            if next_word_index < len(tag_dicts[tag]):
                new_terminals = tuple([next_word_index if j == i else t for j, t in enumerate(terminals)])
                new_p = probability(base_struct, tags, new_terminals)
                new_pivot = i
                queue.put((-new_p, base_struct, new_terminals, new_pivot))
*/
    
}


