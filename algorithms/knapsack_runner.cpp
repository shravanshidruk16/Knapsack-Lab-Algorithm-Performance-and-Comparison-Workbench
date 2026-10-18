#include "knapsack_algorithms.h"
#include <iostream>
#include <string>
#include <vector>
#include <sstream>
#include <iomanip>
#include <cctype>
#include <cmath>

namespace {

// Minimalistic robust JSON scanner & parser for knapsack input
class MiniJsonParser {
public:
    explicit MiniJsonParser(const std::string& input) : text(input), pos(0) {}

    bool parse(long long& capacity, int& trials, std::vector<knapsack::Item>& items, std::string& err) {
        skip_ws();
        if (pos >= text.size() || text[pos] != '{') {
            err = "Expected JSON object starting with '{'";
            return false;
        }
        pos++; // Skip '{'

        capacity = 0;
        trials = 1;
        items.clear();
        bool has_capacity = false;

        while (pos < text.size()) {
            skip_ws();
            if (pos < text.size() && text[pos] == '}') {
                pos++;
                break;
            }

            std::string key = parse_string();
            skip_ws();
            if (pos >= text.size() || text[pos] != ':') {
                err = "Expected ':' after key: " + key;
                return false;
            }
            pos++; // Skip ':'
            skip_ws();

            if (key == "capacity") {
                capacity = parse_integer();
                has_capacity = true;
            } else if (key == "trials") {
                trials = static_cast<int>(parse_integer());
                if (trials < 1) trials = 1;
            } else if (key == "items") {
                if (!parse_items_array(items, err)) {
                    return false;
                }
            } else {
                skip_value();
            }

            skip_ws();
            if (pos < text.size() && text[pos] == ',') {
                pos++;
            }
        }

        if (!has_capacity) {
            err = "Missing required 'capacity' field in input JSON.";
            return false;
        }
        return true;
    }

private:
    const std::string& text;
    size_t pos;

    void skip_ws() {
        while (pos < text.size() && (std::isspace(static_cast<unsigned char>(text[pos])) || text[pos] == '\r' || text[pos] == '\n')) {
            pos++;
        }
    }

    std::string parse_string() {
        skip_ws();
        if (pos >= text.size() || text[pos] != '"') {
            return "";
        }
        pos++; // Skip opening '"'
        std::string s;
        while (pos < text.size() && text[pos] != '"') {
            if (text[pos] == '\\' && pos + 1 < text.size()) {
                pos++;
                s += text[pos];
            } else {
                s += text[pos];
            }
            pos++;
        }
        if (pos < text.size() && text[pos] == '"') {
            pos++; // Skip closing '"'
        }
        return s;
    }

    long long parse_integer() {
        skip_ws();
        bool negative = false;
        if (pos < text.size() && text[pos] == '-') {
            negative = true;
            pos++;
        }
        long long val = 0;
        while (pos < text.size() && std::isdigit(static_cast<unsigned char>(text[pos]))) {
            val = val * 10 + (text[pos] - '0');
            pos++;
        }
        return negative ? -val : val;
    }

    void skip_value() {
        skip_ws();
        if (pos >= text.size()) return;
        char c = text[pos];
        if (c == '"') {
            parse_string();
        } else if (c == '{') {
            int depth = 1;
            pos++;
            while (pos < text.size() && depth > 0) {
                if (text[pos] == '{') depth++;
                else if (text[pos] == '}') depth--;
                else if (text[pos] == '"') parse_string();
                pos++;
            }
        } else if (c == '[') {
            int depth = 1;
            pos++;
            while (pos < text.size() && depth > 0) {
                if (text[pos] == '[') depth++;
                else if (text[pos] == ']') depth--;
                else if (text[pos] == '"') parse_string();
                pos++;
            }
        } else {
            while (pos < text.size() && text[pos] != ',' && text[pos] != '}' && text[pos] != ']') {
                pos++;
            }
        }
    }

