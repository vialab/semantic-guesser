#include <iostream>
#include <fstream>
#include <vector>
#include <sstream>
#include <stdlib.h>
#include <unordered_map> 
#include <dirent.h>
#include <string.h>
#include <queue>
#include <regex>
#include <iterator>
#include <algorithm>
#include <string>
#include <limits>
#include "cpp-argparse/OptionParser.h"

using namespace std;
using namespace optparse;

typedef match_results<const char*> cmatch;

typedef struct {
    std::string word;
    double p;
} Terminal;

typedef struct {
    std::string str;
    double p;
} Rule;

class Guess {
    public:
        Rule * rule;
        std::vector<std::vector<Terminal>::iterator> terminals;
        unsigned pivot;
};
//testing
std::set<std::string> gaps = {"number", "num+special", "special", "char", "all_mixed"};
std::vector<Rule> rules;
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

double probability(double p_rule,
		std::vector<std::vector<Terminal>::iterator> &terminals){
    
    double p = p_rule;

    for (int i=0; i<terminals.size(); i++){
    	p *= (*terminals[i]).p;
    }
    return p;
}

double probability(Guess g){
    return probability(g.rule->p, g.terminals);
}


std::string mangle_guess(const Guess &guess, std::vector<std::string> &tags, const std::string &action, std::vector<bool> &gap_map){

    std:stringstream guess_str;
    for (int i=0; i<tags.size(); i++){
    	//std::vector<Terminal>::iterator word_pointer = guess.terminals[i];
        std::string word = (*guess.terminals[i]).word;
        if (!gap_map[i]){
            if (action=="upper")
                std::transform(word.begin(), word.end(), word.begin(), ::toupper);
            else if (action=="lower")
                std::transform(word.begin(), word.end(), word.begin(), ::tolower);
            else if (action=="title"){
                std::transform(word.begin(), word.end(), word.begin(), ::tolower);
                word[0] = toupper(word[0]);
            }
        }
       guess_str << word;
    }

    return guess_str.str();
}

std::vector<std::string> decode_guess(const Guess &guess){

    std::stringstream temp("");
                
    for (int i=0; i < guess.terminals.size(); i++){
        temp << (*guess.terminals[i]).word;
    }
    
    std::vector<std::string> guesses {temp.str()};
    
    return guesses;
}

bool is_gap(std::string str){
    return (str.find("number") == 0)
    || (str.find("special") == 0)
    || (str.find("char") == 0);
}

std::vector<std::string> decode_guess_mangled(const Guess &guess){
	std::vector<std::string> tags = unpack(guess.rule->str);

    std::vector<bool> gap_map;
    bool allgaps = true;
    for (int i=0; i<tags.size(); i++){
        const bool is_gap_ = is_gap(tags[i]);
        gap_map.push_back(is_gap_);
        if (!is_gap_) allgaps = false;
    }

    // if it's all gaps, there's nothing to mangle
    if (allgaps) return decode_guess(guess);

    std::vector<std::string> guesses;

    std::string lower = mangle_guess(guess, tags, "lower", gap_map);
    std::string upper = mangle_guess(guess, tags, "upper", gap_map);
    std::string camel = mangle_guess(guess, tags, "title", gap_map);

    guesses.push_back(lower);
    guesses.push_back(upper);
    if (camel !=  upper)
        guesses.push_back(camel);
  
    std::string title(lower);
    title[0] = toupper(title[0]);
    if (title != camel)
        guesses.push_back(title);
    

    return guesses;
}

void load_grammar(std::string &grammar_folder ){

    std::string rules_path = grammar_folder + "rules.txt";
    std::ifstream fs(rules_path);
    std::string line;
   
    while (std::getline(fs, line)){
        std::vector<std::string> fields = split(line, '\t');
        Rule rule;
        rule.str = fields[0];  // string
        rule.p = atof(fields[1].c_str());  // probability
        rules.push_back(rule);
    }
    fs.close();
    
    std::string nonterminals_path = grammar_folder + "nonterminals/";
    DIR *dir = opendir(nonterminals_path.c_str());
    struct dirent *ent;

    while ((ent = readdir(dir)) != NULL){
        std::string path = nonterminals_path + std::string(ent->d_name);
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

        fs.close();

    }
    closedir(dir);
}

/**
 * Used with std::sort to sort an array in decreasing order.
 */
//bool compare(std::pair<std::string, double> a, std::pair<std::string, double> b){
//    return a.second < b.second;
//}

/**
 * Returns the *approximate* probabilities of the least and most probable guesses.
 */
