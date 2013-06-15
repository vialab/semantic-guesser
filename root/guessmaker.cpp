#include <iostream>
#include <fstream>
#include <vector>
#include <sstream>
#include <stdlib.h>
#include <unordered_map> 

using namespace std;

std::unordered_map<std::string, double> rules;

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

int main() {
    std::ifstream fs("grammar/rules.txt");
    std::string line;
    
    while (std::getline(fs, line)){
        std::vector<std::string> fields = split(line, '\t');
        std::string rule = fields[0];
        double p = atof(fields[1].c_str());
        rules[rule] = p;
    }

    cout << rules["(number)"];
}