    bool parse_items_array(std::vector<knapsack::Item>& items, std::string& err) {
        skip_ws();
        if (pos >= text.size() || text[pos] != '[') {
            err = "Expected '[' at start of items array";
            return false;
        }
        pos++; // Skip '['

        int orig_idx = 0;
        while (pos < text.size()) {
            skip_ws();
            if (pos < text.size() && text[pos] == ']') {
                pos++;
                break;
            }

            if (text[pos] == '{') {
                pos++; // Skip '{'
                int item_id = orig_idx + 1;
                std::string item_name = "Item " + std::to_string(orig_idx + 1);
                long long weight = 0;
                long long value = 0;

                while (pos < text.size()) {
                    skip_ws();
                    if (pos < text.size() && text[pos] == '}') {
                        pos++;
                        break;
                    }

                    std::string key = parse_string();
                    skip_ws();
                    if (pos < text.size() && text[pos] == ':') pos++;
                    skip_ws();

                    if (key == "id") {
                        item_id = static_cast<int>(parse_integer());
                    } else if (key == "name") {
                        item_name = parse_string();
                    } else if (key == "weight") {
                        weight = parse_integer();
                    } else if (key == "value") {
                        value = parse_integer();
                    } else {
                        skip_value();
                    }

                    skip_ws();
                    if (pos < text.size() && text[pos] == ',') {
                        pos++;
                    }
                }

                items.emplace_back(item_id, item_name, weight, value, orig_idx);
                orig_idx++;
            } else {
                skip_value();
            }

            skip_ws();
            if (pos < text.size() && text[pos] == ',') {
                pos++;
            }
        }
        return true;
    }
};

void escape_json(std::ostream& os, const std::string& s) {
    for (char c : s) {
        if (c == '"') os << "\\\"";
        else if (c == '\\') os << "\\\\";
        else if (c == '\b') os << "\\b";
        else if (c == '\f') os << "\\f";
        else if (c == '\n') os << "\\n";
        else if (c == '\r') os << "\\r";
        else if (c == '\t') os << "\\t";
        else os << c;
    }
}

void print_result_json(std::ostream& os, const knapsack::KnapsackResult& res) {
    os << "{\n";
    os << "    \"algorithm_name\": \""; escape_json(os, res.algorithm_name); os << "\",\n";
    os << "    \"success\": " << (res.success ? "true" : "false") << ",\n";
    if (!res.success) {
        os << "    \"error_message\": \""; escape_json(os, res.error_message); os << "\"\n";
        os << "  }";
        return;
    }
    os << "    \"optimal_value\": " << res.optimal_value << ",\n";
    os << "    \"total_weight\": " << res.total_weight << ",\n";
    os << "    \"selected_count\": " << res.selected_count << ",\n";
    os << "    \"selected_indices\": [";
    for (size_t i = 0; i < res.selected_indices.size(); ++i) {
        os << res.selected_indices[i];
        if (i + 1 < res.selected_indices.size()) os << ", ";
    }
    os << "],\n";
    os << "    \"execution_time_us\": " << std::fixed << std::setprecision(3) << res.execution_time_us << ",\n";
    os << "    \"execution_time_ms\": " << std::fixed << std::setprecision(6) << res.execution_time_ms << ",\n";
    os << "    \"trials_conducted\": " << res.trials_conducted << ",\n";
    os << "    \"peak_working_set_bytes\": " << res.peak_working_set_bytes << ",\n";
    os << "    \"algorithm_workspace_bytes\": " << res.algorithm_workspace_bytes << ",\n";
    os << "    \"memory_source\": \""; escape_json(os, res.memory_source); os << "\"";

    if (res.algorithm_name == "Dynamic Programming") {
        os << ",\n    \"dp_rows\": " << res.dp_rows << ",\n";
        os << "    \"dp_cols\": " << res.dp_cols << ",\n";
        os << "    \"dp_table_entries\": " << res.dp_table_entries << "\n";
    } else {
        os << ",\n    \"nodes_expanded\": " << res.nodes_expanded << ",\n";
        os << "    \"nodes_generated\": " << res.nodes_generated << ",\n";
        os << "    \"nodes_pruned\": " << res.nodes_pruned << ",\n";
        os << "    \"max_frontier_size\": " << res.max_frontier_size << "\n";
    }
    os << "  }";
}

} // namespace