/*double* prob_bounds(){
    std::vector<std::pair<std::string, double>> vec(rules.begin(), rules.end());
    std::sort(vec.begin(), vec.end(), &compare);
    
    // calculate the highest probability guess
    std::string max_rule = vec.back().first;
    std::vector<std::string> tmp_tags = unpack(max_rule);
    double max_p = probability(max_rule, tmp_tags, std::vector<int>(tmp_tags.size(), 0));
    
    // calculate the lowest probability guess
    std::string min_rule = vec[0].first;
//    cerr << "least probable rule: " << min_rule << '\n';
    tmp_tags = unpack(min_rule);
    double min_p = vec[0].second;
    for (std::vector<int>::size_type i = 0; i != tmp_tags.size(); i++){
        min_p *= tag_dicts[tmp_tags[i]].back().p;
    }
    
    double bounds[2];
    bounds[0] = min_p;
    bounds[1] = max_p;
    
    return bounds;
}*/

bool operator<( const Guess& a, const Guess& b ) {
    return probability(a) < probability(b);
}

/**
 * Check if, of all possible parents of child, the informed
 * parent is the one with the lowest probability.
 * The pseudocode for this function can be found in Appendix
 * B of Weir's PhD thesis.
 */
bool is_lowest_probability_parent(Guess &child, Guess &parent, std::vector<std::string> &tags, double parent_p, int pivot){
	Rule rule = *parent.rule;

	for (int i = 0; i < tags.size(); i++){
		if (i == pivot)
			continue;

		std::string tag = tags[i];

		// generate a parent for this guess by decrementing the pointer to its ith terminal
		std::vector<std::vector<Terminal>::iterator> other_parent(child.terminals);
		// check if decrementing the pointer will send it off valid bounds
		// if so, skip this terminal
		if (other_parent[i] == tag_dicts[tag].begin())
			continue;
		--other_parent[i];

		double other_parent_p = probability(rule.p, other_parent);

		// decide if other parent will take care of the child
		if (other_parent_p < parent_p)
			return false;
		else if (other_parent_p == parent_p) {
			if (i > pivot) // location of the pivot is used to break ties
				return false;
		}
	}
	return true;
}

int run_deadbeat(bool mangle, double limit, int min_length, double min_prob, bool verbose){

    priority_queue<Guess, vector<Guess>, less<vector<Guess>::value_type>> queue;

    // Initialize queue with the most probable guess of each rule
    for (std::vector<Rule>::iterator it = rules.begin(); it != rules.end(); ++it){
    	Rule * rule = &(*it);

        std::vector<std::string> tags = unpack(rule->str);

        std::vector<std::vector<Terminal>::iterator> terminals;
        for (int i=0; i<tags.size(); i++){
            terminals.push_back(tag_dicts[tags[i]].begin());
        }

        Guess g;
        g.terminals = terminals;
        g.pivot = 0;
        g.rule = rule;

        // only enqueue guesses with probability higher than threshold
        if (probability(g) >= min_prob)
        	queue.push(g);
    }

    long long nguesses = 0;
    Guess curr_guess;
    std::string guess_string;

    // Generate (output) guesses in highest probability order
    while (!queue.empty()){
        curr_guess = queue.top();
        double curr_guess_p = probability(curr_guess);
        queue.pop();


        std::vector<std::string> guesses;
        if (mangle)
            guesses = decode_guess_mangled(curr_guess);
        else
            guesses = decode_guess(curr_guess);

        for (int i=0; i<guesses.size(); i++){
        	guess_string = guesses[i];
            // TODO: if we want to make things faster, should not generate the
            // unwanted guesses in the first place.
            if (guess_string.length() < min_length)
                continue;

            nguesses++;

            if (nguesses % 1000000 == 0){ // output status line
                cerr << "# of guesses: " << nguesses          << "\n";
                cerr << "queue size: "   << (int)queue.size() << "\n";
            }

            cout << guess_string ; // output guess
            if (verbose){
            	cout << "\t" << curr_guess_p; // output probability
            	cout << "\t" << curr_guess.rule->str; //output rule
            }
            cout << "\n";


            // exit when reach the limit of guesses
            if (nguesses == limit){
            	cerr << "Last guess: (" << guess_string << ", " << curr_guess_p << ")\n";
            	cerr << nguesses << " guesses generated\n";
            	return 0;
            }
        }

        std::vector<std::string> tags = unpack(curr_guess.rule->str);
        // enqueue lower probability guesses from the same rule of curr_guess
        for (int i = 0; i < tags.size(); i++ ){
            std::string tag = tags[i];

            std::vector<std::vector<Terminal>::iterator> new_terminals(curr_guess.terminals);
            ++new_terminals[i];

            if (new_terminals[i] != tag_dicts[tag].end()){

                double child_p = probability((*curr_guess.rule).p, new_terminals);

                // do not enqueue guesses with probability lower than threshold
                if (child_p < min_prob) continue;

                Guess child;
                child.terminals = new_terminals;
                child.pivot     = i;
                child.rule      = curr_guess.rule;

                if (is_lowest_probability_parent(child, curr_guess, tags, curr_guess_p, i))
                	queue.push(child);
            }
        }
    }

    cerr << "Last guess: (" << guess_string << ", " << probability(curr_guess) << ")\n";
    cerr << nguesses << " guesses generated\n";

    return 0;
}