int main(int argc, char* argv[]) {
    std::ios_base::sync_with_stdio(false);
    std::cin.tie(NULL);

    std::string mode = "both"; // "both", "dp", or "bb"

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--help" || arg == "-h") {
            std::cout << "Knapsack Lab C++17 Runner\n"
                      << "Usage:\n"
                      << "  knapsack_runner [--mode both|dp|bb] [--health]\n"
                      << "Reads JSON from standard input and outputs JSON to standard output.\n";
            return 0;
        } else if (arg == "--health") {
            std::cout << "{\"status\": \"ok\", \"compiler\": \"C++17\", \"engine\": \"Knapsack Lab Runner 1.0.0\"}\n";
            return 0;
        } else if (arg == "--mode" && i + 1 < argc) {
            mode = argv[++i];
        }
    }

    // Read full JSON string from stdin
    std::stringstream buffer;
    buffer << std::cin.rdbuf();
    std::string input_json = buffer.str();

    if (input_json.empty()) {
        std::cerr << "{\"success\": false, \"error\": \"Empty input received on stdin.\"}\n";
        return 1;
    }

    long long capacity = 0;
    int trials = 1;
    std::vector<knapsack::Item> items;
    std::string parse_err;

    MiniJsonParser parser(input_json);
    if (!parser.parse(capacity, trials, items, parse_err)) {
        std::cerr << "{\"success\": false, \"error\": \"JSON parse error: " << parse_err << "\"}\n";
        return 1;
    }

    knapsack::KnapsackResult dp_res;
    knapsack::KnapsackResult bb_res;

    if (mode == "both" || mode == "dp") {
        dp_res = knapsack::solve_dynamic_programming(items, capacity, trials);
    }
    if (mode == "both" || mode == "bb") {
        bb_res = knapsack::solve_branch_and_bound(items, capacity, trials);
    }

    std::cout << "{\n";
    std::cout << "  \"success\": true,\n";
    std::cout << "  \"capacity\": " << capacity << ",\n";
    std::cout << "  \"item_count\": " << items.size() << ",\n";

    if (mode == "both" || mode == "dp") {
        std::cout << "  \"dp\": ";
        print_result_json(std::cout, dp_res);
        if (mode == "both") std::cout << ",\n";
        else std::cout << "\n";
    }

    if (mode == "both" || mode == "bb") {
        std::cout << "  \"branch_and_bound\": ";
        print_result_json(std::cout, bb_res);
        if (mode == "both") std::cout << ",\n";
        else std::cout << "\n";
    }

    if (mode == "both") {
        bool agreement = (dp_res.success && bb_res.success && (dp_res.optimal_value == bb_res.optimal_value));
        std::string faster = "Identical";
        double diff_ms = std::abs(dp_res.execution_time_ms - bb_res.execution_time_ms);
        double speedup = 1.0;
        std::string speedup_summary = "Both algorithms had virtually identical measured runtimes.";

        if (dp_res.execution_time_us > 0.0 && bb_res.execution_time_us > 0.0) {
            if (bb_res.execution_time_us < dp_res.execution_time_us * 0.95) {
                faster = "Branch and Bound";
                speedup = dp_res.execution_time_us / bb_res.execution_time_us;
                std::stringstream ss;
                ss << "Branch and Bound was " << std::fixed << std::setprecision(2) << speedup << "x faster than DP.";
                speedup_summary = ss.str();
            } else if (dp_res.execution_time_us < bb_res.execution_time_us * 0.95) {
                faster = "Dynamic Programming";
                speedup = bb_res.execution_time_us / dp_res.execution_time_us;
                std::stringstream ss;
                ss << "Dynamic Programming was " << std::fixed << std::setprecision(2) << speedup << "x faster than B&B.";
                speedup_summary = ss.str();
            }
        }

        std::cout << "  \"comparison\": {\n";
        std::cout << "    \"optimal_values_match\": " << (agreement ? "true" : "false") << ",\n";
        std::cout << "    \"faster_algorithm\": \"" << faster << "\",\n";
        std::cout << "    \"runtime_difference_ms\": " << std::fixed << std::setprecision(6) << diff_ms << ",\n";
        std::cout << "    \"speedup\": " << std::fixed << std::setprecision(3) << speedup << ",\n";
        std::cout << "    \"speedup_summary\": \""; escape_json(std::cout, speedup_summary); std::cout << "\"\n";
        std::cout << "  }\n";
    }

    std::cout << "}\n";
    return 0;
}