int run_next(bool mangle, double limit, int min_length, double min_prob, bool verbose){

    priority_queue<Guess, vector<Guess>, less<vector<Guess>::value_type>> queue;

    // Initialize queue with the most probable guess of each rule
    for (std::vector<Rule>::iterator it = rules.begin(); it != rules.end(); ++it){
    	Rule * rule = &(*it);
        
        std::vector<std::string> tags = unpack(rule->str);

        std::vector<std::vector<Terminal>::iterator> terminals;
        for (int i=0; i<tags.size(); i++){
            terminals.push_back(tag_dicts[tags[i]].begin());
        }
        
        Guess g;
        g.terminals = terminals;
        g.pivot = 0;
        g.rule = rule;
        
        // only enqueue guesses with probability higher than threshold
        if (probability(g) >= min_prob)
        	queue.push(g);
    }

    long long nguesses = 0;
    Guess curr_guess;
    std::string guess_string;

    // Generate (output) guesses in highest probability order
    while (!queue.empty()){
        curr_guess = queue.top();
        queue.pop();
                
        std::vector<std::string> guesses;
        if (mangle)
            guesses = decode_guess_mangled(curr_guess);
        else
            guesses = decode_guess(curr_guess);
            
        for (int i=0; i<guesses.size(); i++){
        	guess_string = guesses[i];
            // TODO: if we want to make things faster, should not generate the
            // unwanted guesses in the first place.
            if (guess_string.length() < min_length)
                continue;
            
            nguesses++;
                
            if (nguesses % 1000000 == 0){ // output status line
                cerr << "# of guesses: " << nguesses          << "\n"; 
                cerr << "queue size: "   << (int)queue.size() << "\n";
            }

            cout << guess_string; // output guess
            if (verbose){
            	cout << "\t" << probability(curr_guess); // output probability
            	cout << "\t" << curr_guess.rule->str; //output rule
            }
            cout << "\n";


            // exit when reach the limit of guesses
            if (nguesses == limit){
            	cerr << "Last guess: (" << guess_string << ", " << probability(curr_guess) << ")\n";
            	cerr << nguesses << " guesses generated\n";
            	return 0;
            }
        }  
        
        std::vector<std::string> tags = unpack(curr_guess.rule->str);
        // enqueue lower probability guesses from the same rule of curr_guess
        for (int i=curr_guess.pivot; i<tags.size(); i++ ){
            std::string tag = tags[i];
            
            std::vector<std::vector<Terminal>::iterator> new_terminals(curr_guess.terminals);
            ++new_terminals[i];

            if (new_terminals[i] != tag_dicts[tag].end()){
//                double new_p = probability((*curr_guess.rule).p, tags, new_terminals);
                double new_p = probability((*curr_guess.rule).p, new_terminals);

                // do not enqueue guesses with probability lower than threshold
                if (new_p < min_prob) continue;

                int new_pivot = i;
                
                Guess g;
                g.terminals = new_terminals;
                g.pivot = new_pivot;
                g.rule = curr_guess.rule;
                

                queue.push(g);
            }
        }
    }
    
    cerr << "Last guess: (" << guess_string << ", " << probability(curr_guess) << ")\n";
    cerr << nguesses << " guesses generated\n";

    return 0;
}

optparse::Values options(int argc, char *argv[]){    
    OptionParser parser = OptionParser().description("Generates guesses from a PCFG");

    parser.add_option("-m", "--mangle").help("enables mangling rules").action("store_true");
    parser.add_option("-n", "--limit").type("double").help("limits the number of guesses generated")
                                .set_default(std::numeric_limits<double>::infinity());
    parser.add_option("-l", "--length").help("minimum length of the guesses").type("int")
                                .set_default(0);
    parser.add_option("-p", "--prob").type("double").help("sets a minimum guess probability threshold").set_default(0);
    
    parser.add_option("-g", "--grammar").set_default("").help("location of the grammar");
    parser.add_option("-v", "--verbose").action("store_true");
    char const* const algorithms[] = { "next", "deadbeat"};
    parser.add_option("-a", "--algorithm").choices(&algorithms[0], &algorithms[2]).help("Either 'next' or 'deadbeat'");
    return parser.parse_args(argc, argv);
}

int main(int argc, char *argv[]) {
    optparse::Values opts = options(argc, argv);
    std::string grammar_path = opts["grammar"];
    if (grammar_path != ""){
        if (grammar_path.back() != '/'){
            grammar_path.append("/");
        }
    }
        
    const char* algo = (const char*) opts.get("algorithm");

    load_grammar(grammar_path);
//    double *bounds = prob_bounds();
//    cout << bounds[0] << '\t' << bounds[1] << '\n';

    if (strcmp(algo, "next") == 0)
    	return run_next((bool)opts.get("mangle"), (double) opts.get("limit"), (int)opts.get("length"),
    	    		(double)opts.get("prob"), (bool)opts.get("verbose"));
    else
    	return run_deadbeat((bool)opts.get("mangle"), (double) opts.get("limit"), (int)opts.get("length"),
    		(double)opts.get("prob"), (bool)opts.get("verbose"));

}

